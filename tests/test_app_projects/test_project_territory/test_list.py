import functools

import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated

from tests.utils import request_response_list
from ma_saas.constants.system import Callable
from ma_saas.constants.company import CUS, ROLES, NOT_ACCEPT_CUS, NOT_ACCEPT_CUS_VALUES
from ma_saas.constants.project import ProjectStatus
from companies.models.company_user import CompanyUser

User = get_user_model()

__get_response = functools.partial(request_response_list, path="/api/v1/project-territory/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, status_codes=NotAuthenticated)
    assert response.data["detail"] == {"detail": NotAuthenticated.default_detail}


def test__user_without_companies_got_nothing(api_client, user_fi: User):
    response = __get_response(api_client, user=user_fi)
    assert not response.data


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("qty", (1, 3))
def test__related_accepted_user_is__success(
    api_client, get_project_territory_fi: Callable, get_cu_fi, role, qty: int
):
    company_user = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    [get_project_territory_fi(company=company_user.company) for _ in range(qty)]
    response = __get_response(api_client, user=company_user.user)
    assert len(response.data) == qty
    assert response.data[0]["territory_title"]
    assert response.data[0]["project_title"]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("project_status", ProjectStatus.values)
def test__with_any_project_status__success(
    api_client,
    get_project_territory_fi: Callable,
    r_cu,
    get_project_fi,
    project_status,
):
    project = get_project_fi(company=r_cu.company, status=project_status)
    instance = get_project_territory_fi(company=r_cu.company, project=project)
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == 1
    assert response.data[0]["id"] == instance.id


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("company_status", NOT_ACCEPT_CUS)
@pytest.mark.parametrize("qty", (1, 3))
def test__not_accepted_users__empty_response(
    api_client,
    get_project_territory_fi: Callable,
    get_cu_fi,
    role,
    company_status,
    qty,
):
    company_user = get_cu_fi(role=role, status=company_status.value)
    [get_project_territory_fi(company=company_user.company) for _ in range(qty)]
    response = __get_response(api_client, user=company_user.user)
    assert not response.data
