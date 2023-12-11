import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated

from tests.utils import request_response_get
from ma_saas.constants.system import Callable
from tasks.models.reservation import Reservation
from ma_saas.constants.company import CUR, ROLES, NOT_ACCEPT_CUS, NOT_OWNER_ROLES, CompanyUserStatus
from companies.models.company_user import CompanyUser
from tests.test_app_tasks.test_reservations.utils import compare_response_and_instance

User = get_user_model()

__get_response = functools.partial(request_response_get, path="/api/v1/reservations/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("reservation_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, get_reservation_fi):
    instance = get_reservation_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user)
    response_instance = Reservation.objects.get(id=response.data["id"])
    assert instance == response_instance
    assert compare_response_and_instance(data=response.data, instance=response_instance)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__related_manager__success(api_client, r_cu, get_reservation_fi):
    instance = get_reservation_fi(company=r_cu.company)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    response_instance = Reservation.objects.get(id=response.data["id"])
    assert instance == response_instance
    assert compare_response_and_instance(data=response.data, instance=response_instance)


def test__related_pt_worker__success(api_client, get_pt_worker_fi, get_reservation_fi):
    r_pt_worker = get_pt_worker_fi()
    instance = get_reservation_fi(project_territory_worker=r_pt_worker)

    response = __get_response(api_client, instance.id, r_pt_worker.company_user.user)
    response_instance = Reservation.objects.get(id=response.data["id"])
    assert instance == response_instance
    assert compare_response_and_instance(data=response.data, instance=response_instance)


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", CompanyUserStatus.values)
def test__different_company_user__empty_response(api_client, get_cu_fi, get_reservation_fi, role, status):
    r_cu = get_cu_fi(status=status, role=role)
    instance = get_reservation_fi()
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
@pytest.mark.parametrize("status", CompanyUserStatus)
def test__not_related_user__fail(api_client, get_cu_fi, get_reservation_fi, role, status):
    r_cu = get_cu_fi(status=status.value, role=role)
    instance = get_reservation_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__contractor_not_accepted_owner_cu__fail(api_client, get_cu_fi, get_reservation_fi, status):
    r_cu = get_cu_fi(status=status, role=CUR.OWNER)
    instance = get_reservation_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail
