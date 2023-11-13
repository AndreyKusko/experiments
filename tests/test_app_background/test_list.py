import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.status import HTTP_200_OK
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from tests.utils import request_response_list
from accounts.models import USER_IS_BLOCKED, USER_IS_DELETED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from ma_saas.constants.company import NOT_ACCEPT_CUS
from clients.policies.interface import Policies
from companies.models.company_user import CompanyUser

User = get_user_model()

__get_response = functools.partial(request_response_list, path="/api/v1/background-tasks/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, get_background_task_fi, r_cu):
    instance = get_background_task_fi(company=r_cu.company)
    response = __get_response(api_client, user=r_cu.user)
    assert response.data[0]["id"] == instance.id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__fail(api_client, monkeypatch, get_cu_owner_fi, get_background_task_fi, status):
    r_cu = get_cu_owner_fi(status=status)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    get_background_task_fi(company_user=r_cu)
    response = __get_response(api_client, user=r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager__with_policy__success(api_client, monkeypatch, get_background_task_fi, r_cu):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [instance.company.id])

    instance = get_background_task_fi(company=r_cu.company)
    response = __get_response(api_client, user=r_cu.user)
    assert response.data[0]["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager__without_policy__success(
    api_client, mock_policies_false, get_background_task_fi, r_cu
):
    instance = get_background_task_fi(company=r_cu.company)
    response = __get_response(api_client, user=r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_manager__with_policy__fail(
    api_client, monkeypatch, get_background_task_fi, get_cu_manager_fi, status
):
    r_cu = get_cu_manager_fi(status=status)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [instance.company.id])
    instance = get_background_task_fi(company=r_cu.company)
    response = __get_response(api_client, user=r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__different_company_user__empty_response(api_client, monkeypatch, get_background_task_fi, r_cu):
    instance = get_background_task_fi()

    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [instance.company.id])

    response = __get_response(api_client, user=r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("is_user", "field", "err_text"),
    (
        (True, "is_blocked", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_BLOCKED)),
        (True, "is_deleted", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_DELETED)),
        (False, "is_deleted", REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY),
    ),
)
def test__not_ta__cu__fail(api_client, monkeypatch, r_cu, get_background_task_fi, is_user, field, err_text):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    get_background_task_fi(company=r_cu.company)

    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()
    else:
        setattr(r_cu, field, True)
        r_cu.save()
    response = __get_response(api_client, r_cu.user, status_codes={PermissionDenied, HTTP_200_OK})
    assert response.data == {"detail": err_text} or response.data == []
