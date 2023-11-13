import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated

from tests.utils import request_response_list, retrieve_response_instance
from ma_saas.constants.company import CUR, CUS, ROLES, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from clients.policies.interface import Policies

User = get_user_model()

__get_response = functools.partial(request_response_list, path="/api/v1/project-schemes/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


def test__user_without_companies_got_nothing(api_client, monkeypatch, user_fi: User):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    response = __get_response(api_client, user=user_fi)
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("qty", (1, 3))
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, get_project_scheme_fi, qty):
    instances = [get_project_scheme_fi(company=r_cu.company) for _ in range(qty)]
    instances.reverse()
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == qty
    for index, response_instance in enumerate(response.data):
        assert response_instance["id"] == instances[index].id


@pytest.mark.xfail
@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__with_policy__fail(
    api_client, monkeypatch, get_cu_fi, get_project_scheme_fi, status
):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    get_project_scheme_fi(company=r_cu.company)

    response = __get_response(api_client, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__without_policy__fail(
    api_client, monkeypatch, get_cu_fi, get_project_scheme_fi, status
):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    get_project_scheme_fi(company=r_cu.company)

    response = __get_response(api_client, r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__without_policy__fail(api_client, monkeypatch, get_cu_fi, get_project_scheme_fi, role):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    get_project_scheme_fi()

    response = __get_response(api_client, r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__with_policy__success(api_client, monkeypatch, get_cu_fi, get_project_scheme_fi, role):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_project_scheme_fi(company=r_cu.company)

    response = __get_response(api_client, r_cu.user)
    assert response.data[0]["id"] == instance.id


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", CUS)
@pytest.mark.parametrize("qty", (1, 3))
def test__different_company_user__fail(
    api_client, monkeypatch, get_cu_fi, get_project_scheme_fi, role, status, qty
):
    r_cu = get_cu_fi(role=role, status=status.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    [get_project_scheme_fi() for _ in range(qty)]
    response = __get_response(api_client, user=r_cu.user)
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("qty", (3,))
@pytest.mark.parametrize("is_specialisation", (True, False))
def test__response_data(
    api_client, monkeypatch, r_cu, get_specialisation_fi, is_specialisation, get_project_scheme_fi, qty
):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    specialisation = get_specialisation_fi() if is_specialisation else None
    instances = [
        get_project_scheme_fi(company=r_cu.company, specialisation=specialisation) for _ in range(qty)
    ]
    instances.reverse()

    response = __get_response(api_client, user=r_cu.user)
    for index, response_instance in enumerate(response.data):
        assert response_instance.pop("id") == instances[index].id

        if response_project := retrieve_response_instance(response_instance, "project", dict):
            assert response_project.pop("id") == instances[index].project.id
            assert response_project.pop("title") == instances[index].project.title
        assert not response_project

        if is_specialisation:
            if response_specialisation := retrieve_response_instance(
                response_instance, "specialisation", dict
            ):
                assert response_specialisation.pop("id") == instances[index].specialisation.id
                assert response_specialisation.pop("title") == instances[index].specialisation.title
            assert not response_specialisation
        else:
            assert response_instance.pop("specialisation") == {}
        assert response_instance.pop("is_labour_exchange") == instances[index].is_labour_exchange
        assert (
            response_instance.pop("entered_labour_exchange_at") == instances[index].entered_labour_exchange_at
        )
        assert response_instance.pop("service_name_for_receipt") == instances[index].service_name_for_receipt
        assert response_instance.pop("title") == instances[index].title
        assert response_instance.pop("color") == instances[index].color
        assert response_instance.pop("created_at")
        assert response_instance.pop("updated_at")

        assert not response_instance
