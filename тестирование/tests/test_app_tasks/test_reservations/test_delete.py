import functools

import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated

from tests.utils import request_response_delete
from ma_saas.constants.system import Callable
from tasks.models.reservation import Reservation
from ma_saas.constants.company import CUR, ROLES, CompanyUserStatus
from companies.models.company_user import CompanyUser

User = get_user_model()

__get_response = functools.partial(request_response_delete, path="/api/v1/reservations/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("reservation_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codess={NotAuthenticated.status_code})
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, get_reservation_fi):
    instance = get_reservation_fi(company=r_cu.company)
    assert __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    assert not Reservation.objects.existing().filter(id=instance.id)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__related_manager__success(api_client, r_cu, get_reservation_fi: Callable):
    instance = get_reservation_fi(company=r_cu.company)
    assert __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    assert not Reservation.objects.existing().filter(id=instance.id)


def test__related_pt_worker__fail(api_client, get_pt_worker_fi, get_reservation_fi: Callable):
    r_pt_worker = get_pt_worker_fi()
    r_cu, pt = r_pt_worker.company_user, r_pt_worker.project_territory
    instance = get_reservation_fi(project_territory=pt, project_territory_worker=r_pt_worker)
    response = __get_response(api_client, instance.id, user=r_cu.user, status_codes=NotAuthenticated)
    assert response.data == {"detail": 'Method "DELETE" not allowed.'}


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", CompanyUserStatus.values)
def test__different_company_user__empty_response(
    api_client, get_cu_fi, get_reservation_fi: Callable, role, status
):
    r_cu = get_cu_fi(status=status, role=role)
    instance = get_reservation_fi()
    response = __get_response(api_client, user=r_cu.user, instance_id=instance.id, status_codess=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", CompanyUserStatus.values)
def test__contractor_not_related_user__fail(
    api_client, get_cu_fi, get_reservation_fi: Callable, role, status
):
    if status == CompanyUserStatus.ACCEPT.value and role == CUR.OWNER:
        return
    r_cu = get_cu_fi(status=status, role=role)
    instance = get_reservation_fi(company=r_cu.company)
    response = __get_response(api_client, user=r_cu.user, instance_id=instance.id, status_codess=NotFound)
    assert response.data == {"detail": NotFound.default_detail}
