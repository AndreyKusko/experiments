import functools

import pytest
import requests
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from tests.utils import request_response_create
from accounts.models import USER_IS_BLOCKED, USER_IS_DELETED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from tests.mocked_instances import MockResponse
from companies.models.company import COMPANY_IS_DELETED, NOT_TA_COMPANY_REASON
from ma_saas.constants.company import NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_REASON, NOT_TA_RCU_MUST_BE_ACCEPT, CompanyUser
from projects.models.project_variable import ProjectVariable

User = get_user_model()


__get_response = functools.partial(request_response_create, path="/api/v1/project-variables/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, {}, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(api_client, monkeypatch, r_cu, new_project_variable_data):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)

    data = new_project_variable_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user)
    response_instance = response.data

    created_instance_id = response_instance.pop("id")
    assert created_instance_id
    created_instance = ProjectVariable.objects.get(id=created_instance_id)

    response_project = response_instance.pop("project")
    assert response_project == {"id": created_instance.project.id}

    assert response_instance.pop("title") == created_instance.title == data["title"]
    assert response_instance.pop("key") == created_instance.key == data["key"]
    assert response_instance.pop("kind") == created_instance.kind == data["kind"]
    assert not response_instance


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, new_project_variable_data):
    data = new_project_variable_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user)
    assert ProjectVariable.objects.filter(id=response.data["id"]).exists()
    assert response.data.get("id")


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__fail(
    api_client, monkeypatch, get_cu_owner_fi, new_project_variable_data, status
):
    r_cu = get_cu_owner_fi(status=status.value)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    data = new_project_variable_data(company=r_cu.company)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__without_policy__fail(
    api_client, mock_policies_false, get_cu_fi, new_project_variable_data, role
):
    r_cu = get_cu_fi(role=role)
    data = new_project_variable_data(company=r_cu.company)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PermissionDenied.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__with_policy__success(
    api_client, monkeypatch, get_cu_fi, new_project_variable_data, role
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu = get_cu_fi(role=role)
    data = new_project_variable_data(company=r_cu.company)
    response = __get_response(api_client, data, r_cu.user)
    assert response.data["id"]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("is_user", "field", "err_text"),
    (
        (True, "is_blocked", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_BLOCKED)),
        (True, "is_deleted", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_DELETED)),
        (False, "is_deleted", REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY),
    ),
)
@pytest.mark.parametrize("has_object_policy", [True, False])
def test__not_ta__cu__fail(
    api_client, monkeypatch, r_cu, new_project_variable_data, has_object_policy, is_user, field, err_text
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    data = new_project_variable_data(company=r_cu.company)
    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()
    else:
        setattr(r_cu, field, True)
        r_cu.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": err_text}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_company__fail(api_client, monkeypatch, r_cu, new_project_variable_data):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    data = new_project_variable_data(company=r_cu.company)
    r_cu.company.is_deleted = True
    r_cu.company.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": NOT_TA_RCU_REASON.format(reason=NOT_TA_COMPANY_REASON.format(reason=COMPANY_IS_DELETED))
    }
