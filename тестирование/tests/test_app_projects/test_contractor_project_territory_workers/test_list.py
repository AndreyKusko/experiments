import functools

import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated

from tests.utils import request_response_list
from ma_saas.constants.system import Callable
from ma_saas.constants.company import CUR, CUS, ROLES
from companies.models.company_user import CompanyUser

User = get_user_model()

__get_response = functools.partial(
    request_response_list, path="/api/v1/contractor-project-territory-workers/"
)


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("qty", (1, 3))
def test__accepted_owner__success(api_client, mock_policies_false, get_pt_worker_fi, r_cu, qty):
    [get_pt_worker_fi(company=r_cu.company) for _ in range(qty)]
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == qty


@pytest.mark.parametrize("qty", (1, 3))
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__related__manager__success(
    api_client,
    r_cu,
    get_pt_worker_fi,
    get_cu_fi,
    get_project_territory_fi,
    qty,
):
    pt = get_project_territory_fi(company=r_cu.company)
    [get_pt_worker_fi(company=r_cu.company, project_territory=pt) for _ in range(qty)]
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == qty


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", CUS)
def test__not_related_user__empty_response(
    api_client,
    get_cu_fi,
    get_pt_worker_fi,
    role,
    status,
):
    if status == CUS.ACCEPT.value and role == CUR.OWNER:
        return
    r_cu = get_cu_fi(status=status.value, role=role)
    get_pt_worker_fi(company=r_cu.company)
    response = __get_response(api_client, user=r_cu.user)
    assert not response.data


def test__different_company_user__empty_response(api_client, get_cu_fi, get_pt_worker_fi):
    r_cu = get_cu_fi(role=CUR.OWNER)
    get_pt_worker_fi()
    response = __get_response(api_client, user=r_cu.user, status_codes=status_code.HTTP_200_OK)
    assert not response.data
