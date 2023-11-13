import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated

from tests.utils import request_response_get
from ma_saas.constants.system import Callable
from ma_saas.constants.company import CUS, NOT_OWNER_ROLES
from tasks.models.schedule_time_slot import ScheduleTimeSlot

User = get_user_model()

__get_response = functools.partial(request_response_get, path="/api/v1/schedule-time-slots/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("schedule_time_slot_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__owner__with_policy__success(
    api_client, mock_policy_true, r_cu, get_schedule_time_slot_fi: Callable
):
    mock_policy_true(r_cu.company)
    instance = get_schedule_time_slot_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user)
    assert instance == ScheduleTimeSlot.objects.get(id=response.data["id"])


@pytest.mark.xfail
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__not_accepted_owner__with_policy__fail(
    api_client, mock_policy_true, r_cu, get_schedule_time_slot_fi: Callable
):
    mock_policy_true(r_cu.company)
    instance = get_schedule_time_slot_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__related_manager__with_policy__success(
    api_client, mock_policy_true, r_cu, get_schedule_time_slot_fi
):
    mock_policy_true(r_cu.company)

    instance = get_schedule_time_slot_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user)
    assert instance == ScheduleTimeSlot.objects.get(id=response.data["id"])


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__related_manager__without_policy__fail(
    api_client, mock_policies_false, r_cu, get_schedule_time_slot_fi
):
    instance = get_schedule_time_slot_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__any_accepted_cu__not_owner__with_policy__success(
    api_client, mock_policy_true, get_cu_fi, get_schedule_time_slot_fi, role
):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    mock_policy_true(r_cu.company)
    instance = get_schedule_time_slot_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user)
    assert instance == ScheduleTimeSlot.objects.get(id=response.data["id"])


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__any_accepted_cu__not_owner__without_policy__fail(
    api_client, mock_policies_false, get_cu_fi, get_schedule_time_slot_fi, role
):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    instance = get_schedule_time_slot_fi(company=r_cu.company)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__related_pt_worker__without_policy__success(
    api_client, mock_policies_false, pt_worker, get_schedule_time_slot_fi, get_reservation_fi
):
    r_cu = pt_worker.company_user
    instance = get_schedule_time_slot_fi(project_territory=pt_worker.project_territory)
    get_reservation_fi(schedule_time_slot=instance, project_territory_worker=pt_worker)
    response = __get_response(api_client, instance.id, r_cu.user)
    assert instance == ScheduleTimeSlot.objects.get(id=response.data["id"])


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__different_company_owner__with_policy__fail(
    api_client, mock_policy_true, r_cu, get_schedule_time_slot_fi
):
    instance: ScheduleTimeSlot = get_schedule_time_slot_fi()
    company = instance.project_scheme.project.company
    mock_policy_true(company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(api_client, mock_policy_true, r_cu, get_schedule_time_slot_fi):
    mock_policy_true(r_cu.company)
    instance = get_schedule_time_slot_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user)
    response_instance = response.data
    assert response_instance.pop("id") == instance.id
    assert response_instance.pop("geo_point") == {"id": instance.geo_point.id}
    assert response_instance.pop("project_scheme") == {
        "id": instance.project_scheme.id,
        "title": instance.project_scheme.title,
        "color": instance.project_scheme.color,
    }
    assert response_instance.pop("max_reports_qty") == instance.max_reports_qty
    assert response_instance.pop("reward") == instance.reward
    assert response_instance.pop("active_since_date")
    assert response_instance.pop("active_since_time")
    assert response_instance.pop("active_since_date_local")
    assert response_instance.pop("active_since_time_local")
    assert response_instance.pop("active_till_date")
    assert response_instance.pop("active_till_time")
    assert response_instance.pop("active_till_date_local")
    assert response_instance.pop("active_till_time_local")
    assert response_instance.pop("updated_at")
    assert response_instance.pop("created_at")
    assert not response_instance
