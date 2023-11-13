from random import randrange

import pytest
import requests
from django.utils.crypto import get_random_string
from rest_framework.exceptions import ValidationError, PermissionDenied

from billing.models import WorkerReportsTransaction
from tests.mocked_instances import MockResponse
from ma_saas.constants.report import STATUSES_ALLOWING_MANAGEMENT_UPDATE_WORKER_REPORTS, WorkerReportStatus
from ma_saas.constants.system import Callable
from ma_saas.constants.company import CUS, NOT_OWNER_AND_NOT_WORKER_ROLES
from clients.policies.interface import Policies
from reports.models.worker_report import WorkerReport
from clients.billing.interfaces.worker import WorkerBilling
from reports.permissions.worker_report import MANAGEMENT_NOT_ALLOWED_TO_UPDATE_IN_PENDING_STATUS
from reports.validators.worker_report_serializer import (
    FOLLOW_WORKER_REPORT_STATUS_CHANGE_SEQUENCE,
    NOT_ALLOWED_UPDATE_REWARD_IF_STATUS_NOT_LOADED,
)
from tests.test_app_reports.test_worker_reports.test_update.test_common import __get_response


@pytest.mark.parametrize("role", NOT_OWNER_AND_NOT_WORKER_ROLES)
@pytest.mark.parametrize(
    ("current_status", "target_status"),
    (
        (WorkerReportStatus.LOADED, WorkerReportStatus.LOADED),
        (WorkerReportStatus.LOADED, WorkerReportStatus.DECLINED),
        (WorkerReportStatus.DECLINED, WorkerReportStatus.DECLINED),
        (WorkerReportStatus.DECLINED, WorkerReportStatus.ARCHIVED),
        (WorkerReportStatus.ARCHIVED, WorkerReportStatus.ARCHIVED),
        (WorkerReportStatus.ACCEPTED, WorkerReportStatus.ACCEPTED),
    ),
)
def test__change_status___success(
    api_client,
    monkeypatch,
    get_cu_fi,
    get_worker_report_fi: Callable,
    current_status: WorkerReportStatus,
    target_status: WorkerReportStatus,
    role,
):
    monkeypatch.setattr(WorkerBilling, "make_u1_transaction", lambda *args, **kwargs: None)

    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_worker_report_fi(company=r_cu.company, status=current_status)

    response = __get_response(api_client, instance.id, {"status": target_status}, r_cu.user)
    updated_instance = WorkerReport.objects.get(id=instance.id)
    assert response.data
    assert response.data["id"] == instance.id
    assert response.data["status"] == target_status == updated_instance.status


@pytest.mark.parametrize("role", NOT_OWNER_AND_NOT_WORKER_ROLES)
def test__change_reward_on_loaded_status__success(
    api_client, monkeypatch, get_worker_report_fi, get_cu_fi, role
):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_worker_report_fi(
        company=r_cu.company, status=WorkerReportStatus.LOADED.value, reward=randrange(100)
    )
    new_reward = instance.reward + 2
    data = {"status": WorkerReportStatus.LOADED.value, "reward": new_reward}
    response = __get_response(api_client, instance.id, data, r_cu.user)

    assert response.data
    assert response.data["id"] == instance.id

    updated_instance = WorkerReport.objects.get(id=instance.id)
    assert response.data["reward"] == new_reward == updated_instance.reward != instance.reward


@pytest.mark.parametrize("role", NOT_OWNER_AND_NOT_WORKER_ROLES)
@pytest.mark.parametrize("report_status", STATUSES_ALLOWING_MANAGEMENT_UPDATE_WORKER_REPORTS)
def test__change_comment__success(
    api_client, monkeypatch, get_worker_report_fi, get_cu_fi, role, report_status
):

    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_worker_report_fi(company=r_cu.company, status=report_status)
    assert not instance.comment
    comment = get_random_string()
    response = __get_response(api_client, instance.id, {"comment": comment}, r_cu.user)
    updated_instance = WorkerReport.objects.get(id=instance.id)
    assert response.data.pop("comment") == updated_instance.comment == comment


@pytest.mark.parametrize("role", NOT_OWNER_AND_NOT_WORKER_ROLES)
def test__accept_and_change_reward___success(
    api_client,
    monkeypatch,
    get_worker_report_fi,
    get_cu_fi,
    role,
    get_schedule_time_slot_fi,
    get_reservation_fi,
):
    monkeypatch.setattr(WorkerBilling, "make_u1_transaction", lambda *a, **kw: MockResponse(id=123))
    monkeypatch.setattr(requests, "request", lambda *a, **kw: MockResponse(data={"id": 123}))

    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    schedule_time_slot = get_schedule_time_slot_fi(company=r_cu.company)
    reservation = get_reservation_fi(schedule_time_slot=schedule_time_slot)
    instance = get_worker_report_fi(
        project_territory_worker=reservation.project_territory_worker,
        schedule_time_slot=schedule_time_slot,
        status=WorkerReportStatus.LOADED.value,
    )

    assert not instance.is_paid
    assert not WorkerReportsTransaction.objects.filter(worker_report_id=instance.id).exists()
    target_status = WorkerReportStatus.ACCEPTED.value
    assert instance.status != target_status
    target_status = WorkerReportStatus.ACCEPTED.value
    new_reward = randrange(100)
    data = {"status": target_status, "reward": new_reward}
    response = __get_response(api_client, instance.id, data, r_cu.user)
    updated_instance = WorkerReport.objects.get(id=instance.id)
    assert response.data.pop("reward") == updated_instance.reward == new_reward
    assert response.data.pop("status") == updated_instance.status == target_status


@pytest.mark.parametrize("role", NOT_OWNER_AND_NOT_WORKER_ROLES)
@pytest.mark.parametrize(
    ("current_status", "target_status"),
    (
        (WorkerReportStatus.DECLINED, WorkerReportStatus.ACCEPTED),
        (WorkerReportStatus.ACCEPTED, WorkerReportStatus.DECLINED),
        (WorkerReportStatus.ARCHIVED, WorkerReportStatus.DECLINED),
        (WorkerReportStatus.ARCHIVED, WorkerReportStatus.ACCEPTED),
        (WorkerReportStatus.ARCHIVED, WorkerReportStatus.LOADED),
    ),
)
def test__change_statues_invalid_sequences__fail(
    api_client,
    monkeypatch,
    get_cu_fi,
    get_worker_report_fi: Callable,
    current_status,
    target_status,
    role,
):

    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_worker_report_fi(company=r_cu.company, status=current_status.value)
    data = {"status": target_status.value}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    assert response.data[0] == FOLLOW_WORKER_REPORT_STATUS_CHANGE_SEQUENCE


@pytest.mark.parametrize("role", NOT_OWNER_AND_NOT_WORKER_ROLES)
def test__change_if_status_loading__fail(api_client, monkeypatch, get_cu_fi, get_worker_report_fi, role):

    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_worker_report_fi(company=r_cu.company, status=WorkerReportStatus.PENDING.value)
    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=PermissionDenied)
    assert response.data["detail"] == MANAGEMENT_NOT_ALLOWED_TO_UPDATE_IN_PENDING_STATUS


@pytest.mark.parametrize("role", NOT_OWNER_AND_NOT_WORKER_ROLES)
@pytest.mark.parametrize("report_status", [s for s in WorkerReportStatus if s != WorkerReportStatus.LOADED])
def test__change_reward__if_status_not_loaded__fail(
    api_client, monkeypatch, get_cu_fi, get_worker_report_fi, report_status, role
):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_worker_report_fi(company=r_cu.company, status=report_status, reward=randrange(100))
    data = {"reward": instance.reward + 1}
    status_codes = {PermissionDenied.status_code, ValidationError.status_code}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=status_codes)
    assert (
        response.data == {"detail": NOT_ALLOWED_UPDATE_REWARD_IF_STATUS_NOT_LOADED}
        or response.data == {"detail": MANAGEMENT_NOT_ALLOWED_TO_UPDATE_IN_PENDING_STATUS}
        or response.data == NOT_ALLOWED_UPDATE_REWARD_IF_STATUS_NOT_LOADED
        or response.data == [NOT_ALLOWED_UPDATE_REWARD_IF_STATUS_NOT_LOADED]
        or response.data == {"non_field_errors": [NOT_ALLOWED_UPDATE_REWARD_IF_STATUS_NOT_LOADED]}
    )
