import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated, PermissionDenied

from tests.utils import request_response_delete
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from ma_saas.constants.company import CUR, CUS, NOT_OWNER_ROLES, NOT_ACCEPT_CUS_VALUES
from clients.policies.interface import Policies
from projects.models.project_scheme_partnership import ProjectSchemePartnership

User = get_user_model()

__get_response = functools.partial(request_response_delete, path="/api/v1/project-scheme-partnership/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("project_scheme_partnership_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("project_scheme_partnership_fi")])
def test__not_client_accepted_owner__success(
    api_client, mock_policies_false, get_cu_fi, instance: ProjectSchemePartnership
):
    inviting_company = instance.project_partnership.company_partnership.inviting_company
    r_cu = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value, company=inviting_company)
    assert __get_response(api_client, instance.id, r_cu.user)
    deleted_instance = ProjectSchemePartnership.objects.get(id=instance.id)
    assert deleted_instance.is_deleted


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("project_scheme_partnership_fi")])
@pytest.mark.parametrize("status", NOT_ACCEPT_CUS_VALUES)
def test__not_client_not_accepted_owner__fail(
    api_client, mock_policies_false, get_cu_fi, instance: ProjectSchemePartnership, status
):
    inviting_company = instance.project_partnership.company_partnership.inviting_company
    r_cu = get_cu_fi(role=CUR.OWNER, status=status, company=inviting_company)
    assert __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    deleted_instance = ProjectSchemePartnership.objects.get(id=instance.id)
    assert not deleted_instance.is_deleted


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("project_scheme_partnership_fi")])
def test__client_owner__fail(api_client, mock_policies_false, get_cu_fi, instance: ProjectSchemePartnership):
    invited_company = instance.project_partnership.company_partnership.invited_company
    r_cu = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value, company=invited_company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}
    deleted_instance = ProjectSchemePartnership.objects.get(id=instance.id)
    assert not deleted_instance.is_deleted


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("project_scheme_partnership_fi")])
@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_client_cu__with_policy__success(
    api_client, monkeypatch, role, get_cu_fi, instance: ProjectSchemePartnership
):
    inviting_company = instance.project_partnership.company_partnership.inviting_company
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value, company=inviting_company)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    assert __get_response(api_client, instance.id, r_cu.user)
    deleted_instance = ProjectSchemePartnership.objects.get(id=instance.id)
    assert deleted_instance.is_deleted


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("project_scheme_partnership_fi")])
@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_client_cu__without_policy__fail(
    api_client, monkeypatch, role, get_cu_fi, instance: ProjectSchemePartnership
):
    inviting_company = instance.project_partnership.company_partnership.inviting_company
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value, company=inviting_company)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])

    assert __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    deleted_instance = ProjectSchemePartnership.objects.get(id=instance.id)
    assert not deleted_instance.is_deleted
