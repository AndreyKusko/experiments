import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_update, retrieve_response_instance
from projects.models.project import PROJECT_STATUS_MUST_BE_SETUP
from ma_saas.constants.company import CUR, CUS, ROLES, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from ma_saas.constants.project import NOT_SETUP_PROJECT_STATUS_VALUES, ProjectStatus
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_MUST_BE_ACCEPT
from reports.models.processed_report_form import ProjectScheme

User = get_user_model()


__get_response = functools.partial(request_response_update, path="/api/v1/project-schemes/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("project_scheme_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, {}, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(
    api_client, mock_policies_false, r_cu, get_project_scheme_fi, get_project_fi
):
    project = get_project_fi(status=ProjectStatus.SETUP.value, company=r_cu.company)
    instance = get_project_scheme_fi(project=project)
    response = __get_response(api_client, instance.id, {}, r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__without_policies__fail(
    api_client, mock_policies_false, get_cu_fi, get_project_fi, get_project_scheme_fi, status
):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    project = get_project_fi(status=ProjectStatus.SETUP.value, company=r_cu.company)
    instance = get_project_scheme_fi(project=project)

    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__with_policies__fail(
    api_client, monkeypatch, get_cu_fi, get_project_scheme_fi, get_project_fi, status
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    project = get_project_fi(status=ProjectStatus.SETUP.value, company=r_cu.company)
    instance = get_project_scheme_fi(project=project)

    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__without_policies__fail(
    api_client, mock_policies_false, get_cu_fi, get_project_fi, get_project_scheme_fi, role
):
    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)
    project = get_project_fi(status=ProjectStatus.SETUP.value, company=r_cu.company)
    instance = get_project_scheme_fi(project=project)
    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__with_policy__success(
    api_client, monkeypatch, get_cu_fi, get_project_scheme_fi, get_project_fi, role
):

    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    project = get_project_fi(status=ProjectStatus.SETUP.value, company=r_cu.company)
    instance = get_project_scheme_fi(project=project)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    response = __get_response(api_client, instance.id, {}, r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("role", ROLES)
def test__user_from_different_company__fail(api_client, monkeypatch, get_cu_fi, get_project_scheme_fi, role):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)

    instance = get_project_scheme_fi()
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__remove_specialization__success(
    api_client,
    monkeypatch,
    r_cu,
    get_project_scheme_fi,
    get_specialisation_fi,
    new_project_scheme_data,
    get_project_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    specialisation = get_specialisation_fi()
    instance = get_project_scheme_fi(project=project, specialisation=specialisation)
    assert instance.specialisation
    data = {"specialisation": None}
    response = __get_response(
        api_client,
        instance.id,
        data,
        r_cu.user,
    )
    updated_instance = ProjectScheme.objects.get(id=instance.id)
    assert updated_instance.specialisation is None
    response_instance = response.data
    assert response_instance["specialisation"] == {}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("is_specialisation", (True, False))
def test__response_data(
    api_client,
    monkeypatch,
    r_cu,
    get_project_scheme_fi,
    new_project_scheme_data,
    get_project_fi,
    get_specialisation_fi,
    is_specialisation,
):

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance = get_project_scheme_fi(project=project)
    specialisation = get_specialisation_fi() if is_specialisation else None

    new_data = new_project_scheme_data(specialisation=specialisation)
    response = __get_response(api_client, instance.id, new_data, r_cu.user)
    updated_instance = ProjectScheme.objects.get(id=instance.id)

    response_instance = response.data

    assert response_instance.pop("id") == instance.id

    if response_project := retrieve_response_instance(response_instance, "project", dict):
        assert response_project.pop("id") == updated_instance.project.id == instance.project.id
        assert response_project.pop("title") == updated_instance.project.title == instance.project.title
    assert not response_project

    if is_specialisation:
        if response_specialisation := retrieve_response_instance(response_instance, "specialisation", dict):
            assert response_specialisation.pop("id") == updated_instance.specialisation.id
            assert response_specialisation.pop("title") == updated_instance.specialisation.title
        assert not response_specialisation
    else:
        assert response_instance.pop("specialisation") == {}

    assert response_instance.pop("title") == updated_instance.title
    assert response_instance.pop("color") == updated_instance.color

    assert response_instance.pop("created_at")
    assert response_instance.pop("updated_at")
    assert response_instance.pop("service_name_for_receipt") == updated_instance.service_name_for_receipt
    assert response_instance.pop("is_labour_exchange") == updated_instance.is_labour_exchange
    assert response_instance.pop("entered_labour_exchange_at") == updated_instance.entered_labour_exchange_at
    assert not response_instance, f"response_instance = {response_instance}"


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("status", NOT_SETUP_PROJECT_STATUS_VALUES)
def test__not_setup_project__fail(
    api_client, monkeypatch, r_cu, get_project_scheme_fi, get_project_fi, status
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    project = get_project_fi(company=r_cu.company, status=status)
    instance = get_project_scheme_fi(project=project)

    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=ValidationError)
    assert (
        response.data["non_field_errors"][0] == PROJECT_STATUS_MUST_BE_SETUP
    ), f"response.data = {response.data}"


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__duplicates__success(
    api_client, monkeypatch, r_cu, get_project_scheme_fi, new_project_scheme_data, get_project_fi
):

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    duplicate_instance = get_project_scheme_fi(project=project)

    instance = get_project_scheme_fi(
        project=duplicate_instance.project, specialisation=duplicate_instance.specialisation
    )

    new_data = new_project_scheme_data(title=duplicate_instance.title)
    response = __get_response(api_client, instance.id, new_data, r_cu.user)

    updated_instance = ProjectScheme.objects.get(id=instance.id)
    assert response.data["project"]["id"] == updated_instance.project.id == duplicate_instance.project.id
    assert response.data["title"] == updated_instance.title == duplicate_instance.title


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__restricted_field__not_updating(
    api_client, monkeypatch, r_cu, get_project_scheme_fi, new_project_scheme_data, get_project_fi
):

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance = get_project_scheme_fi(project=project)
    instance_new_data = new_project_scheme_data(project=instance.project)
    response = __get_response(api_client, instance.id, instance_new_data, r_cu.user)
    updated_instance_data = ProjectScheme.objects.get(id=instance.id)
    assert response.data["project"]["id"] == updated_instance_data.project.id == instance.project.id
