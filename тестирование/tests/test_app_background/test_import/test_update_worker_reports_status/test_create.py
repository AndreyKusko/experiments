import json
import functools

import pytest
from django.forms import model_to_dict
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, PermissionDenied

from tests.utils import request_response_create
from accounts.models import USER_IS_BLOCKED, NOT_TA_USER_REASON, NOT_TA_R_U__DELETED, USER_EMAIL_NOT_VERIFIED
from background.models import BackgroundTask
from ma_saas.constants.report import WorkerReportStatus as WRS
from ma_saas.constants.system import Callable
from ma_saas.constants.company import CUR, CUS, NOT_OWNER_ROLES, NOT_ACCEPT_CUS_VALUES
from reports.models.worker_report import WorkerReport
from companies.models.company_user import (
    NOT_TA_RCU_REASON,
    NOT_TA_RCU_MUST_BE_ACCEPT,
    COMPANY_OWNER_ONLY_ALLOWED,
    CompanyUser,
)
from clients.billing.interfaces.worker import WorkerBilling
from ma_saas.constants.background_task import BackgroundTaskType, BackgroundTaskStatus
from companies.permissions.company_user import REQUESTING_USER_NOT_BELONG_TO_COMPANY
from background.tasks.workers_reports_status_update import update_workers_reports_status_task

User = get_user_model()

__get_response = functools.partial(request_response_create, path="/api/v1/update-workers-reports-status/")


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(
    api_client,
    mock_policies_false,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_worker_report_fi,
):
    monkeypatch.setattr(WorkerBilling, "make_u1_transaction", lambda *args, **kwargs: None)
    monkeypatch.setattr(update_workers_reports_status_task, "delay", lambda *args, **kwargs: None)

    worker_report = get_worker_report_fi(company=r_cu.company, status=WRS.LOADED.value)
    params = {"status": WRS.ACCEPTED.value, "ids": [worker_report.id]}
    data = new_background_task_data(
        company=r_cu.company, params=params, model_name=WorkerReport._meta.concrete_model.__name__
    )
    data.pop("company_user")
    data.pop("status")
    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instance = BackgroundTask.objects.get(id=response.data["id"])
    created_instance_dict = model_to_dict(created_instance)

    created_instance_params = created_instance_dict.pop("params")
    data_params = json.loads(data.pop("params"))
    response_data_params = response.data.pop("params")
    assert created_instance_params["status"] == data_params["status"] == response_data_params["status"]
    assert created_instance_params["ids"] == data_params["ids"] == response_data_params["ids"]

    data["input_files"] = json.loads(data.pop("input_files"))
    data["result"] = json.loads(data.pop("result"))
    data["output_files"] = json.loads(data.pop("output_files"))
    data["failures"] = json.loads(data.pop("failures"))
    assert created_instance.model_name == WorkerReport._meta.concrete_model.__name__
    data.pop("task_type")
    assert created_instance.task_type == BackgroundTaskType.UPDATE_WORKER_REPORT_STATUS.value
    for key, value in data.items():
        assert created_instance_dict[key] == response.data[key] == value


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__another_cu__not_saving(
    api_client,
    monkeypatch,
    r_cu,
    get_cu_fi,
    new_background_task_data,
    get_worker_report_fi,
):
    monkeypatch.setattr(WorkerBilling, "make_u1_transaction", lambda *args, **kwargs: None)
    monkeypatch.setattr(update_workers_reports_status_task, "delay", lambda *args, **kwargs: None)
    company = r_cu.company
    another_cu = get_cu_fi(company=company, role=CUR.OWNER, status=CUS.ACCEPT.value)
    worker_report = get_worker_report_fi(company=company, status=WRS.LOADED.value)
    data = new_background_task_data(
        company=company,
        company_user=another_cu,
        params={"status": WRS.ACCEPTED.value, "ids": [worker_report.id]},
    )
    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instance = BackgroundTask.objects.get(id=response.data["id"])
    assert created_instance.company_user.id == response.data["company_user"] == r_cu.id


@pytest.mark.parametrize("bts_status", BackgroundTaskStatus.values)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__status__not_saving(
    api_client,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_worker_report_fi,
    bts_status,
):
    monkeypatch.setattr(WorkerBilling, "make_u1_transaction", lambda *args, **kwargs: None)
    monkeypatch.setattr(update_workers_reports_status_task, "delay", lambda *args, **kwargs: None)

    worker_report = get_worker_report_fi(company=r_cu.company, status=WRS.LOADED.value)
    data = new_background_task_data(
        status=bts_status,
        company=r_cu.company,
        company_user=r_cu,
        params={"status": WRS.ACCEPTED.value, "ids": [worker_report.id]},
    )
    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instance = BackgroundTask.objects.get(id=response.data["id"])
    assert created_instance.status == response.data["status"] == BackgroundTaskStatus.PENDING.value


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_company_owner__fail(
    api_client,
    get_cu_fi,
    new_background_task_data,
    get_worker_report_fi,
    role,
):
    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)
    company = r_cu.company
    worker_report = get_worker_report_fi(company=company, status=WRS.LOADED.value)
    data = new_background_task_data(
        company_user=r_cu,
        params={"status": WRS.ACCEPTED.value, "ids": [worker_report.id]},
    )
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data["detail"] == COMPANY_OWNER_ONLY_ALLOWED


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS_VALUES)
def test__not_accepted_owner__fail(
    api_client, get_cu_fi, new_background_task_data, get_worker_report_fi, status
):
    r_cu = get_cu_fi(status=status, role=CUR.OWNER)
    company = r_cu.company
    worker_report = get_worker_report_fi(company=company, status=WRS.LOADED.value)
    params = {"status": WRS.ACCEPTED.value, "ids": [worker_report.id]}
    data = new_background_task_data(company_user=r_cu, params=params)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_cu__fail(api_client, r_cu, new_background_task_data, get_worker_report_fi):
    worker_report = get_worker_report_fi(company=r_cu.company, status=WRS.LOADED.value)
    r_cu.is_deleted = True
    r_cu.save()
    params = {"status": WRS.ACCEPTED.value, "ids": [worker_report.id]}
    data = new_background_task_data(company_user=r_cu, params=params)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_COMPANY}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("user_attr", "value", "err_msg"),
    (
        (
            "is_deleted",
            True,
            NOT_TA_RCU_REASON.format(reason=NOT_TA_R_U__DELETED),
        ),
        (
            "is_blocked",
            True,
            NOT_TA_RCU_REASON.format(reason=NOT_TA_USER_REASON.format(reason=USER_IS_BLOCKED)),
        ),
        (
            "is_verified_email",
            False,
            NOT_TA_RCU_REASON.format(reason=NOT_TA_USER_REASON.format(reason=USER_EMAIL_NOT_VERIFIED)),
        ),
    ),
)
def test__not_active_user__fail(
    api_client,
    r_cu,
    new_background_task_data,
    get_worker_report_fi,
    user_attr: str,
    value: bool,
    err_msg: str,
):
    worker_report = get_worker_report_fi(company=r_cu.company, status=WRS.LOADED.value)
    setattr(r_cu.user, user_attr, value)
    r_cu.user.save()

    data = new_background_task_data(
        company_user=r_cu, params={"status": WRS.ACCEPTED.value, "ids": [worker_report.id]}
    )
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data["detail"] == err_msg
