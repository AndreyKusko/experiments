import functools

import pytest
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework.exceptions import NotFound, ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_update, retrieve_response_instance
from projects.models.project import PROJECT_IS_ARCHIVED
from ma_saas.constants.system import DATETIME_FORMAT
from ma_saas.constants.company import (
    CUR,
    CUS,
    NOT_ACCEPT_CUS,
    NOT_OWNER_ROLES,
    NOT_OWNER_AND_NOT_WORKER_ROLES,
)
from ma_saas.constants.project import ProjectStatus
from clients.policies.interface import Policies
from tasks.models.schedule_time_slot import ScheduleTimeSlot

User = get_user_model()

__get_response = functools.partial(request_response_update, path="/api/v1/schedule-time-slots/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("schedule_time_slot_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, {}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__without_policies__success(
    api_client, mock_policy_true, r_cu, get_schedule_time_slot_fi
):
    mock_policy_true(r_cu.company)
    instance = get_schedule_time_slot_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, {}, r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__fail(
    api_client, mock_policy_true, get_cu_fi, get_schedule_time_slot_fi, status
):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status)
    mock_policy_true(r_cu.company)
    instance = get_schedule_time_slot_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_AND_NOT_WORKER_ROLES)
def test__not_owner_and_not_worker__without_policies__fail(
    api_client, mock_policies_false, get_cu_fi, get_schedule_time_slot_fi, role
):
    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)
    instance = get_schedule_time_slot_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}, f"response.data = {response.data}"


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__related_worker__without_policies__fail(
    api_client, mock_policies_false, pt_worker, get_schedule_time_slot_fi, get_reservation_fi
):
    """вообще должен срабатывать тест сверху, для этого будет необходимо поменять фильтрацию кверисета"""
    r_cu = pt_worker.company_user
    instance = get_schedule_time_slot_fi(project_territory=pt_worker.project_territory)
    get_reservation_fi(schedule_time_slot=instance, project_territory_worker=pt_worker)
    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PermissionDenied.default_detail}, f"response.data = {response.data}"


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__with_policies__success(
    api_client, mock_policy_true, get_cu_fi, get_schedule_time_slot_fi, role
):
    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)

    mock_policy_true(r_cu.company)

    instance = get_schedule_time_slot_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, {}, r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_contractor_owner__fail(
    api_client, mock_policies_false, get_cu_fi, get_schedule_time_slot_fi, status
):
    r_cu = get_cu_fi(status=status.value, role=CUR.OWNER)
    instance = get_schedule_time_slot_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("status", [s for s in ProjectStatus if s != ProjectStatus.ARCHIVED])
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__update_if_project_status__not__archived__success(
    api_client, mock_policy_true, r_cu, get_project_fi, get_schedule_time_slot_fi, status
):
    mock_policy_true(r_cu.company)
    project = get_project_fi(company=r_cu.company, status=status.value)
    instance = get_schedule_time_slot_fi(project=project)
    data = {"status": status, "title": get_random_string()}
    response = __get_response(api_client, instance.id, data, r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__update_if_project_status_archive__fail(
    api_client, mock_policy_true, r_cu, get_project_fi, get_schedule_time_slot_fi
):
    mock_policy_true(r_cu.company)
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.ARCHIVED.value)
    instance = get_schedule_time_slot_fi(project=project)
    data = {"reward": instance.reward + 1}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    assert response.data == {"non_field_errors": [PROJECT_IS_ARCHIVED]}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(
    api_client, mock_policy_true, r_cu, get_schedule_time_slot_fi, new_schedule_time_slot_data
):
    mock_policy_true(r_cu.company)

    instance = get_schedule_time_slot_fi(company=r_cu.company)
    data = new_schedule_time_slot_data()

    response = __get_response(api_client, instance.id, data=data, user=r_cu.user)

    updated_instance = ScheduleTimeSlot.objects.get(id=instance.id)
    response_instance = response.data
    assert response_instance.pop("id") == updated_instance.id

    if response_project_scheme := retrieve_response_instance(response_instance, "project_scheme", dict):
        assert (
            response_project_scheme.pop("id")
            == updated_instance.project_scheme.id
            == instance.project_scheme.id
        )
        assert (
            response_project_scheme.pop("color")
            == updated_instance.project_scheme.color
            == instance.project_scheme.color
        )
        assert (
            response_project_scheme.pop("title")
            == updated_instance.project_scheme.title
            == instance.project_scheme.title
        )
    assert not response_project_scheme

    if response_geo_point := retrieve_response_instance(response_instance, "geo_point", dict):
        assert response_geo_point.pop("id") == updated_instance.geo_point.id == instance.geo_point.id
    assert not response_geo_point

    assert response_instance.pop("reward") == updated_instance.reward
    assert response_instance.pop("active_since_date") == str(updated_instance.active_since_date)
    assert response_instance.pop("active_since_time") == str(updated_instance.active_since_time)
    assert response_instance.pop("active_since_date_local") == str(updated_instance.active_since_date_local)
    assert response_instance.pop("active_since_time_local") == str(updated_instance.active_since_time_local)
    assert response_instance.pop("active_till_date") == str(updated_instance.active_till_date)
    assert response_instance.pop("active_till_time") == str(updated_instance.active_till_time)
    assert response_instance.pop("active_till_date_local") == str(updated_instance.active_till_date_local)
    assert response_instance.pop("active_till_time_local") == str(updated_instance.active_till_time_local)
    assert response_instance.pop("max_reports_qty") == updated_instance.max_reports_qty
    assert response_instance.pop("created_at") == updated_instance.created_at.strftime(DATETIME_FORMAT)
    assert response_instance.pop("updated_at") == updated_instance.updated_at.strftime(DATETIME_FORMAT)
    assert not response_instance
