import functools

import pytest
from django.forms import model_to_dict
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated

from tests.utils import request_response_get
from ma_saas.constants.system import Callable
from ma_saas.constants.company import ROLES
from ma_saas.constants.project import ProjectStatus
from companies.models.company_user import CompanyUser

User = get_user_model()


__get_response = functools.partial(request_response_get, path="/api/v1/project-territory/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("project_territory_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("role", ROLES)
def test__accepted_related_users__success(
    api_client,
    get_cu_fi,
    get_project_territory_fi: Callable,
    new_project_territory_data: Callable,
    role,
):
    company_user = get_cu_fi(role=role)
    instance = get_project_territory_fi(company=company_user.company)

    response = __get_response(api_client, instance_id=instance.id, user=company_user.user)
    instance_dict = model_to_dict(instance)
    assert response.data["territory_title"]
    assert response.data["project_title"]
    assert response.data.pop("territory_title") == instance.territory.title
    assert response.data.pop("project_title") == instance.project.title
    assert all(instance_dict[key] == value for key, value in response.data.items())


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("qty", (1, 3))
def test__owner_is__success(api_client, get_project_territory_fi: Callable, r_cu, qty: int):
    instance = get_project_territory_fi(company=r_cu.company)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    instance_dict = model_to_dict(instance)
    response.data.pop("territory_title")
    response.data.pop("project_title")
    assert all(instance_dict[key] == value for key, value in response.data.items())


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
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    assert response.data
