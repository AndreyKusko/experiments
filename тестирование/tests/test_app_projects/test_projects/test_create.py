import functools

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated, PermissionDenied

from tests.utils import request_response_create, retrieve_response_instance
from accounts.models import USER_IS_BLOCKED, USER_IS_DELETED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from projects.models.project import Project
from ma_saas.constants.system import DATETIME_FORMAT
from ma_saas.constants.company import CUR, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_MUST_BE_ACCEPT, CompanyUser

User = get_user_model()


__get_response = functools.partial(request_response_create, path="/api/v1/projects/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, {}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(api_client, monkeypatch, r_cu, new_project_data):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    data = new_project_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user)
    response_instance = response.data

    created_instance_id = response_instance.pop("id")
    assert created_instance_id
    created_instance = Project.objects.get(id=created_instance_id)

    if response_company := retrieve_response_instance(response_instance, "company", dict):
        assert response_company.pop("id") == data["company"] == created_instance.company.id
    assert not response_company

    assert response_instance.pop("title") == data["title"] == created_instance.title
    assert response_instance.pop("description") == data["description"] == created_instance.description

    assert response_instance.pop("status") == created_instance.status
    assert response_instance.pop("created_at") == created_instance.created_at.strftime(DATETIME_FORMAT)
    assert response_instance.pop("updated_at") == created_instance.updated_at.strftime(DATETIME_FORMAT)
    assert not response_instance


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__project_scheme_auto_create(api_client, monkeypatch, r_cu, new_project_data):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    ProjectScheme = apps.get_model("projects", "ProjectScheme")
    data = new_project_data(company=r_cu.company)

    assert not ProjectScheme.objects.filter(project__title=data["title"]).exists()

    response = __get_response(api_client, data=data, user=r_cu.user)
    response_instance = response.data
    created_instance_id = response_instance.pop("id")
    assert created_instance_id
    created_instance = Project.objects.get(id=created_instance_id)
    assert ProjectScheme.objects.filter(project=created_instance).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, new_project_data):
    data = new_project_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user)
    assert Project.objects.filter(id=response.data["id"])
    assert response.data.get("id")


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__fail(api_client, monkeypatch, get_cu_fi, new_project_data, status):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    data = new_project_data(company=r_cu.company)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__without_policy__fail(api_client, mock_policies_false, get_cu_fi, new_project_data, role):
    r_cu = get_cu_fi(role=role)
    data = new_project_data(company=r_cu.company)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PermissionDenied.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__with_policy__success(api_client, monkeypatch, get_cu_fi, new_project_data, role):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu = get_cu_fi(role=role)
    data = new_project_data(company=r_cu.company)
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
    api_client, monkeypatch, r_cu, new_project_data, has_object_policy, is_user, field, err_text
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    data = new_project_data(company=r_cu.company)
    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()
    else:
        setattr(r_cu, field, True)
        r_cu.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": err_text}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_company__fail(api_client, monkeypatch, r_cu, new_project_data):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    data = new_project_data(company=r_cu.company)
    r_cu.company.is_deleted = True
    r_cu.company.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": "Company not found"}
