import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated

from tests.utils import request_response_list, retrieve_response_instance
from ma_saas.constants.company import CUS, NOT_OWNER_ROLES
from clients.policies.interface import Policies

User = get_user_model()

__get_response = functools.partial(request_response_list, path="/api/v1/schedule-time-slots/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("qty", (3,))
def test__owner__with_policy__success(api_client, mock_policy_true, get_schedule_time_slot_fi, r_cu, qty):
    mock_policy_true(r_cu.company)
    [get_schedule_time_slot_fi(company=r_cu.company) for _ in range(qty)]
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == qty


@pytest.mark.xfail
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__not_accepted_owner__with_policy__fail(
    api_client, mock_policy_true, get_schedule_time_slot_fi, r_cu
):
    mock_policy_true(r_cu.company)

    get_schedule_time_slot_fi(company=r_cu.company)
    response = __get_response(api_client, user=r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__related_manager__with_policy__success(
    api_client, mock_policy_true, r_cu, get_schedule_time_slot_fi, get_project_territory_fi
):
    mock_policy_true(r_cu.company)

    pt = get_project_territory_fi(company=r_cu.company)
    instance = get_schedule_time_slot_fi(project_territory=pt)
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == 1
    assert response.data[0]["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__related_manager__without_policy__fail(
    api_client, mock_policies_false, r_cu, get_schedule_time_slot_fi
):
    get_schedule_time_slot_fi(company=r_cu.company)
    response = __get_response(api_client, user=r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__related_pt_worker__without_policy__success(
    api_client, mock_policies_false, pt_worker, get_schedule_time_slot_fi, get_reservation_fi
):
    r_cu = pt_worker.company_user
    instance = get_schedule_time_slot_fi(project_territory=pt_worker.project_territory)
    get_reservation_fi(schedule_time_slot=instance, project_territory_worker=pt_worker)
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == 1
    assert response.data[0]["id"] == instance.id


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__with_policy__success(
    api_client, mock_policy_true, get_cu_fi, get_schedule_time_slot_fi, role
):
    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)
    mock_policy_true(r_cu.company)
    instance = get_schedule_time_slot_fi(company=r_cu.company)
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == 1
    assert response.data[0]["id"] == instance.id


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__without_policy__fail(
    api_client, mock_policies_false, get_cu_fi, get_schedule_time_slot_fi, role
):
    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)
    get_schedule_time_slot_fi(company=r_cu.company)
    response = __get_response(api_client, user=r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__different_company_user__empty_response(
    api_client, mock_policy_true, r_cu, get_schedule_time_slot_fi
):
    instance = get_schedule_time_slot_fi()
    company = instance.project_scheme.project.company

    mock_policy_true(company)

    response = __get_response(api_client, user=r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("qty", (3,))
def test__response_data(api_client, mock_policies_false, get_schedule_time_slot_fi, r_cu, qty: int):
    instances = [get_schedule_time_slot_fi(company=r_cu.company) for _ in range(qty)]
    instances.reverse()
    response = __get_response(api_client, user=r_cu.user)
    for index, response_instance in enumerate(response.data):
        assert response_instance.pop("id") == instances[index].id

        if response_scheme := retrieve_response_instance(response_instance, "project_scheme", dict):
            assert response_scheme.pop("id") == instances[index].project_scheme.id
            assert response_scheme.pop("color") == instances[index].project_scheme.color
            assert response_scheme.pop("title") == instances[index].project_scheme.title
        assert not response_scheme

        assert response_instance.pop("geo_point") == {"id": instances[index].geo_point.id}
        assert response_instance.pop("reward") == instances[index].reward
        assert response_instance.pop("max_reports_qty") == instances[index].max_reports_qty
        assert response_instance.pop("active_since")
        assert response_instance.pop("active_since_local")
        assert response_instance.pop("active_till")
        assert response_instance.pop("active_till_local")
        assert response_instance.pop("created_at")
        assert response_instance.pop("updated_at")
        assert not response_instance
