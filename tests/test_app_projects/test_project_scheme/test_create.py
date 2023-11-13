import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_create, retrieve_response_instance
from accounts.models import USER_IS_BLOCKED, USER_IS_DELETED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from projects.models.project import PROJECT_STATUS_MUST_BE_SETUP
from companies.models.company import COMPANY_IS_DELETED, NOT_TA_COMPANY_REASON
from ma_saas.constants.company import CUR, CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from ma_saas.constants.project import NOT_ACTIVE_OR_SETUP_PROJECT_STATUS_VALUES, ProjectStatus
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_REASON, NOT_TA_RCU_MUST_BE_ACCEPT, CompanyUser
from projects.models.project_scheme import ProjectScheme

User = get_user_model()

INVALID_FIELD_DATA_TYPES = {str: 123, bool: "qwe", int: "qwe", list: "qwe"}


__get_response = functools.partial(request_response_create, path="/api/v1/project-schemes/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, {}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__without_policy__success(
    api_client, mock_policies_false, r_cu, get_project_fi, new_project_scheme_data
):
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance_data = new_project_scheme_data(project=project)
    response = __get_response(api_client, instance_data, r_cu.user)
    assert response.data["id"]


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__without_policy__fail(
    api_client, mock_policies_false, get_cu_fi, get_project_fi, new_project_scheme_data, status
):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance_data = new_project_scheme_data(project=project)
    response = __get_response(api_client, instance_data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__with_policy__fail(
    api_client, monkeypatch, get_cu_fi, get_project_fi, new_project_scheme_data, status
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance_data = new_project_scheme_data(project=project)
    response = __get_response(api_client, instance_data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner_without_policy__fail(
    api_client, mock_policies_false, get_cu_fi, get_project_fi, new_project_scheme_data, role
):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance_data = new_project_scheme_data(project=project)
    response = __get_response(api_client, instance_data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PermissionDenied.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__with_policy__success(
    api_client, monkeypatch, get_cu_fi, get_project_fi, new_project_scheme_data, role
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    r_cu = get_cu_fi(role=role)
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance_data = new_project_scheme_data(project=project)
    response = __get_response(api_client, instance_data, r_cu.user)
    assert response.data["id"]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("is_specialisation", (True, False))
def test__response_data(
    api_client,
    monkeypatch,
    r_cu,
    get_project_fi,
    get_specialisation_fi,
    new_project_scheme_data,
    is_specialisation,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    specialisation = get_specialisation_fi() if is_specialisation else None
    instance_data = new_project_scheme_data(project=project, specialisation=specialisation)

    response = __get_response(api_client, instance_data, r_cu.user)

    response_instance = response.data
    instance_id = response_instance.pop("id")
    created_instance = ProjectScheme.objects.get(id=instance_id)
    assert response_instance.pop("title") == instance_data["title"] == created_instance.title

    if response_project := retrieve_response_instance(response_instance, "project", dict):
        assert response_project.pop("id") == created_instance.project.id == instance_data["project"]
        assert response_project.pop("title") == created_instance.project.title
    assert not response_project
    if response_specialisation := retrieve_response_instance(response_instance, "specialisation", dict):
        if is_specialisation:
            assert instance_data["specialisation"] == created_instance.specialisation.id
            assert instance_data["specialisation"] == response_specialisation.pop("id")
            assert response_specialisation.pop("title") == created_instance.specialisation.title
    assert not response_specialisation

    assert response_instance.pop("service_name_for_receipt") == created_instance.service_name_for_receipt
    assert created_instance.service_name_for_receipt == instance_data["service_name_for_receipt"]

    assert response_instance.pop("is_labour_exchange") == created_instance.is_labour_exchange
    assert created_instance.is_labour_exchange == instance_data["is_labour_exchange"]

    assert response_instance.pop("color") == created_instance.color == instance_data["color"]
    assert response_instance.pop("entered_labour_exchange_at") is None
    assert response_instance.pop("created_at")
    assert response_instance.pop("updated_at")
    assert not response_instance


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__user_from_different_company__with_policy__fail(
    api_client, monkeypatch, new_project_scheme_data, r_cu
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    data = new_project_scheme_data()
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("status", NOT_ACTIVE_OR_SETUP_PROJECT_STATUS_VALUES)
def test__project_status_not_setup__fail(
    api_client, monkeypatch, r_cu, new_project_scheme_data, get_project_fi, status
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    project = get_project_fi(company=r_cu.company, status=status)
    instance_data = new_project_scheme_data(project=project)
    response = __get_response(api_client, instance_data, r_cu.user, status_codes=ValidationError)
    assert response.data == {"project": [PROJECT_STATUS_MUST_BE_SETUP]}, f"response ={response.data}"


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_company__fail(api_client, monkeypatch, r_cu, get_project_fi, new_project_scheme_data):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    data = new_project_scheme_data(project=project)
    r_cu.company.is_deleted = True
    r_cu.company.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": NOT_TA_RCU_REASON.format(reason=NOT_TA_COMPANY_REASON.format(reason=COMPANY_IS_DELETED))
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_project__fail(api_client, monkeypatch, r_cu, new_project_scheme_data, get_project_fi):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    data = new_project_scheme_data(project=project)
    project.is_deleted = True
    project.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": "Project not found"}


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
    api_client,
    monkeypatch,
    r_cu,
    new_project_scheme_data,
    get_project_fi,
    has_object_policy,
    is_user,
    field,
    err_text,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)

    data = new_project_scheme_data(project=project)
    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()
    else:
        setattr(r_cu, field, True)
        r_cu.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": err_text}
