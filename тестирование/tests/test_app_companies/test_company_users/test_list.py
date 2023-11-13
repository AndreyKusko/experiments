import functools
import itertools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated

from tests.utils import request_response_list, retrieve_response_instance
from ma_saas.constants.company import CUR, CUS, ROLES, NOT_ACCEPT_CUS
from clients.policies.interface import Policies

User = get_user_model()

CONTRACTOR_ROLE_STATUS_COMBINATIONS = list(itertools.product(ROLES, CUS.values))
CLIENT_ROLE_STATUS_COMBINATIONS = list(itertools.product(ROLES, CUS.values))


__get_response = functools.partial(request_response_list, path="/api/v1/company-users/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


def test__random_user__empty_response(api_client, monkeypatch, user_fi: User, get_cu_fi):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    get_cu_fi()
    response = __get_response(api_client, user=user_fi)
    assert not response.data


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", CUS)
def test__response_data(api_client, monkeypatch, get_cu_fi, role, status):
    instance = get_cu_fi(role=role, status=status.value)
    r_cu = instance
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    response = __get_response(api_client, r_cu.user)

    assert len(response.data) == 1
    response_instance = response.data[0]
    assert response_instance.pop("id") == instance.id

    if response_user := retrieve_response_instance(response_instance, "user", dict):
        assert response_user.pop("id") == instance.user.id
        assert response_user.pop("email") == instance.user.email
        assert response_user.pop("phone") == instance.user.phone
        assert response_user.pop("first_name") == instance.user.first_name
        assert response_user.pop("middle_name") == instance.user.middle_name
        assert response_user.pop("last_name") == instance.user.last_name
        assert response_user.pop("birthdate") == str(instance.user.birthdate)
        assert response_user.pop("city") == instance.user.city
        assert response_user.pop("lat") == instance.user.lat
        assert response_user.pop("lon") == instance.user.lon
        assert response_user.pop("avatar") == "{}"
    assert not response_user, f"response_user = {response_user}"

    if response_company := retrieve_response_instance(response_instance, "company", dict):
        assert response_company.pop("id") == instance.company.id
        assert response_company.pop("title") == instance.company.title
        assert response_company.pop("logo") == instance.company.logo
        assert response_company.pop("support_email") == instance.company.support_email
        assert response_company.pop("work_wo_inn") is None
    assert not response_company, f"company = {response_company}"

    assert response_instance.pop("role") == role
    assert response_instance.pop("status") == status.value
    accepted_at = response_instance.pop("accepted_at")
    assert accepted_at or accepted_at is None
    assert response_instance.pop("created_at")
    assert response_instance.pop("updated_at")

    assert not response_instance, f"response_instance = {response_instance}"


@pytest.mark.parametrize("status", CUS)
def test__contractor_worker__got_only_self_model(api_client, monkeypatch, get_cu_fi, status):
    instance = get_cu_fi(role=CUR.WORKER, status=status.value)
    r_cu = instance
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    c = instance.company
    [get_cu_fi(role=r, status=s, company=c) for r, s in CONTRACTOR_ROLE_STATUS_COMBINATIONS]
    response = __get_response(api_client, r_cu.user)
    assert len(response.data) == 1
    assert response.data[0]["id"] == instance.id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__contractor_not_accepted_manager__got_self_model_only(api_client, monkeypatch, get_cu_fi, status):
    instance = get_cu_fi(role=CUR.PROJECT_MANAGER, status=status.value)
    r_cu = instance
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    c = instance.company
    [get_cu_fi(role=r, status=s, company=c) for r, s in CONTRACTOR_ROLE_STATUS_COMBINATIONS]
    response = __get_response(api_client, r_cu.user)
    assert len(response.data) == 1
    assert response.data[0]["id"] == instance.id


def test__contractor_owner_got_self_and_other_staff(api_client, monkeypatch, get_cu_fi):
    instance = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    r_cu = instance
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    c = instance.company
    [get_cu_fi(role=r, status=s, company=c) for r, s in CONTRACTOR_ROLE_STATUS_COMBINATIONS]
    response = __get_response(api_client, r_cu.user)
    assert len(response.data) == len(CONTRACTOR_ROLE_STATUS_COMBINATIONS) + 1


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__contractor_not_accepted_owner_got_self_model(api_client, monkeypatch, get_cu_fi, status):
    instance = get_cu_fi(role=CUR.OWNER, status=status.value)
    r_cu = instance
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    c = instance.company
    [get_cu_fi(role=r, status=s, company=c) for r, s in CONTRACTOR_ROLE_STATUS_COMBINATIONS]
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == 1
    assert response.data[0]["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__contractor_not_see_users_from_another_company(api_client, monkeypatch, r_cu, get_cu_fi):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    [get_cu_fi(role=r, status=s) for r, s in CONTRACTOR_ROLE_STATUS_COMBINATIONS]
    response = __get_response(api_client, r_cu.user)
    assert len(response.data) == 1


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__client_manager__got_only_self_model(api_client, monkeypatch, get_cu_fi, r_cu):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    [get_cu_fi(role=r, status=s, company=r_cu.company) for r, s in CLIENT_ROLE_STATUS_COMBINATIONS]
    response = __get_response(api_client, r_cu.user)
    assert len(response.data) == 1
    assert response.data[0]["id"] == r_cu.id


def test__client_owner__got_self_and_other_staff(api_client, monkeypatch, get_cu_fi):
    instance = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)

    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    c = instance.company
    [get_cu_fi(role=r, status=s, company=c) for r, s in CLIENT_ROLE_STATUS_COMBINATIONS]
    response = __get_response(api_client, user=instance.user)
    assert len(response.data) == len(CLIENT_ROLE_STATUS_COMBINATIONS) + 1


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__client_not_accepted_owner__got_self_model(api_client, monkeypatch, get_cu_fi, status):
    instance = get_cu_fi(role=CUR.OWNER, status=status.value)
    r_cu = instance
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    [get_cu_fi(role=r, status=s, company=instance.company) for r, s in CLIENT_ROLE_STATUS_COMBINATIONS]
    response = __get_response(api_client, r_cu.user)
    assert len(response.data) == 1
    assert response.data[0]["id"] == instance.id
