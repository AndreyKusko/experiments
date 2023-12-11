import functools

import pytest
from rest_framework.exceptions import NotFound, NotAuthenticated, PermissionDenied

from tests.utils import request_response_delete
from tests.constants import ROLES_WITH_DIFFERENT_LOGIC
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from ma_saas.constants.company import NOT_ACCEPT_CUS
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_MUST_BE_ACCEPT
from projects.models.project_variable import ProjectVariable

__get_response = functools.partial(request_response_delete, path="/api/v1/project-variables/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("project_variable_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, get_project_variable_fi):
    instance = get_project_variable_fi(company=r_cu.company)
    assert ProjectVariable.objects.filter(project__company=r_cu.company).exists()
    assert __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    assert not ProjectVariable.objects.filter(project__company=r_cu.company).existing().exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__related__manager__with_policy__success(api_client, monkeypatch, r_cu, get_project_variable_fi):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    instance = get_project_variable_fi(company=r_cu.company)
    assert ProjectVariable.objects.filter(project__company=r_cu.company).exists()
    assert __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    assert not ProjectVariable.objects.filter(project__company=r_cu.company).existing().exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__related__manager__without_policy__fail(
    api_client, mock_policies_false, r_cu, get_project_variable_fi, get_project_fi
):
    project = get_project_fi(company=r_cu.company)
    instance = get_project_variable_fi(project=project)
    assert ProjectVariable.objects.filter(project=project).exists()
    assert __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert ProjectVariable.objects.filter(project=project).existing().exists()


@pytest.mark.parametrize("role", ROLES_WITH_DIFFERENT_LOGIC)
@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accept_user__fail(api_client, monkeypatch, get_cu_fi, get_project_variable_fi, role, status):
    r_cu = get_cu_fi(status=status.value, role=role)
    company = r_cu.company

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [company.id])

    instance = get_project_variable_fi(company=company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("role", ROLES_WITH_DIFFERENT_LOGIC)
@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__different_company_user__fail(
    api_client, monkeypatch, get_cu_fi, get_project_variable_fi, role, status
):
    r_cu = get_cu_fi(status=status.value, role=role)
    instance = get_project_variable_fi()
    company = instance.project.company

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [company.id])

    response = __get_response(api_client, instance.id, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}
