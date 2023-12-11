import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_update, retrieve_response_instance
from pg_logger.models import PgLog
from ma_saas.constants.report import (
    FINAL_NOT_ARCHIVED_WORKER_REPORT_STATUSES_VALUES,
    WorkerReportStatus,
    WorkerReportDisputeStatus,
    WorkerReportPaymentStatus,
)
from ma_saas.constants.system import Callable
from ma_saas.constants.company import CUS, NOT_OWNER_ROLES
from ma_saas.constants.project import NOT_ACTIVE_PROJECT_STATUS
from clients.policies.interface import Policies
from reports.models.worker_report import WorkerReport
from clients.billing.interfaces.worker import WorkerBilling
from reports.permissions.worker_report import PROJECT_STATUS_MUST_BE_ACTIVE
from reports.validators.worker_report_serializer import FOLLOW_WORKER_REPORT_STATUS_CHANGE_SEQUENCE

User = get_user_model()

__get_response = functools.partial(request_response_update, path="/api/v1/worker-reports/")


def test__anonymous_user__fail(api_client, get_worker_report_fi):
    instance = get_worker_report_fi()
    response = __get_response(api_client, instance.id, {}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__updated_by_company_user__data(
    api_client, monkeypatch, r_cu, get_schedule_time_slot_fi, get_reservation_fi, get_worker_report_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_worker_report_fi(company=r_cu.company)
    worker_report_model_name = WorkerReport._meta.concrete_model.__name__
    assert not PgLog.objects.filter(model_name=worker_report_model_name, model_id=instance.id).exists()

    data = {"status": WorkerReportStatus.DECLINED.value}
    response = __get_response(api_client, instance.id, data, r_cu.user)
    assert PgLog.objects.filter(model_name=worker_report_model_name, model_id=instance.id).exists()
    response_instance = response.data
    if response_updated_by := retrieve_response_instance(response_instance, "updated_by", dict):
        if response_updated_by_user := retrieve_response_instance(response_updated_by, "user", dict):
            assert response_updated_by_user.pop("id") == r_cu.user.id
            assert response_updated_by_user.pop("first_name") == r_cu.user.first_name
            assert response_updated_by_user.pop("last_name") == r_cu.user.last_name
            assert response_updated_by_user.pop("middle_name") == r_cu.user.middle_name
            assert response_updated_by_user.pop("email") == r_cu.user.email
        assert not response_updated_by_user
        if response_updated_by_company_user := retrieve_response_instance(
            response_updated_by, "company_user", dict
        ):
            assert response_updated_by_company_user.pop("id") == r_cu.id
        assert not response_updated_by_company_user
    assert not response_updated_by


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("current_status", "target_status"),
    (
        (WorkerReportStatus.ACCEPTED, WorkerReportStatus.LOADED),
        (WorkerReportStatus.DECLINED, WorkerReportStatus.LOADED),
    ),
)
def test__forbidden_status_conversions__fail(
    api_client, monkeypatch, r_cu, get_worker_report_fi, current_status, target_status
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_worker_report_fi(company=r_cu.company, status=current_status.value)
    data = {"status": target_status.value}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    assert response.data == [FOLLOW_WORKER_REPORT_STATUS_CHANGE_SEQUENCE]


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__without_policy__fail(api_client, mock_policies_false, get_cu_fi, get_worker_report_fi, role):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)

    instance = get_worker_report_fi(company=r_cu.company)

    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__users_from_different_company__fail(api_client, monkeypatch, get_worker_report_fi: Callable, r_cu):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_worker_report_fi()
    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("project_status", NOT_ACTIVE_PROJECT_STATUS)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__not_active_project__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_worker_report_fi: Callable,
    get_project_fi,
    get_schedule_time_slot_fi,
    get_reservation_fi,
    project_status,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    project = get_project_fi(company=r_cu.company, status=project_status.value)

    sts = get_schedule_time_slot_fi(project=project)
    reservation = get_reservation_fi(schedule_time_slot=sts)

    ptw = reservation.project_territory_worker
    instance = get_worker_report_fi(project_territory_worker=ptw, schedule_time_slot=sts)

    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PROJECT_STATUS_MUST_BE_ACTIVE}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("final_status", FINAL_NOT_ARCHIVED_WORKER_REPORT_STATUSES_VALUES)
def test__response_data(
    api_client,
    monkeypatch,
    r_cu,
    get_schedule_time_slot_fi,
    get_reservation_fi,
    get_worker_report_fi,
    final_status,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    monkeypatch.setattr(WorkerBilling, "make_u1_transaction", lambda *args, **kwargs: None)

    instance = get_worker_report_fi(company=r_cu.company, status=WorkerReportStatus.LOADED.value)
    assert not instance.status_final_at
    assert instance.updated_at
    assert not instance.is_status_final

    worker_report_model_name = WorkerReport._meta.concrete_model.__name__
    assert not PgLog.objects.filter(model_name=worker_report_model_name, model_id=instance.id).exists()

    data = {"status": final_status}
    response = __get_response(api_client, instance.id, data, r_cu.user)
    updated_instance = WorkerReport.objects.get(id=instance.id)
    assert updated_instance.updated_at != instance.updated_at
    assert updated_instance.status == final_status
    assert updated_instance.is_status_final
    assert updated_instance.status_final_at
    assert PgLog.objects.filter(model_name=worker_report_model_name, model_id=instance.id).exists()
    response_instance = response.data
    if response_updated_by := retrieve_response_instance(response_instance, "updated_by", dict):
        if response_updated_by_user := retrieve_response_instance(response_updated_by, "user", dict):
            assert response_updated_by_user.pop("id") == r_cu.user.id
            assert response_updated_by_user.pop("first_name") == r_cu.user.first_name
            assert response_updated_by_user.pop("last_name") == r_cu.user.last_name
            assert response_updated_by_user.pop("middle_name") == r_cu.user.middle_name
            assert response_updated_by_user.pop("email") == r_cu.user.email
            assert not response_updated_by_user
        if response_updated_by_cu := retrieve_response_instance(response_updated_by, "company_user", dict):
            assert response_updated_by_cu.pop("id") == r_cu.id
            assert not response_updated_by_cu
        assert not response_updated_by
    if response_cu := retrieve_response_instance(response_instance, "company_user", dict):
        assert response_cu.pop("id") == instance.company_user.id
        if response_cu_u := retrieve_response_instance(response_cu, "user", dict):
            assert response_cu_u.pop("id") == instance.company_user.user.id
            assert response_cu_u.pop("first_name") == instance.company_user.user.first_name
            assert response_cu_u.pop("last_name") == instance.company_user.user.last_name
            assert response_cu_u.pop("middle_name") == instance.company_user.user.middle_name
            assert response_cu_u.pop("email") == instance.company_user.user.email
            assert response_cu_u.pop("phone") == instance.company_user.user.phone
            assert not response_cu_u
        if response_company := retrieve_response_instance(response_cu, "company", dict):
            assert response_company.pop("id") == instance.company_user.company.id
            assert response_company.pop("title") == instance.company_user.company.title
            assert not response_company
        assert not response_cu
    if response_sts := retrieve_response_instance(response_instance, "schedule_time_slot", dict):
        assert response_sts.pop("id") == instance.schedule_time_slot.id
        assert response_sts.pop("reward") == instance.schedule_time_slot.reward
        if response_gp := retrieve_response_instance(response_sts, "geo_point", dict):
            assert response_gp.pop("id") == instance.schedule_time_slot.geo_point.id
            assert response_gp.pop("title") == instance.schedule_time_slot.geo_point.title
            assert response_gp.pop("lat") == instance.schedule_time_slot.geo_point.lat
            assert response_gp.pop("lon") == instance.schedule_time_slot.geo_point.lon
            assert response_gp.pop("city") == instance.schedule_time_slot.geo_point.city
            assert response_gp.pop("address") == instance.schedule_time_slot.geo_point.address
            assert not response_gp
        assert not response_sts
    assert response_instance.pop("id")
    created_at = response_instance.pop("created_at")
    updated_at = response_instance.pop("updated_at")
    status_final_at = response_instance.pop("status_final_at")
    assert created_at and updated_at and status_final_at
    assert created_at != updated_at != status_final_at
    assert response_instance.pop("comment") == ""
    assert response_instance.pop("last_processed_report") == {}
    assert response_instance.pop("payment_status") == WorkerReportPaymentStatus.UNPAID.value
    assert response_instance.pop("payment_error_code") is None
    assert response_instance.pop("payment_error_at") is None
    assert response_instance.pop("dispute_open_at") is None
    assert response_instance.pop("dispute_result_at") is None
    assert response_instance.pop("dispute_status") == WorkerReportDisputeStatus.EMPTY.value
    assert response_instance.pop("dispute_result_comment") == ""
    assert response_instance.pop("dispute_result_reward") == 0
    assert response_instance.pop("reward_at_creation") == 0
    assert response_instance.pop("loaded_at")
    assert response_instance.pop("status") == updated_instance.status == final_status
    assert response_instance.pop("json_fields")
    assert response_instance.pop("reward")
    if response_ps := retrieve_response_instance(response_instance, "project_scheme", dict):
        assert response_ps.pop("id") == instance.project_scheme.id
        if response_project := retrieve_response_instance(response_ps, "project", dict):
            assert response_project.pop("id") == instance.project_scheme.project.id
            assert response_project.pop("title") == instance.project_scheme.project.title
            assert not response_project
        assert not response_ps
    assert not response_instance
