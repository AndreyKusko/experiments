import functools

import pytest
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework.exceptions import NotFound, ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import get_random_email, request_response_update
from ma_saas.settings import SERVER_ENVIRONMENT
from companies.models.company import UNIQ_CONSTRAINT_SUBDOMAIN_ERR, Company
from clients.dnsmadeeasy.views import RequestDmsEasy
from ma_saas.constants.company import CUS, ROLES, NOT_OWNER_ROLES, NOT_ACCEPT_OR_INVITE_CUS_VALUES
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_REASON, CUS_MUST_BE_ACCEPT_OR_INVITE

User = get_user_model()


__get_response = functools.partial(request_response_update, path="/api/v1/companies/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("company_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, {}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__company_owner__without_policy__success(api_client, mock_policies_false, r_cu):
    new_title = get_random_string()
    response = __get_response(api_client, r_cu.company.id, user=r_cu.user, data={"title": new_title})
    assert response.data["title"] == new_title
    assert response.data["id"] == r_cu.company.id


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_company_owner__without_policy__fail(api_client, mock_policies_false, get_cu_fi, role):

    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)
    data = {"title": get_random_string()}
    response = __get_response(api_client, r_cu.company.id, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PermissionDenied.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__another_company__user__with_policy__fail(monkeypatch, api_client, get_company_fi, r_cu):
    instance = get_company_fi()

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [instance.id])
    data = {"title": get_random_string()}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_company_owner__but__with_policy__success(monkeypatch, api_client, get_cu_fi, role):
    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    new_title = get_random_string()
    response = __get_response(api_client, r_cu.company.id, user=r_cu.user, data={"title": new_title})
    assert response.data["title"] == new_title


@pytest.mark.parametrize("status", NOT_ACCEPT_OR_INVITE_CUS_VALUES)
def test__not_accepted_or_invited_cu__fail(monkeypatch, api_client, get_cu_owner_fi, status):
    """Тестируеттся и компания-слиент и компания-подрядчик."""

    r_cu = get_cu_owner_fi(status=status)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    data = {"title": get_random_string()}
    response = __get_response(api_client, r_cu.company.id, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_REASON.format(reason=CUS_MUST_BE_ACCEPT_OR_INVITE)}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(api_client, monkeypatch, r_cu):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])

    monkeypatch.setattr(RequestDmsEasy, "create_subdomain", lambda *a, **kw: None)
    monkeypatch.setattr(RequestDmsEasy, "delete_subdomain_by_name", lambda *a, **kw: None)

    assert r_cu.company.title
    assert not r_cu.company.support_email
    assert r_cu.company.subdomain

    # проверить переход из пустого субдомена и почты в заполненное
    new_title_1 = get_random_string(length=4)
    new_subdomain_1 = new_title_1.lower()
    new_support_email_1 = get_random_email()
    assert r_cu.company.title != new_title_1 and r_cu.company.title and new_support_email_1
    data_1 = {"title": new_title_1, "subdomain": new_title_1, "support_email": new_support_email_1}
    response = __get_response(api_client, r_cu.company.id, data_1, user=r_cu.user)

    assert len(response.data) == 8
    assert response.data.pop("id") == r_cu.company.id
    assert response.data.pop("title") == new_title_1 and new_title_1 != r_cu.company.title
    assert response.data.pop("subdomain") == new_subdomain_1 + f"-{SERVER_ENVIRONMENT}"
    assert response.data.pop("support_email") == new_support_email_1
    assert response.data.pop("transactions_list_scheme") == r_cu.company.transactions_list_scheme
    assert str(response.data.pop("logo")) == r_cu.company.logo
    assert response.data.pop("created_at")
    assert response.data.pop("updated_at")
    assert not response.data

    # проверить переход из заполненного субдомена
    # и почты в другие заполненные
    new_title_2 = get_random_string(length=4)
    new_subdomain_2 = new_title_2.lower()
    new_support_email_2 = get_random_email()
    assert new_title_1 != new_title_2
    assert new_subdomain_1 != new_subdomain_2
    assert new_support_email_1 != new_support_email_2

    data_2 = {"title": new_title_2, "subdomain": new_subdomain_2, "support_email": new_support_email_2}
    response = __get_response(api_client, r_cu.company.id, data=data_2, user=r_cu.user)
    assert len(response.data) == 8
    assert response.data.pop("id") == r_cu.company.id
    assert response.data.pop("title") == new_title_2 and new_title_2 != r_cu.company.title
    assert response.data.pop("subdomain") == new_subdomain_2 + f"-{SERVER_ENVIRONMENT}"
    assert response.data.pop("support_email") == new_support_email_2
    assert response.data.pop("transactions_list_scheme") == r_cu.company.transactions_list_scheme
    assert str(response.data.pop("logo")) == r_cu.company.logo
    assert response.data.pop("created_at")
    assert response.data.pop("updated_at")
    assert not response.data

    # проверить переход из заполненнойпочты в пустую
    new_support_email_3 = ""
    assert new_support_email_2 != new_support_email_3
    data_3 = {"support_email": new_support_email_3}
    response = __get_response(api_client, r_cu.company.id, user=r_cu.user, data=data_3)
    assert len(response.data) == 8
    assert response.data.pop("id") == r_cu.company.id
    assert response.data.pop("title") == new_title_2 and new_title_2 != r_cu.company.title
    assert response.data.pop("subdomain") == new_subdomain_2 + f"-{SERVER_ENVIRONMENT}"
    assert response.data.pop("support_email") == new_support_email_3
    assert response.data.pop("transactions_list_scheme") == r_cu.company.transactions_list_scheme
    assert str(response.data.pop("logo")) == r_cu.company.logo
    assert response.data.pop("created_at")
    assert response.data.pop("updated_at")
    assert not response.data


@pytest.mark.xfail
@pytest.mark.parametrize("role", ROLES)
def test__invited_cu__fail(monkeypatch, api_client, get_cu_fi, role):
    """Тестируеттся и компания-клиент и компания-подрядчик."""

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    r_cu = get_cu_fi(status=CUS.INVITE.value, role=role)
    data = {"title": get_random_string()}
    response = __get_response(api_client, r_cu.company.id, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PermissionDenied.default_detail}


def test__foreign_company_cu__fail(api_client, monkeypatch, get_cu_owner_fi, company_fi: Company):
    r_cu = get_cu_owner_fi(status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [company_fi.id])
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    data = {"title": get_random_string()}
    response = __get_response(api_client, company_fi.id, data=data, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


def test__foreign_company_cu__with_policy__fail(
    monkeypatch, api_client, get_cu_owner_fi, company_fi: Company
):
    r_cu = get_cu_owner_fi(status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [company_fi.id])
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    data = {"title": get_random_string()}
    response = __get_response(api_client, company_fi.id, user=r_cu.user, data=data, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__duplicate_subdomain__without_policy__success(api_client, monkeypatch, r_cu, get_company_fi):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(RequestDmsEasy, "create_subdomain", lambda *a, **kw: None)
    monkeypatch.setattr(RequestDmsEasy, "delete_subdomain_by_name", lambda *a, **kw: None)
    subdomain = get_random_string(length=3)
    get_company_fi(subdomain=subdomain)
    data = {"subdomain": subdomain}
    response = __get_response(api_client, r_cu.company.id, data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == [UNIQ_CONSTRAINT_SUBDOMAIN_ERR]
