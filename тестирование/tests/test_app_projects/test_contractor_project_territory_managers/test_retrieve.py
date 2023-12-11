import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated, PermissionDenied

from tests.utils import request_response_get, retrieve_response_instance
from accounts.models import USER_IS_BLOCKED, USER_IS_DELETED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.constants.company import NOT_ACCEPT_CUS
from clients.policies.interface import Policies
from companies.models.company_user import CompanyUser

User = get_user_model()

__get_response = functools.partial(
    request_response_get, path="/api/v1/contractor-project-territory-managers/"
)


@pytest.mark.parametrize("pt_manager", [pytest.lazy_fixture("contractor_pt_manager_fi")])
def test__anonymous_user__fail(api_client, pt_manager):
    response = __get_response(api_client, pt_manager.id, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, get_contractor_pt_manager_fi):
    instance = get_contractor_pt_manager_fi(company=r_cu.company)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__not_accepted_owner__fail(api_client, monkeypatch, r_cu, get_contractor_pt_manager_fi):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    instance = get_contractor_pt_manager_fi(company=r_cu.company)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager__with_policy__success(api_client, monkeypatch, r_cu, get_contractor_pt_manager_fi):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    instance = get_contractor_pt_manager_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_manager__with_policy__fail(
    api_client, monkeypatch, get_cu_manager_fi, get_contractor_pt_manager_fi, status
):
    r_cu = get_cu_manager_fi(status=status)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    instance = get_contractor_pt_manager_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager__without_policy__fail(api_client, monkeypatch, r_cu, get_contractor_pt_manager_fi):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    instance = get_contractor_pt_manager_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.xfail()
@pytest.mark.parametrize("pt_manager", [pytest.lazy_fixture("contractor_pt_manager_fi")])
def test__pt_manager_model_owner__success(api_client, monkeypatch, pt_manager):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    r_cu = pt_manager.company_user
    response = __get_response(api_client, pt_manager.id, r_cu.user)
    assert response.data["id"] == pt_manager.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__different_company_user__fail(api_client, monkeypatch, r_cu, get_contractor_pt_manager_fi):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    instance = get_contractor_pt_manager_fi()
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("is_user", "field", "err_text"),
    (
        (True, "is_blocked", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_BLOCKED)),
        (True, "is_deleted", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_DELETED)),
        # (False, "is_deleted", REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY),
        (False, "is_deleted", NotFound.default_detail),
    ),
)
@pytest.mark.parametrize("is_policy", [True, False])
def test__not_ta__cu__fail(
    api_client, monkeypatch, r_cu, get_contractor_pt_manager_fi, is_policy, is_user, field, err_text
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: is_policy)
    target_policies = [r_cu.company.id] if is_policy else []
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: target_policies)
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()
    else:
        setattr(r_cu, field, True)
        r_cu.save()
    instance = get_contractor_pt_manager_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes={PermissionDenied, NotFound})
    assert response.data == {"detail": err_text}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(api_client, monkeypatch, r_cu, get_contractor_pt_manager_fi):

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    instance = get_contractor_pt_manager_fi(company=r_cu.company)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    response_instance = response.data
    assert response_instance.pop("id") == instance.id
    assert response_instance.pop("project_territory") == instance.project_territory.id
    if response_cu := retrieve_response_instance(response_instance, "company_user", dict):
        assert response_cu.pop("id") == instance.company_user.id
        if response_u := retrieve_response_instance(response_cu, "user", dict):
            assert response_u.pop("id") == instance.company_user.user.id
            assert response_u.pop("email") == instance.company_user.user.email
            assert response_u.pop("phone") == instance.company_user.user.phone
            assert response_u.pop("first_name") == instance.company_user.user.first_name
            assert response_u.pop("last_name") == instance.company_user.user.last_name
            assert response_u.pop("middle_name") == instance.company_user.user.middle_name
            assert response_u.pop("city") == instance.company_user.user.city
            assert response_u.pop("lat") == instance.company_user.user.lat
            assert response_u.pop("lon") == instance.company_user.user.lon
            assert response_u.pop("birthdate")
            assert response_u.pop("avatar") == "{}"
            assert not response_u
        if response_company := retrieve_response_instance(response_cu, "company", dict):
            assert response_company.pop("id") == instance.company_user.company.id
            assert response_company.pop("title") == instance.company_user.company.title
            assert response_company.pop("logo")
            assert response_company.pop("support_email") == instance.company_user.company.support_email
            assert response_company.pop("work_wo_inn") == instance.company_user.company.work_wo_inn
            assert not response_company
        assert response_cu.pop("created_at")
        assert response_cu.pop("updated_at")
        assert response_cu.pop("role") == instance.company_user.role
        assert response_cu.pop("status") == instance.company_user.status
        assert response_cu.pop("accepted_at")
        assert not response_cu
    assert not response_instance
