import functools

import pytest
from django.forms import model_to_dict
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated

from tests.utils import request_response_get
from ma_saas.constants.system import Callable
from ma_saas.constants.company import CUR, CUS, ROLES, NOT_OWNER_ROLES, NOT_ACCEPT_CUS_VALUES
from companies.models.company_user import CompanyUser

User = get_user_model()


__get_response = functools.partial(request_response_get, path="/api/v1/contractor-project-territory-workers/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(api_client, r_cu: CompanyUser, get_pt_worker_fi):
    instance = get_pt_worker_fi(company=r_cu.company)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    assert len(response.data["company_user"]) == 11
    assert response.data.pop("company_user")["id"] == instance.company_user.id
    instance_dict = model_to_dict(instance)
    assert all(instance_dict[key] == value for key, value in response.data.items())


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, get_pt_worker_fi):
    instance = get_pt_worker_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, user=r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__related__manager__success(api_client, r_cu, get_pt_worker_fi, get_project_territory_fi):
    pt = get_project_territory_fi(company=r_cu.company)
    instance = get_pt_worker_fi(project_territory=pt, company=r_cu.company)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", CUS)
def test__different_company_user__fail(api_client, get_cu_fi, get_pt_worker_fi, role, status):
    r_cu = get_cu_fi(status=status.value, role=role)
    instance = get_pt_worker_fi()
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS_VALUES)
def test__not_accepted_contractor_owner__fail(api_client, get_cu_fi, get_pt_worker_fi, status):
    r_cu = get_cu_fi(status=status, role=CUR.OWNER)
    instance = get_pt_worker_fi(company=r_cu.company)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
@pytest.mark.parametrize("status", CUS)
def test__user_without_pt__fail(
    api_client,
    get_cu_fi,
    get_pt_worker_fi,
    role,
    status,
):
    r_cu = get_cu_fi(status=status.value, role=role)
    instance = get_pt_worker_fi(company=r_cu.company)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail
