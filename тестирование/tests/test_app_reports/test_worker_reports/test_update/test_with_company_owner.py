from random import randrange

import pytest
import requests
from django.utils.crypto import get_random_string
from rest_framework.exceptions import ValidationError

from billing.models import WorkerReportsTransaction
from tests.mocked_instances import MockResponse
from ma_saas.constants.report import FINAL_WORKER_REPORT_STATUSES_VALUES, WorkerReportStatus
from reports.models.worker_report import WorkerReport
from clients.billing.interfaces.worker import WorkerBilling
from reports.validators.worker_report_serializer import (
    FOLLOW_WORKER_REPORT_STATUS_CHANGE_SEQUENCE,
    NOT_ALLOWED_UPDATE_REWARD_IF_STATUS_NOT_LOADED,
)
from tests.test_app_reports.test_worker_reports.test_update.test_common import __get_response


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
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
def test__change_status__success(
    api_client, mock_policies_false, r_cu, get_worker_report_fi, current_status, target_status
):
    instance = get_worker_report_fi(company=r_cu.company, status=current_status.value)
    response = __get_response(api_client, instance.id, {"status": target_status.value}, r_cu.user)
    assert response.data
    assert response.data["id"] == instance.id
    updated_instance = WorkerReport.objects.get(id=instance.id)
    assert response.data["status"] == updated_instance.status == target_status.value


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__change_status_and_reward__success(api_client, mock_policies_false, r_cu, get_worker_report_fi):
    instance = get_worker_report_fi(
        company=r_cu.company,
        status=WorkerReportStatus.LOADED.value,
    )
    new_reward = randrange(100)
    data = {"reward": new_reward}
    response = __get_response(api_client, instance.id, data, r_cu.user)
    updated_instance = WorkerReport.objects.get(id=instance.id)
    assert response.data.pop("reward") == updated_instance.reward == new_reward


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accept_and_change_reward__success(
    api_client, monkeypatch, mock_policies_false, r_cu, get_worker_report_fi
):
    monkeypatch.setattr(WorkerBilling, "make_u1_transaction", lambda *a, **kw: MockResponse(id=123))
    monkeypatch.setattr(requests, "request", lambda *a, **kw: MockResponse(data={"id": 123}))

    instance = get_worker_report_fi(company=r_cu.company, status=WorkerReportStatus.LOADED.value)
    assert not WorkerReportsTransaction.objects.filter(worker_report=instance).exists()
    assert not instance.is_paid
    target_status = WorkerReportStatus.ACCEPTED.value
    assert instance.status != target_status
    response = __get_response(api_client, instance.id, {"status": target_status}, r_cu.user)
    updated_instance = WorkerReport.objects.get(id=instance.id)
    assert response.data.pop("status") == updated_instance.status == target_status


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__update_comment__success(api_client, mock_policies_false, r_cu, get_worker_report_fi):
    instance = get_worker_report_fi(company=r_cu.company, status=WorkerReportStatus.LOADED.value)
    assert not instance.comment
    comment = get_random_string()
    response = __get_response(api_client, instance.id, {"comment": comment}, r_cu.user)
    updated_instance = WorkerReport.objects.get(id=instance.id)
    assert response.data.pop("comment") == updated_instance.comment == comment


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
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
def test__change_statuses_invalid_sequences__fail(
    api_client, mock_policies_false, r_cu, get_worker_report_fi, current_status, target_status
):
    instance = get_worker_report_fi(company=r_cu.company, status=current_status.value)
    data = {"status": target_status.value}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    assert response.data == [FOLLOW_WORKER_REPORT_STATUS_CHANGE_SEQUENCE]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("report_status", FINAL_WORKER_REPORT_STATUSES_VALUES)
def test__change_reward_if_status_final__fail(
    api_client, mock_policies_false, r_cu, get_worker_report_fi, report_status
):
    instance = get_worker_report_fi(company=r_cu.company, status=report_status, reward=randrange(100))
    new_reward = instance.reward + 1
    data = {"reward": new_reward}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    assert response.data == {"non_field_errors": [NOT_ALLOWED_UPDATE_REWARD_IF_STATUS_NOT_LOADED]}
