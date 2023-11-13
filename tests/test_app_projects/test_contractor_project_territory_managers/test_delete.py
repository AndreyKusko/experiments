import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated, PermissionDenied

from tests.utils import request_response_delete
from accounts.models import USER_IS_BLOCKED, USER_IS_DELETED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.constants.system import Callable
from ma_saas.constants.company import NOT_ACCEPT_CUS
from clients.policies.interface import Policies
from companies.models.company_user import CompanyUser
from projects.models.contractor_project_territory_manager import ContractorProjectTerritoryManager

User = get_user_model()

__get_response = functools.partial(
    request_response_delete, path="/api/v1/contractor-project-territory-managers/"
)


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("contractor_pt_manager_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codes={NotAuthenticated.status_code})
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, get_contractor_pt_manager_fi):
    instance = get_contractor_pt_manager_fi(company=r_cu.company)
    assert __get_response(api_client, instance_id=instance.id, user=r_cu.user)


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__fail(
    api_client, monkeypatch, get_cu_owner_fi, get_contractor_pt_manager_fi, status
):
    r_cu = get_cu_owner_fi(status=status.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    # monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    instance = get_contractor_pt_manager_fi(company=r_cu.company)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager__with_policy__success(api_client, monkeypatch, r_cu, get_contractor_pt_manager_fi):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    instance = get_contractor_pt_manager_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user)
    assert not response.data
    assert not ContractorProjectTerritoryManager.objects.existing().filter(id=instance.id).exists()
    assert ContractorProjectTerritoryManager.objects.filter(id=instance.id).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager__without_policy__fail(api_client, monkeypatch, r_cu, get_contractor_pt_manager_fi):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    instance = get_contractor_pt_manager_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}
    assert ContractorProjectTerritoryManager.objects.filter(id=instance.id).exists()
    assert ContractorProjectTerritoryManager.objects.existing().filter(id=instance.id).exists()


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
    assert ContractorProjectTerritoryManager.objects.filter(id=instance.id).exists()
    assert ContractorProjectTerritoryManager.objects.existing().filter(id=instance.id).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__different_company_user__fail(api_client, monkeypatch, get_contractor_pt_manager_fi, r_cu):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    instance = get_contractor_pt_manager_fi()
    assert __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)


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
@pytest.mark.parametrize("has_object_policy", [True, False])
def test__not_ta__cu__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_contractor_pt_manager_fi,
    has_object_policy,
    is_user,
    field,
    err_text,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    policy_companies = [r_cu.company.id] if has_object_policy else []
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: policy_companies)
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


def test__model_is_fake_delete_allow_create_new_model(api_client, get_contractor_pt_manager_fi: Callable):
    instance = get_contractor_pt_manager_fi()
    fields = {f: getattr(instance, f) for f in ["project_territory", "company_user"]}
    instance.is_deleted = True
    instance.save()
    assert ContractorProjectTerritoryManager.objects.filter(**fields, is_deleted=True).count() == 1
    assert get_contractor_pt_manager_fi(**fields)
    assert ContractorProjectTerritoryManager.objects.existing().filter(**fields).count() == 1
