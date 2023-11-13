import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated

from tests.utils import request_response_get, retrieve_response_instance
from ma_saas.constants.system import Callable
from ma_saas.constants.company import CUR, CUS, ROLES, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from clients.policies.interface import Policies

User = get_user_model()


__get_response = functools.partial(request_response_get, path="/api/v1/project-schemes/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("processed_report_form_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, get_project_scheme_fi, r_cu):
    instance = get_project_scheme_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.xfail
@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__with_policy__fail(
    api_client, monkeypatch, get_cu_fi, get_project_scheme_fi, status
):

    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    instance = get_project_scheme_fi(company=r_cu.company)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__without_policy__fail(
    api_client, mock_policies_false, get_cu_fi, get_project_scheme_fi, status
):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    instance = get_project_scheme_fi(company=r_cu.company)

    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__without_policies__fail(
    api_client, mock_policies_false, get_cu_fi, get_project_scheme_fi, role
):
    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)
    instance = get_project_scheme_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__with_policies__success(api_client, monkeypatch, get_cu_fi, get_project_scheme_fi, role):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)
    instance = get_project_scheme_fi(company=r_cu.company)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    response = __get_response(api_client, instance.id, r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("is_specialisation", (True, False))
def test__response_data(
    api_client, monkeypatch, get_project_scheme_fi, get_specialisation_fi, is_specialisation, r_cu
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    specialisation = get_specialisation_fi() if is_specialisation else None
    instance = get_project_scheme_fi(company=r_cu.company, specialisation=specialisation)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    response = __get_response(api_client, instance.id, r_cu.user)
    response_instance = response.data
    assert response_instance.pop("id") == instance.id

    if response_project := retrieve_response_instance(response_instance, "project", dict):
        assert response_project.pop("id") == instance.project.id
        assert response_project.pop("title") == instance.project.title
    assert not response_project

    if is_specialisation:
        if response_specialisation := retrieve_response_instance(response_instance, "specialisation", dict):
            assert response_specialisation.pop("id") == instance.specialisation.id
            assert response_specialisation.pop("title") == instance.specialisation.title
        assert not response_specialisation
    else:
        assert response_instance.pop("specialisation") == {}

    assert response_instance.pop("title") == instance.title
    assert response_instance.pop("color") == instance.color

    assert response_instance.pop("created_at")
    assert response_instance.pop("updated_at")
    assert response_instance.pop("service_name_for_receipt") == instance.service_name_for_receipt
    assert response_instance.pop("is_labour_exchange") == instance.is_labour_exchange
    assert response_instance.pop("entered_labour_exchange_at") == instance.entered_labour_exchange_at
    assert not response_instance, f"response_instance = {response_instance}"


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", CUS)
def test__user_from_different_company__fail(
    api_client, monkeypatch, get_cu_fi, get_project_scheme_fi, role, status
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu = get_cu_fi(status=status.value, role=role)
    instance = get_project_scheme_fi()

    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [instance.project.id])

    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}
