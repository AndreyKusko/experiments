import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated, PermissionDenied

from tests.utils import request_response_get
from accounts.models import USER_IS_BLOCKED, NOT_TA_R_U__DELETED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from ma_saas.constants.company import NOT_ACCEPT_CUS
from clients.policies.interface import Policies
from companies.models.company_user import CompanyUser
from ma_saas.constants.background_task import BackgroundTaskType, BackgroundTaskStatus

User = get_user_model()

__get_response = functools.partial(request_response_get, path="/api/v1/background-tasks/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("background_task_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, get_background_task_fi):
    instance = get_background_task_fi(company=r_cu.company)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__with_policy__fail(
    api_client, monkeypatch, get_cu_owner_fi, get_background_task_fi, status
):
    r_cu = get_cu_owner_fi(status=status)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    instance = get_background_task_fi(company=r_cu.company)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager__with_policy__success(api_client, monkeypatch, r_cu, get_background_task_fi):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    instance = get_background_task_fi(company=r_cu.company)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager__without_policy__fail(
    api_client, mock_policies_false, r_cu, get_background_task_fi
):
    instance = get_background_task_fi(company=r_cu.company)
    # response = __get_response(api_client, instance.id, r_cu.user, status_codes=PermissionDenied)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    # assert response.data == {'detail': PermissionDenied.default_detail}
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_manager__with_policy__fail(
    api_client, monkeypatch, get_cu_manager_fi, get_background_task_fi, status
):
    r_cu = get_cu_manager_fi(status=status)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    instance = get_background_task_fi(company=r_cu.company)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user, status_codes=NotFound)
    # assert response.data == {'detail': NOT_TA_RCU_MUST_BE_ACCEPT}
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__different_company_user__fail(api_client, monkeypatch, r_cu, get_background_task_fi):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    instance = get_background_task_fi()
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("is_user", "field", "err_text"),
    (
        (True, "is_blocked", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_BLOCKED)),
        (True, "is_deleted", NOT_TA_R_U__DELETED),
        (False, "is_deleted", REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY),
    ),
)
@pytest.mark.parametrize("is_policy", [True, False])
def test__not_ta__cu__fail(
    api_client, monkeypatch, r_cu, get_background_task_fi, is_policy, is_user, field, err_text
):
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    instance = get_background_task_fi(company_user=r_cu)

    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()
    else:
        setattr(r_cu, field, True)
        r_cu.save()

    response = __get_response(api_client, instance.id, r_cu.user, status_codes={PermissionDenied, NotFound})
    assert response.data == {"detail": err_text} or response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(api_client, mock_policies_false, r_cu, get_background_task_fi):
    instance = get_background_task_fi(company_user=r_cu)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    response_instance = response.data
    print("response_instance =", response_instance)
    assert response_instance.pop("id") == instance.id
    assert response_instance.pop("status") == BackgroundTaskStatus.PENDING.value
    assert response_instance.pop("company") == r_cu.company.id
    assert response_instance.pop("company_user") == r_cu.id
    assert response_instance.pop("model_name") == "WorkerReport"
    assert response_instance.pop("task_type") == BackgroundTaskType.UPDATE_WORKER_REPORT_STATUS.value
    assert response_instance.pop("params") == {}
    assert response_instance.pop("input_files") == []
    assert response_instance.pop("result") == []
    assert response_instance.pop("output_files") == []
    assert response_instance.pop("failures") == []
    assert response_instance.pop("created_at")
    assert response_instance.pop("updated_at")
    assert not response_instance
