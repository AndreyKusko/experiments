import functools

import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from tests.utils import request_response_list
from accounts.models.users import (
    USER_IS_BLOCKED,
    USER_IS_DELETED,
    USER_EMAIL_NOT_VERIFIED,
    USER_PHONE_NOT_VERIFIED,
    NOT_TA_REQUESTING_USER_REASON,
)
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from ma_saas.constants.system import Callable
from ma_saas.constants.company import CUR, ROLES, NOT_WORKER_ROLES, NOT_ACCEPT_CUS_VALUES
from clients.policies.interface import Policies
from companies.models.company_user import CompanyUser

User = get_user_model()


__get_response = functools.partial(request_response_list, path="/api/v1/territories/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


def test__user_without_companies__empty_response(api_client, user_fi: User):
    response = __get_response(api_client, status_codes=status_code.HTTP_200_OK, user=user_fi)
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__blocked_user__fail(api_client, get_territory_fi: Callable, r_cu: CompanyUser):
    get_territory_fi(company=r_cu.company)
    r_cu.user.is_blocked = True
    r_cu.user.save()
    response = __get_response(api_client, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data["detail"] == USER_IS_BLOCKED


@pytest.mark.parametrize("role", NOT_WORKER_ROLES)
def test__not_verified_management_user__fail(api_client, get_territory_fi: Callable, get_cu_fi, role):
    r_cu = get_cu_fi(role=role)
    get_territory_fi(company=r_cu.company)
    r_cu.user.is_verified_email = False
    r_cu.user.save()

    response = __get_response(api_client, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_REQUESTING_USER_REASON.format(reason=USER_EMAIL_NOT_VERIFIED)}


def test__not_verified_worker_user__fail(api_client, get_territory_fi: Callable, get_cu_fi):
    r_cu = get_cu_fi(role=CUR.WORKER)
    get_territory_fi(company=r_cu.company)

    r_cu.user.is_verified_phone = False
    r_cu.user.save()

    response = __get_response(api_client, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_REQUESTING_USER_REASON.format(reason=USER_PHONE_NOT_VERIFIED)}


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("qty", (1, 3))
def test__accepted_related_user__success(api_client, get_territory_fi, get_cu_fi, role, qty: int):
    company_user = get_cu_fi(role=role)
    [get_territory_fi(company=company_user.company) for _ in range(qty)]
    response = __get_response(api_client, user=company_user.user)
    assert len(response.data) == qty


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", NOT_ACCEPT_CUS_VALUES)
def test__not_accepted_related_user__empty_response(api_client, get_territory_fi, get_cu_fi, role, status):
    company_user = get_cu_fi(role=role, status=status)
    response = __get_response(api_client, user=company_user.user)
    assert not response.data


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
    api_client, monkeypatch, r_cu, get_territory_fi, has_object_policy, is_user, field, err_text
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()
    else:
        setattr(r_cu, field, True)
        r_cu.save()
    get_territory_fi(company=r_cu.company)
    response = __get_response(api_client, r_cu.user, status_codes=PermissionDenied)
    assert response.data == err_text


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__not_email_verified__fail(api_client, r_cu: CompanyUser, get_territory_fi: Callable):
    get_territory_fi(company=r_cu.company)
    r_cu.user.is_verified_email = False
    r_cu.user.save()
    response = __get_response(api_client, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data["detail"] == NOT_TA_REQUESTING_USER_REASON.format(reason=USER_EMAIL_NOT_VERIFIED)


def test__not_phone_verified__fail(api_client, get_cu_worker_fi, get_territory_fi: Callable):
    r_cu = get_cu_worker_fi()
    get_territory_fi(company=r_cu.company)
    r_cu.user.is_verified_phone = False
    r_cu.user.save()
    response = __get_response(api_client, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_REQUESTING_USER_REASON.format(reason=USER_PHONE_NOT_VERIFIED)}
