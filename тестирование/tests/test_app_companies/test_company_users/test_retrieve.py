import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated, PermissionDenied

from tests.utils import request_response_get, retrieve_response_instance
from tests.constants import ROLES_WITH_DIFFERENT_LOGIC
from ma_saas.constants.company import CUS, NOT_ACCEPT_CUS, NOT_OWNER_AND_NOT_WORKER_ROLES
from clients.policies.interface import Policies
from companies.models.company_user import CUS_MUST_BE_ACCEPT, NOT_TA_COMPANY_USER_REASON

User = get_user_model()


__get_response = functools.partial(request_response_get, path="/api/v1/company-users/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("cu_owner_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__data_response(api_client, monkeypatch, r_cu):

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    instance = r_cu
    response = __get_response(api_client, instance.id, instance.user)
    response_instance = response.data
    assert response_instance["id"] == instance.id

    assert response_instance.pop("id") == instance.id

    if response_user := retrieve_response_instance(response_instance, "user", dict):
        assert response_user.pop("id") == instance.user.id
        assert response_user.pop("email") == instance.user.email
        assert response_user.pop("phone") == instance.user.phone
        assert response_user.pop("first_name") == instance.user.first_name
        assert response_user.pop("last_name") == instance.user.last_name
        assert response_user.pop("middle_name") == instance.user.middle_name
        assert response_user.pop("birthdate") == instance.user.birthdate
        assert response_user.pop("city") == instance.user.city
        assert response_user.pop("lat") == instance.user.lat
        assert response_user.pop("lon") == instance.user.lon
        assert response_user.pop("avatar") == "{}"
    assert not response_user

    if response_company := retrieve_response_instance(response_instance, "company", dict):
        assert response_company.pop("id") == instance.company.id
        assert response_company.pop("title") == instance.company.title
        assert response_company.pop("logo") == instance.company.logo
        assert response_company.pop("support_email") == instance.company.support_email
        assert response_company.pop("work_wo_inn") is None
    assert not response_company
    assert response_instance.pop("role") == instance.role
    assert response_instance.pop("status") == instance.status
    assert response_instance.pop("accepted_at")
    assert response_instance.pop("created_at")
    assert response_instance.pop("updated_at")

    assert not response_instance


@pytest.mark.parametrize("status", CUS)
@pytest.mark.parametrize("role", ROLES_WITH_DIFFERENT_LOGIC)
def test__model_owner__success(api_client, mock_policies_false, get_cu_fi, role, status):
    instance = get_cu_fi(role=role, status=status.value)
    r_cu = instance
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    assert response.data
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("requesting_role", NOT_OWNER_AND_NOT_WORKER_ROLES)
@pytest.mark.parametrize("target_role", ROLES_WITH_DIFFERENT_LOGIC)
@pytest.mark.parametrize("target_status", CUS)
def test__not_owner_and_not_worker__without_policy__another_user__fail(
    api_client, mock_policies_false, get_cu_fi, requesting_role, target_role, target_status
):
    r_cu = get_cu_fi(role=requesting_role, status=CUS.ACCEPT.value)
    instance = get_cu_fi(company=r_cu.company, role=target_role, status=target_status.value)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("requesting_role", NOT_OWNER_AND_NOT_WORKER_ROLES)
@pytest.mark.parametrize("target_role", ROLES_WITH_DIFFERENT_LOGIC)
@pytest.mark.parametrize("target_status", CUS)
def test__not_owner_and_not_worker__with_policy__another_user__success(
    api_client, monkeypatch, get_cu_fi, requesting_role, target_role, target_status
):

    r_cu = get_cu_fi(role=requesting_role, status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_cu_fi(company=r_cu.company, role=target_role, status=target_status.value)
    response = __get_response(api_client, instance.id, r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("requesting_role", NOT_OWNER_AND_NOT_WORKER_ROLES)
@pytest.mark.parametrize("requesting_status", NOT_ACCEPT_CUS)
@pytest.mark.parametrize("target_role", ROLES_WITH_DIFFERENT_LOGIC)
@pytest.mark.parametrize("target_status", CUS)
def test__not_accepted__not_owner_and_not_worker__with_policy__another_user__success(
    api_client,
    monkeypatch,
    get_cu_fi,
    requesting_role,
    target_role,
    target_status,
    requesting_status,
):
    print("requesting_role =", requesting_role)
    r_cu = get_cu_fi(role=requesting_role, status=requesting_status.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_cu_fi(company=r_cu.company, role=target_role, status=target_status.value)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_COMPANY_USER_REASON.format(reason=CUS_MUST_BE_ACCEPT)}


@pytest.mark.parametrize("target_role", ROLES_WITH_DIFFERENT_LOGIC)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__another_company__fail(api_client, monkeypatch, get_cu_fi, target_role, r_cu):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_cu_fi(role=target_role)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail
