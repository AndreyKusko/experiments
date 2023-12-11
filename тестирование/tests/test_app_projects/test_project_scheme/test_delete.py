import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated, PermissionDenied

from tests.utils import request_response_delete
from ma_saas.constants.company import (
    CUR,
    CUS,
    NOT_ACCEPT_CUS,
    NOT_OWNER_ROLES,
    NOT_OWNER_AND_NOT_WORKER_ROLES,
)
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_MUST_BE_ACCEPT
from projects.models.project_scheme import ProjectScheme

User = get_user_model()

__get_response = functools.partial(request_response_delete, path="/api/v1/project-schemes/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("project_scheme_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, get_project_scheme_fi):
    instance = get_project_scheme_fi(company=r_cu.company)
    assert __get_response(api_client, instance.id, r_cu.user)
    deleted_instance = ProjectScheme.objects.get(id=instance.id)
    assert deleted_instance.is_deleted


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_worker_fi")])
def test__project_territory_worker__cu_status_accepted__fail(
    api_client, mock_policies_false, r_cu, get_project_scheme_fi, get_pt_worker_fi
):
    instance = get_project_scheme_fi(company=r_cu.company)
    get_pt_worker_fi(company_user=r_cu, project=instance.project)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PermissionDenied.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_worker_fi")])
def test__not_project_territory_accepted_worker__fail(
    api_client, mock_policies_false, r_cu, get_project_scheme_fi, get_pt_worker_fi
):
    instance = get_project_scheme_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__fail(api_client, mock_policies_false, get_cu_fi, get_project_scheme_fi, status):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    instance = get_project_scheme_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__with_policies__fail(
    api_client, monkeypatch, get_cu_fi, get_project_scheme_fi, status
):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_project_scheme_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("role", NOT_OWNER_AND_NOT_WORKER_ROLES)
def test__not_owner__without_policies__fail(
    api_client, mock_policies_false, get_cu_fi, get_project_scheme_fi, role
):
    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)
    instance = get_project_scheme_fi(company=r_cu.company)

    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__with_policies__success(api_client, monkeypatch, get_cu_fi, get_project_scheme_fi, role):
    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_project_scheme_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user)
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__user_from_different_company__fail(api_client, monkeypatch, get_cu_fi, get_project_scheme_fi, r_cu):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_project_scheme_fi()
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)

    assert response.data == {"detail": NotFound.default_detail}, f"response.data = {response.data}"
