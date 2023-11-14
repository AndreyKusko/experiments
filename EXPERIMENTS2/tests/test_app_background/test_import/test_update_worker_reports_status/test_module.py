from typing import Callable
from unittest import mock

import pytest

from background.models import BackgroundTask
from ma_saas.constants.report import PAID_STATUSES
from ma_saas.constants.report import WorkerReportStatus as WRS
from ma_saas.constants.company import NOT_OWNER_ROLES, CompanyUserStatus
from reports.models.worker_report import WorkerReport
from companies.models.company_user import COMPANY_OWNER_ONLY_ALLOWED, CompanyUser
from clients.billing.interfaces.worker import WorkerBilling
from ma_saas.constants.background_task import (
    BackgroundTaskType,
    BackgroundTaskStatus,
    BackgroundTaskParamsKeys,
)
from background.tasks.workers_reports_status_update import (
    RCU_ANOTHER_COMPANY_FAIL,
    REQUIRED_WORKER_REPORT_STATUS,
    UPDATE_WORKER_REPORT_STATUS_FAIL,
    NOT_ACCEPT_WORKER_REPORT_STATUS_FAIL,
    update_workers_reports_status_task,
)


def throw_exception(*args, **kwargs):
    raise Exception("Unacceptable")


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(
    monkeypatch, r_cu: CompanyUser, get_background_task_fi: Callable, get_worker_report_fi: Callable
):
    monkeypatch.setattr(WorkerBilling, "make_u1_transaction", lambda *args, **kwargs: None)

    target_worker_report = get_worker_report_fi(company=r_cu.company, status=WRS.LOADED.value)

    assert target_worker_report.status != WRS.ACCEPTED.value
    # assert not target_worker_report.is_paid
    instance = get_background_task_fi(
        company_user=r_cu,
        params={"ids": [target_worker_report.id], BackgroundTaskParamsKeys.STATUS: WRS.ACCEPTED.value},
        model_name=WorkerReport._meta.concrete_model.__name__,
        task_type=BackgroundTaskType.UPDATE_WORKER_REPORT_STATUS.value,
    )

    update_workers_reports_status_task.run(background_task_id=instance.id)
    updated_instance = BackgroundTask.objects.get(id=instance.id)

    zero_len_fields = [
        updated_instance.input_files,
        updated_instance.result,
        updated_instance.failures,
        updated_instance.output_files,
    ]
    assert not any(zero_len_fields)
    assert updated_instance.status == BackgroundTaskStatus.COMPLETED.value

    updated_worker_report = WorkerReport.objects.get(id=target_worker_report.id)
    assert updated_worker_report.status == WRS.ACCEPTED.value
    # assert updated_worker_report.is_paid


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("report_status", [status.value for status in WRS if status != WRS.LOADED.value])
def test__change_status_from_not_LOADED__fail(
    monkeypatch,
    r_cu: CompanyUser,
    get_background_task_fi: Callable,
    get_worker_report_fi: Callable,
    report_status,
):
    monkeypatch.setattr(WorkerBilling, "make_u1_transaction", lambda: throw_exception())

    target_worker_report = get_worker_report_fi(company=r_cu.company, status=report_status)
    assert target_worker_report.status == report_status
    # assert not target_worker_report.is_paid
    instance = get_background_task_fi(
        company_user=r_cu,
        params={"ids": [target_worker_report.id], BackgroundTaskParamsKeys.STATUS: WRS.ACCEPTED.value},
        model_name=WorkerReport._meta.concrete_model.__name__,
        task_type=BackgroundTaskType.UPDATE_WORKER_REPORT_STATUS.value,
    )

    update_workers_reports_status_task.run(background_task_id=instance.id)

    updated_instance = BackgroundTask.objects.get(id=instance.id)
    zero_len_fields = [updated_instance.input_files, updated_instance.output_files, updated_instance.result]
    assert not any(zero_len_fields)
    assert updated_instance.status == BackgroundTaskStatus.FAILED.value
    assert updated_instance.failures == [
        UPDATE_WORKER_REPORT_STATUS_FAIL.format(
            worker_report_id=target_worker_report.id, reason=REQUIRED_WORKER_REPORT_STATUS
        )
    ]

    updated_worker_report = WorkerReport.objects.get(id=target_worker_report.id)
    assert updated_worker_report.status == report_status


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__if_paid__not_transaction__but_status__updating(
    monkeypatch, r_cu: CompanyUser, get_background_task_fi: Callable, get_worker_report_fi: Callable
):
    monkeypatch.setattr(WorkerBilling, "make_u1_transaction", lambda: throw_exception())

    target_worker_report = get_worker_report_fi(
        company=r_cu.company, status=WRS.LOADED.value, payment_status__in=PAID_STATUSES
    )
    assert target_worker_report.status == WRS.LOADED.value
    # assert target_worker_report.is_paid
    instance = get_background_task_fi(
        company_user=r_cu,
        params={"ids": [target_worker_report.id], BackgroundTaskParamsKeys.STATUS: WRS.ACCEPTED.value},
        model_name=WorkerReport._meta.concrete_model.__name__,
        task_type=BackgroundTaskType.UPDATE_WORKER_REPORT_STATUS.value,
    )

    update_workers_reports_status_task.run(background_task_id=instance.id)

    updated_instance = BackgroundTask.objects.get(id=instance.id)
    zero_len_fields = [
        updated_instance.input_files,
        updated_instance.output_files,
        updated_instance.result,
        updated_instance.failures,
    ]
    assert not any(zero_len_fields)
    updated_worker_report = WorkerReport.objects.get(id=target_worker_report.id)
    assert updated_worker_report.status == WRS.ACCEPTED.value
    # assert updated_worker_report.is_paid


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("target_status", [status for status in WRS if status != WRS.ACCEPTED.value])
def test__not_ACCEPT_new_status__fail(
    monkeypatch,
    r_cu: CompanyUser,
    get_background_task_fi: Callable,
    get_worker_report_fi: Callable,
    target_status,
):
    monkeypatch.setattr(WorkerBilling, "make_u1_transaction", lambda: throw_exception())
    target_worker_report = get_worker_report_fi(
        company=r_cu.company, status=WRS.LOADED.value, payment_status__in=PAID_STATUSES
    )
    assert target_worker_report.status == WRS.LOADED.value
    # assert target_worker_report.is_paid
    instance = get_background_task_fi(
        company_user=r_cu,
        params={"ids": [target_worker_report.id], BackgroundTaskParamsKeys.STATUS: target_status.value},
        model_name=WorkerReport._meta.concrete_model.__name__,
        task_type=BackgroundTaskType.UPDATE_WORKER_REPORT_STATUS.value,
    )
    update_workers_reports_status_task.run(background_task_id=instance.id)
    updated_instance = BackgroundTask.objects.get(id=instance.id)
    zero_len_fields = [updated_instance.input_files, updated_instance.output_files, updated_instance.result]
    assert not any(zero_len_fields)
    assert updated_instance.failures == [
        UPDATE_WORKER_REPORT_STATUS_FAIL.format(
            worker_report_id=target_worker_report.id, reason=NOT_ACCEPT_WORKER_REPORT_STATUS_FAIL
        )
    ]
    updated_worker_report = WorkerReport.objects.get(id=target_worker_report.id)
    assert updated_worker_report.status == WRS.LOADED.value


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__another_company_owner__fail(
    monkeypatch,
    r_cu: CompanyUser,
    get_background_task_fi: Callable,
    get_worker_report_fi: Callable,
    get_company_fi,
):
    monkeypatch.setattr(WorkerBilling, "make_u1_transaction", lambda: throw_exception())
    company = get_company_fi()
    target_worker_report = get_worker_report_fi(company=company, status=WRS.LOADED.value)
    assert target_worker_report.status == WRS.LOADED.value
    # assert not target_worker_report.is_paid
    instance = get_background_task_fi(
        company_user=r_cu,
        params={"ids": [target_worker_report.id], BackgroundTaskParamsKeys.STATUS: WRS.ACCEPTED.value},
        model_name=WorkerReport._meta.concrete_model.__name__,
        task_type=BackgroundTaskType.UPDATE_WORKER_REPORT_STATUS.value,
    )

    update_workers_reports_status_task.run(background_task_id=instance.id)

    updated_instance = BackgroundTask.objects.get(id=instance.id)
    zero_len_fields = [updated_instance.input_files, updated_instance.output_files, updated_instance.result]
    assert not any(zero_len_fields)
    assert updated_instance.failures == [
        UPDATE_WORKER_REPORT_STATUS_FAIL.format(
            worker_report_id=target_worker_report.id, reason=RCU_ANOTHER_COMPANY_FAIL
        )
    ]

    updated_worker_report = WorkerReport.objects.get(id=target_worker_report.id)
    assert updated_worker_report.status == WRS.LOADED.value
    # assert not updated_worker_report.is_paid


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner_and_not_related__fail(
    monkeypatch,
    get_cu_fi,
    get_background_task_fi: Callable,
    get_worker_report_fi: Callable,
    role,
):
    monkeypatch.setattr(WorkerBilling, "make_u1_transaction", lambda: throw_exception())

    r_cu = get_cu_fi(role=role, status=CompanyUserStatus.ACCEPT.value)
    target_worker_report = get_worker_report_fi(company=r_cu.company, status=WRS.LOADED.value)
    assert target_worker_report.status != WRS.ACCEPTED.value
    # assert not target_worker_report.is_paid
    instance = get_background_task_fi(
        company_user=r_cu,
        params={"ids": [target_worker_report.id], BackgroundTaskParamsKeys.STATUS: WRS.ACCEPTED.value},
        model_name=WorkerReport._meta.concrete_model.__name__,
        task_type=BackgroundTaskType.UPDATE_WORKER_REPORT_STATUS.value,
    )
    update_workers_reports_status_task.run(background_task_id=instance.id)
    updated_instance = BackgroundTask.objects.get(id=instance.id)
    zero_len_fields = [updated_instance.input_files, updated_instance.output_files, updated_instance.result]
    assert not any(zero_len_fields)
    assert updated_instance.failures == [
        UPDATE_WORKER_REPORT_STATUS_FAIL.format(
            worker_report_id=target_worker_report.id, reason=COMPANY_OWNER_ONLY_ALLOWED
        )
    ]
    updated_worker_report = WorkerReport.objects.get(id=target_worker_report.id)
    assert updated_worker_report.status == WRS.LOADED.value
