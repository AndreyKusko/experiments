from random import randrange

import pytest
import requests
from django.utils.crypto import get_random_string
from rest_framework.exceptions import ValidationError, PermissionDenied

from billing.models import WorkerReportsTransaction
from tests.mocked_instances import MockResponse
from ma_saas.constants.report import WorkerReportStatus
from ma_saas.constants.system import Callable
from clients.policies.interface import Policies
from reports.models.worker_report import WorkerReport
from clients.billing.interfaces.worker import WorkerBilling
from reports.permissions.worker_report import MANAGEMENT_NOT_ALLOWED_TO_UPDATE_IN_PENDING_STATUS
from reports.validators.worker_report_serializer import (
    FOLLOW_WORKER_REPORT_STATUS_CHANGE_SEQUENCE,
    NOT_ALLOWED_UPDATE_REWARD_IF_STATUS_NOT_LOADED,
)
from tests.test_app_reports.test_worker_reports.test_update.test_common import __get_response


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
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__change_status__success(
    api_client,
    monkeypatch,
    r_cu,
    get_worker_report_fi,
    get_project_territory_fi,
    current_status: WorkerReportStatus,
    target_status: WorkerReportStatus,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    monkeypatch.setattr(WorkerBilling, "make_u1_transaction", lambda *args, **kwargs: None)

    pt = get_project_territory_fi(company=r_cu.company)
    instance = get_worker_report_fi(project_territory=pt, status=current_status)
    response = __get_response(api_client, instance.id, {"status": target_status}, r_cu.user)
    updated_instance = WorkerReport.objects.get(id=instance.id)
    assert response.data
    assert response.data["id"] == instance.id
    assert response.data["status"] == target_status == updated_instance.status


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__change_reward_on_loaded_status__success(api_client, monkeypatch, r_cu, get_worker_report_fi):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_worker_report_fi(company=r_cu.company, status=WorkerReportStatus.LOADED.value)
    new_reward = randrange(100)
    data = {"status": WorkerReportStatus.LOADED.value, "reward": new_reward}
    response = __get_response(api_client, instance.id, data, r_cu.user)
    assert response.data
    assert response.data["id"] == instance.id
    updated_instance = WorkerReport.objects.get(id=instance.id)
    assert response.data["reward"] == new_reward == updated_instance.reward != instance.reward


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
@pytest.mark.parametrize("worker_status", [s for s in WorkerReportStatus if s != WorkerReportStatus.PENDING])
def test__change_comment__success(
    api_client, monkeypatch, r_cu, get_worker_report_fi, get_project_territory_fi, worker_status
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    pt = get_project_territory_fi(company=r_cu.company)
    instance = get_worker_report_fi(project_territory=pt, status=worker_status.value)
    assert not instance.comment
    comment = get_random_string()
    response = __get_response(api_client, instance.id, {"comment": comment}, r_cu.user)
    updated_instance = WorkerReport.objects.get(id=instance.id)
    assert response.data.pop("comment") == updated_instance.comment == comment


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accept_and_change_reward__success(api_client, monkeypatch, r_cu, get_worker_report_fi):

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    monkeypatch.setattr(WorkerBilling, "make_u1_transaction", lambda *a, **kw: MockResponse(id=123))
    monkeypatch.setattr(requests, "request", lambda *a, **kw: MockResponse(data={"id": 123}))

    instance = get_worker_report_fi(company=r_cu.company, status=WorkerReportStatus.LOADED.value)
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


#
# @pytest.mark.parametrize("pt_manager", [pytest.lazy_fixture("contractor_pt_manager_fi")])
# def test__no_worker_report_transaction_created_if_tax_service__fail(
#     api_client,
#     monkeypatch,
#     pt_manager: ContractorProjectTerritoryManager,
#     get_reservation_fi: Callable,
#     get_worker_report_fi: Callable,
# ):

#     @pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
#     pt = get_project_territory_fi(company=r_cu.company)
#     project = get_project_fi(company=r_cu.company)

#
#     monkeypatch.setattr(WorkerBilling, "make_u1_transaction", lambda *a, **kw: MockResponse(id=123))
#     tax_service_failed_status = status_code.HTTP_400_BAD_REQUEST
#     mocked_tax_serv_response = MockResponse(return_status_code=tax_service_failed_status)
#     monkeypatch.setattr(requests, "request", lambda *a, **kw: mocked_tax_serv_response)
#
#     reservation = get_reservation_fi(project_territory=pt_manager.project_territory)
#     instance = get_worker_report_fi(
#         project_territory_worker=reservation.project_territory_worker,
#         geo_point=reservation.geo_point,
#         status=WorkerReportStatus.LOADED.value,
#     )
#     assert not instance.is_paid
#     assert not WorkerReportsTransaction.objects.filter(worker_report=instance).exists()
#     target_status = WorkerReportStatus.ACCEPTED.value
#     assert instance.status != target_status
#     target_status = WorkerReportStatus.ACCEPTED.value
#     new_reward = randrange(100)
#     response = __get_response(
#         api_client,
#         data={"status": target_status, "reward": new_reward},
#         instance_id=instance.id,
#         user=pt_manager.company_user.user,
#         status_codes=status_code.HTTP_500_INTERNAL_SERVER_ERROR,
#     )
#     updated_instance = WorkerReport.objects.get(id=instance.id)
#     assert not WorkerReportsTransaction.objects.filter(worker_report=instance).exists()
#     assert updated_instance.is_paid
#     assert updated_instance.updated_at.strftime(DATETIME_STR_FORMAT)
#     assert updated_instance.loaded_at.strftime(DATETIME_STR_FORMAT)
#     assert updated_instance.status == target_status
#     assert response.data["detail"] == CREATE_TAX_CHECK_FAILED.format(
#         worker_report=updated_instance.id,
#         status_code=tax_service_failed_status,
#         content=mocked_tax_serv_response.content,
#     )


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
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
    r_cu,
    get_worker_report_fi,
    get_schedule_time_slot_fi,
    get_reservation_fi,
    get_project_territory_fi,
    current_status,
    target_status,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    schedule_time_slot = get_schedule_time_slot_fi(project_territory=pt)
    reservation = get_reservation_fi(schedule_time_slot=schedule_time_slot)

    instance = get_worker_report_fi(
        schedule_time_slot=schedule_time_slot,
        project_territory_worker=reservation.project_territory_worker,
        status=current_status,
    )
    data = {"status": target_status}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    assert response.data[0] == FOLLOW_WORKER_REPORT_STATUS_CHANGE_SEQUENCE


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__change_if_status_loading__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_schedule_time_slot_fi,
    get_reservation_fi,
    get_worker_report_fi,
    get_project_territory_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    schedule_time_slot = get_schedule_time_slot_fi(project_territory=pt)
    reservation = get_reservation_fi(schedule_time_slot=schedule_time_slot)

    instance = get_worker_report_fi(
        project_territory_worker=reservation.project_territory_worker,
        schedule_time_slot=schedule_time_slot,
        status=WorkerReportStatus.PENDING.value,
    )
    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": MANAGEMENT_NOT_ALLOWED_TO_UPDATE_IN_PENDING_STATUS}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
@pytest.mark.parametrize("report_status", (WorkerReportStatus.DECLINED, WorkerReportStatus.ACCEPTED))
def test__change_reward__if_status_not_loaded__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_schedule_time_slot_fi,
    get_reservation_fi,
    get_project_territory_fi,
    get_worker_report_fi: Callable,
    report_status,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    schedule_time_slot = get_schedule_time_slot_fi(project_territory=pt)
    reservation = get_reservation_fi(schedule_time_slot=schedule_time_slot)

    instance = get_worker_report_fi(
        project_territory_worker=reservation.project_territory_worker,
        schedule_time_slot=schedule_time_slot,
        status=report_status.value,
        reward=randrange(100),
    )

    new_reward = instance.reward + 1
    data = {"reward": new_reward}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    assert response.data == {"non_field_errors": [NOT_ALLOWED_UPDATE_REWARD_IF_STATUS_NOT_LOADED]}
