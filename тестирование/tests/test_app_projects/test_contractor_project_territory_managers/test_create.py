import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_create, retrieve_response_instance
from accounts.models import (
    USER_IS_BLOCKED,
    USER_IS_DELETED,
    NOT_TA_USER_REASON,
    NOT_TA_REQUESTING_USER_REASON,
)
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from ma_saas.constants.company import CUR, CUS, NOT_ACCEPT_CUS, NOT_ACCEPT_OR_INVITE_CUS
from clients.policies.interface import Policies
from companies.models.company_user import (
    CU_IS_DELETED,
    NOT_TA_TARGET_CU_REASON,
    NOT_TA_RCU_MUST_BE_ACCEPT,
    CUS_MUST_BE_ACCEPT_OR_INVITE,
    CompanyUser,
)
from projects.models.contractor_project_territory_manager import (
    UNIQ_CONSTRAINT_ERR,
    ContractorProjectTerritoryManager,
)

User = get_user_model()

__get_response = functools.partial(
    request_response_create, path="/api/v1/contractor-project-territory-managers/"
)


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, {}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, new_contractor_pt_manager_data):
    data = new_contractor_pt_manager_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user)
    new_instance = ContractorProjectTerritoryManager.objects.get(**data)
    assert response.data["id"] == new_instance.id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__fail(
    api_client, monkeypatch, get_cu_owner_fi, new_contractor_pt_manager_data, status
):
    r_cu = get_cu_owner_fi(status=status)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    data = new_contractor_pt_manager_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}
    assert not ContractorProjectTerritoryManager.objects.filter(**data).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
@pytest.mark.parametrize("status", (CUS.ACCEPT, CUS.INVITE))
def test__accepted_manager__with_policy__success(
    api_client, monkeypatch, get_cu_manager_fi, r_cu, new_contractor_pt_manager_data, status
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    target_cu = get_cu_manager_fi(company=r_cu.company, status=status.value)
    data = new_contractor_pt_manager_data(company_user=target_cu)
    response = __get_response(api_client, data=data, user=r_cu.user)
    new_instance = ContractorProjectTerritoryManager.objects.get(**data)
    assert response.data["id"] == new_instance.id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_manager__with_policy__success(
    api_client, monkeypatch, get_cu_manager_fi, new_contractor_pt_manager_data, status
):
    r_cu = get_cu_manager_fi(status=status)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    target_cu = get_cu_manager_fi(company=r_cu.company)
    data = new_contractor_pt_manager_data(company_user=target_cu)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}
    assert not ContractorProjectTerritoryManager.objects.filter(**data).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager__without_policy__fail(
    api_client, mock_policies_false, get_cu_manager_fi, r_cu, new_contractor_pt_manager_data
):
    target_cu = get_cu_manager_fi(company=r_cu.company)
    data = new_contractor_pt_manager_data(company_user=target_cu)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PermissionDenied.default_detail}


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__accepted_worker__with_policy__success(
    api_client, monkeypatch, get_cu_manager_fi, pt_worker, new_contractor_pt_manager_data
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    r_cu, pt = pt_worker.company_user, pt_worker.project_territory
    target_cu = get_cu_manager_fi(company=r_cu.company)
    data = new_contractor_pt_manager_data(project_territory=pt, company_user=target_cu)
    response = __get_response(api_client, data=data, user=r_cu.user)
    new_instance = ContractorProjectTerritoryManager.objects.get(**data)
    assert response.data["id"] == new_instance.id


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__accepted_worker__without_policy__fail(
    api_client, mock_policies_false, get_cu_manager_fi, pt_worker, new_contractor_pt_manager_data
):
    r_cu, pt = pt_worker.company_user, pt_worker.project_territory
    target_cu = get_cu_manager_fi(company=r_cu.company)
    data = new_contractor_pt_manager_data(project_territory=pt, company_user=target_cu)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PermissionDenied.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__appoint_user_from_different_company__fail(
    api_client, monkeypatch, r_cu, get_cu_manager_fi, new_contractor_pt_manager_data
):
    target_cu = get_cu_manager_fi()
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    data = new_contractor_pt_manager_data(company_user=target_cu, company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("target_role", [role for role in CUR.list if role != CUR.PROJECT_MANAGER])
def test__appoint_not_manager__success(
    api_client, monkeypatch, r_cu, get_cu_fi, new_contractor_pt_manager_data, target_role
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    target_cu = get_cu_fi(role=target_role, company=r_cu.company)
    data = new_contractor_pt_manager_data(company=r_cu.company, company_user=target_cu)
    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instance = ContractorProjectTerritoryManager.objects.get(**data)
    assert response.data["id"] == created_instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("status", NOT_ACCEPT_OR_INVITE_CUS)
def test__not_accepted_and_not_invited__target_user__fail(
    api_client, monkeypatch, r_cu, get_cu_manager_fi, new_contractor_pt_manager_data, status
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    company = r_cu.company
    target_cu = get_cu_manager_fi(status=status.value, company=company)
    data = new_contractor_pt_manager_data(company=company, company_user=target_cu)
    response = __get_response(api_client, data, r_cu.user, status_codes=ValidationError)
    assert response.data == {
        "company_user": [NOT_TA_TARGET_CU_REASON.format(reason=CUS_MUST_BE_ACCEPT_OR_INVITE)]
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__duplicates__fail(
    api_client, monkeypatch, r_cu, new_contractor_pt_manager_data, get_contractor_pt_manager_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    duplicate_instance = get_contractor_pt_manager_fi(company=r_cu.company)
    cu, pt = duplicate_instance.company_user, duplicate_instance.project_territory
    data = new_contractor_pt_manager_data(company_user=cu, project_territory=pt)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == [UNIQ_CONSTRAINT_ERR.format(company_user=cu.id, project_territory=pt.id)]


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
    new_contractor_pt_manager_data,
    has_object_policy,
    is_user,
    field,
    err_text,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    data = new_contractor_pt_manager_data(company=r_cu.company)
    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()
    else:
        setattr(r_cu, field, True)
        r_cu.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": err_text}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("is_user", "field", "err_text"),
    (
        (
            True,
            "is_blocked",
            NOT_TA_TARGET_CU_REASON.format(reason=NOT_TA_USER_REASON.format(reason=USER_IS_BLOCKED)),
        ),
        (
            True,
            "is_deleted",
            NOT_TA_TARGET_CU_REASON.format(reason=NOT_TA_USER_REASON.format(reason=USER_IS_DELETED)),
        ),
        (False, "is_deleted", NOT_TA_TARGET_CU_REASON.format(reason=CU_IS_DELETED)),
    ),
)
@pytest.mark.parametrize("has_object_policy", [True, False])
def test__not_ta__target_cu__fail(
    api_client,
    monkeypatch,
    r_cu,
    new_project_scheme_data,
    new_contractor_pt_manager_data,
    get_cu_manager_fi,
    has_object_policy,
    is_user,
    field,
    err_text,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    target_cu = get_cu_manager_fi(company=r_cu.company)
    data = new_contractor_pt_manager_data(company=r_cu.company, company_user=target_cu)
    if is_user:
        setattr(target_cu.user, field, True)
        target_cu.user.save()
    else:
        setattr(target_cu, field, True)
        target_cu.save()
    response = __get_response(api_client, data, r_cu.user, status_codes={PermissionDenied, ValidationError})
    assert response.data == {"company_user": [err_text]}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(api_client, monkeypatch, r_cu, new_contractor_pt_manager_data):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    data = new_contractor_pt_manager_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user)
    new_instance = ContractorProjectTerritoryManager.objects.get(**data)

    response_instance = response.data
    assert response_instance.pop("id") == new_instance.id
    assert response_instance.pop("project_territory") == new_instance.project_territory.id
    if response_cu := retrieve_response_instance(response_instance, "company_user", dict):
        assert response_cu.pop("id") == new_instance.company_user.id
        assert response_cu.pop("role") == new_instance.company_user.role
        assert response_cu.pop("status") == new_instance.company_user.status
        assert response_cu.pop("accepted_at")
        assert response_cu.pop("created_at")
        assert response_cu.pop("updated_at")
        if response_u := retrieve_response_instance(response_cu, "user", dict):
            assert response_u.pop("id") == new_instance.company_user.user.id
            assert response_u.pop("email") == new_instance.company_user.user.email
            assert response_u.pop("phone") == new_instance.company_user.user.phone
            assert response_u.pop("avatar") == "{}"
            assert response_u.pop("first_name") == new_instance.company_user.user.first_name
            assert response_u.pop("middle_name") == new_instance.company_user.user.middle_name
            assert response_u.pop("last_name") == new_instance.company_user.user.last_name
            assert response_u.pop("city") == new_instance.company_user.user.city
            assert response_u.pop("lat") == new_instance.company_user.user.lat
            assert response_u.pop("lon") == new_instance.company_user.user.lon
            assert response_u.pop("birthdate")
            assert not response_u
        if response_company := retrieve_response_instance(response_cu, "company", dict):
            assert response_company.pop("id") == new_instance.company_user.company.id
            assert response_company.pop("title") == new_instance.company_user.company.title
            assert response_company.pop("logo") == new_instance.company_user.company.logo
            assert response_company.pop("support_email") == new_instance.company_user.company.support_email
            assert response_company.pop("work_wo_inn") == new_instance.company_user.company.work_wo_inn
            assert not response_company
        assert not response_cu
    assert not response_instance
