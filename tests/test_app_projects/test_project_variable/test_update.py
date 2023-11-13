import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated, PermissionDenied

from tests.utils import request_response_update
from accounts.models import USER_IS_BLOCKED, USER_IS_DELETED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.constants.company import CUR, CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from ma_saas.constants.project import (
    ACTIVE_OR_SETUP_PROJECT_STATUS,
    NOT_ACTIVE_OR_SETUP_PROJECT_STATUS,
    ProjectStatus,
)
from clients.policies.interface import Policies
from companies.models.company_user import CompanyUser
from projects.models.project_variable import ProjectVariable

User = get_user_model()


__get_response = functools.partial(request_response_update, path="/api/v1/project-variables/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("project_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, {}, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__without_policy__success(
    api_client, mock_policies_false, r_cu, get_project_variable_fi
):

    instance = get_project_variable_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, {}, r_cu.user)
    assert response.data.get("id")


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted__company_owner__without_policy__fail(
    api_client, mock_policies_false, get_cu_fi, get_project_variable_fi, status
):
    r_cu = get_cu_fi(status=status, role=CUR.OWNER)
    instance = get_project_variable_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__accepted__not_owner__without_policy__fail(
    api_client, mock_policies_false, get_cu_fi, get_project_variable_fi, role
):
    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)
    instance = get_project_variable_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__accepted__not_owner__with_policy__success(
    api_client, monkeypatch, get_cu_fi, get_project_variable_fi, role
):
    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_project_variable_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, {}, r_cu.user)
    assert response.data.get("id")


@pytest.mark.parametrize("status", NOT_ACTIVE_OR_SETUP_PROJECT_STATUS)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__update_if_status_not_setup_or_active__success(
    api_client, mock_policies_false, r_cu, get_project_fi, get_project_variable_fi, status
):

    project = get_project_fi(company=r_cu.company, status=status)
    instance = get_project_variable_fi(project=project)

    response = __get_response(api_client, instance.id, {}, r_cu.user)
    assert response.data["id"]


@pytest.mark.parametrize("status", ACTIVE_OR_SETUP_PROJECT_STATUS)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__update_if_status_setup__success(
    api_client,
    mock_policies_false,
    r_cu,
    get_project_fi,
    get_project_variable_fi,
    status,
):
    project = get_project_fi(company=r_cu.company, status=status)
    instance = get_project_variable_fi(project=project)
    response = __get_response(api_client, instance.id, data={}, user=r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(
    api_client,
    mock_policies_false,
    r_cu,
    get_project_fi,
    get_project_variable_fi,
    new_project_variable_data,
):
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance = get_project_variable_fi(project=project)

    data = new_project_variable_data(project=project)

    response = __get_response(api_client, instance_id=instance.id, data=data, user=r_cu.user)
    updated_instance = ProjectVariable.objects.get(id=instance.id)
    response_instance = response.data

    created_instance_id = response_instance.pop("id")
    assert created_instance_id

    response_project = response_instance.pop("project")
    assert response_project == {"id": instance.project.id}

    assert response_instance.pop("title") == updated_instance.title == data["title"]
    assert response_instance.pop("key") == updated_instance.key == data["key"]
    assert response_instance.pop("kind") == updated_instance.kind == data["kind"]
    assert not response_instance


@pytest.mark.xfail
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("is_user", "field", "has_object_policy", "err_text"),
    (
        (True, "is_blocked", True, NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_BLOCKED)),
        (True, "is_deleted", True, NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_DELETED)),
        (False, "is_deleted", True, NotFound.default_detail),
        (True, "is_blocked", False, NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_BLOCKED)),
        (True, "is_deleted", False, NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_DELETED)),
    ),
)
def test__not_ta__cu__fail(
    api_client, monkeypatch, r_cu, get_project_variable_fi, has_object_policy, is_user, field, err_text
):
    __get_target_policies_return = [r_cu.company.id] if has_object_policy else []
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: __get_target_policies_return)

    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    instance = get_project_variable_fi(company=r_cu.company)
    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()
    else:
        setattr(r_cu, field, True)
        r_cu.save()

    response = __get_response(
        api_client, instance.id, {}, r_cu.user, status_codes={PermissionDenied, NotFound}
    )
    assert response.data == {"detail": err_text}, f"response.data = {response.data}"


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_project__fail(
    api_client, mock_policies_false, r_cu, get_project_fi, get_project_variable_fi
):
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    project.is_deleted = True
    project.save()
    instance = get_project_variable_fi(project=project)
    response = __get_response(api_client, instance.id, {}, user=r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_project__fail(
    api_client, mock_policies_false, r_cu, get_project_fi, get_project_variable_fi
):

    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    project.is_deleted = True
    project.save()
    instance = get_project_variable_fi(project=project)
    response = __get_response(api_client, instance.id, {}, user=r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail
