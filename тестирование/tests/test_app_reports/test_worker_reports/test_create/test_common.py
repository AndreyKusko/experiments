import json
import functools

import pytest
import requests
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_create
from tests.mocked_instances import MockResponse
from projects.models.project import PROJECT_IS_DELETED
from ma_saas.constants.report import WorkerReportStatus as WRS
from ma_saas.constants.report import ProcessedReportFormFieldSpecKeys
from ma_saas.constants.system import TYPE, BASENAME, Callable
from ma_saas.constants.company import CUS, ROLES, NOT_ACCEPT_CUS
from clients.policies.interface import Policies
from reports.models.worker_report import WorkerReport
from companies.models.company_user import NOT_TA_RCU_MUST_BE_ACCEPT
from projects.models.project_territory import NOT_TA_PT_REASON
from reports.permissions.worker_report import (
    REQUESTING_USER_MUST_BE_PT_WORKER,
    WORKER_NOT_ALLOWED_TO_UPDATE_REPORT_COMMENT,
)
from reports.serializers.worker_report import WORKER_REPORT_STATUS_IS_FINAL
from projects.models.contractor_project_territory_worker import NOT_TA_REQUESTING_PT_WORKER_REASON

User = get_user_model()


__get_response = functools.partial(request_response_create, path="/api/v1/worker-reports/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, {}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_worker_fi")])
def test__manager__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_project_territory_fi,
    new_worker_report_data,
):
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [r_cu.company.id])

    pt = get_project_territory_fi(company=r_cu.company)
    data = new_worker_report_data(project_territory=pt)

    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_MUST_BE_PT_WORKER}


@pytest.mark.parametrize("role", ROLES)
def test__any_cu_role__without__pt_worker__fail(
    api_client, monkeypatch, get_cu_fi, new_worker_report_data, role
):
    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)

    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [r_cu.company.id])

    data = new_worker_report_data(company=r_cu.company)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_MUST_BE_PT_WORKER}


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_worker__fail(
    api_client,
    monkeypatch,
    get_cu_worker_fi,
    get_pt_worker_fi,
    new_worker_report_data,
    status,
):
    r_cu = get_cu_worker_fi(status=status.value)
    requesting_pt_worker = get_pt_worker_fi(company_user=r_cu)

    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    data = new_worker_report_data(project_territory=requesting_pt_worker.project_territory)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


def test__different_pt_worker__fail(api_client, monkeypatch, get_pt_worker_fi, new_worker_report_data):
    requesting_pt_worker = get_pt_worker_fi()
    r_cu = requesting_pt_worker.company_user

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [r_cu.company.id])

    data = new_worker_report_data(company=requesting_pt_worker.company_user.company)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_MUST_BE_PT_WORKER}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_worker_fi")])
@pytest.mark.parametrize("report_status", (WRS.LOADED.value, WRS.PENDING.value))
def test__creating_statuses__success(
    api_client,
    monkeypatch,
    r_cu,
    get_pt_worker_fi,
    get_schedule_time_slot_fi,
    get_reservation_fi,
    new_worker_report_data,
    report_status,
):
    monkeypatch.setattr(requests, "get", lambda *a, **k: MockResponse(data="2"))

    pt_worker = get_pt_worker_fi(company_user=r_cu)
    r_cu = pt_worker.company_user
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [r_cu.company.id])

    schedule_time_slot = get_schedule_time_slot_fi(project_territory=pt_worker.project_territory)
    get_reservation_fi(project_territory_worker=pt_worker, schedule_time_slot=schedule_time_slot)

    data = new_worker_report_data(schedule_time_slot=schedule_time_slot)

    data["status"] = report_status
    response = __get_response(api_client, data, r_cu.user)
    data["json_fields"] = json.loads(data["json_fields"])
    new_instance = WorkerReport.objects.get(id=response.data["id"])
    assert new_instance.status == response.data["status"] == report_status


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_worker_fi")])
def test__json_fields__success(
    api_client,
    monkeypatch,
    r_cu,
    get_pt_worker_fi,
    get_reservation_fi,
    get_schedule_time_slot_fi,
    new_worker_report_data,
):
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)

    pt_worker = get_pt_worker_fi(company_user=r_cu)

    schedule_time_slot = get_schedule_time_slot_fi(project_territory=pt_worker.project_territory)
    get_reservation_fi(project_territory_worker=pt_worker, schedule_time_slot=schedule_time_slot)

    new_json_fields = [{TYPE: ProcessedReportFormFieldSpecKeys.PHOTO, BASENAME: "123123123.png"}]
    data = new_worker_report_data(schedule_time_slot=schedule_time_slot, json_fields=new_json_fields)
    response = __get_response(api_client, data, r_cu.user)
    assert response.data
    new_instance = WorkerReport.objects.get(id=response.data["id"])
    assert len(new_instance.json_fields) == 1
    assert len(new_instance.json_fields[0]) == 3
    assert len(response.data["json_fields"][0]) == 3
    assert response.data["json_fields"] == new_instance.json_fields


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_worker_fi")])
def test__write_comment_by_worker__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_pt_worker_fi,
    get_reservation_fi,
    get_schedule_time_slot_fi,
    new_worker_report_data,
):
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    pt_worker = get_pt_worker_fi(company_user=r_cu)

    sts = get_schedule_time_slot_fi(project_territory=pt_worker.project_territory)
    get_reservation_fi(project_territory_worker=pt_worker, schedule_time_slot=sts)
    new_comment = get_random_string()
    data = new_worker_report_data(schedule_time_slot=sts, status=WRS.PENDING.value, comment=new_comment)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": WORKER_NOT_ALLOWED_TO_UPDATE_REPORT_COMMENT}


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
@pytest.mark.parametrize("report_status", (WRS.ACCEPTED.value, WRS.DECLINED.value))
def test__creating_with_final_statuses__fail(
    api_client,
    monkeypatch,
    pt_worker,
    get_reservation_fi: Callable,
    new_worker_report_data: Callable,
    get_schedule_time_slot_fi,
    report_status,
):
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    r_cu, pt = pt_worker.company_user, pt_worker.project_territory
    schedule_time_slot = get_schedule_time_slot_fi(project_territory=pt)
    get_reservation_fi(project_territory_worker=pt_worker, schedule_time_slot=schedule_time_slot)

    data = new_worker_report_data(schedule_time_slot=schedule_time_slot)

    data["status"] = report_status
    response = __get_response(api_client, data, r_cu.user, status_codes=ValidationError)
    assert response.data["status"][0] == WORKER_REPORT_STATUS_IS_FINAL


#
# def test__reward_is_same_as_in_schedule_time_slot(
#     api_client,
#     monkeypatch,
#     get_pt_worker_fi: Callable,
#     get_reservation_fi: Callable,
#     get_schedule_time_slot_fi: Callable,
#     new_worker_report_data: Callable,
# ):
#     monkeypatch.setattr(requests, "get", MockResponse, raising=True)
#
#     requesting_pt_worker = get_pt_worker_fi()
#
#     schedule_time_slot = get_schedule_time_slot_fi(project_territory=requesting_pt_worker.project_territory)
#     get_reservation_fi(project_territory_worker=requesting_pt_worker, schedule_time_slot=schedule_time_slot)
#
#     data = new_worker_report_data(schedule_time_slot=schedule_time_slot)
#
#     response = __get_response(
#         api_client,
#         data,
#         requesting_pt_worker.company_user.user,
#     )
#     instance = WorkerReport.objects.get(id=response.data["id"])
#     assert instance.schedule_time_slot.reward == response.data['schedule_time_slot']


def test__deleted_project__fail(
    api_client,
    get_pt_worker_fi,
    get_reservation_fi: Callable,
    get_schedule_time_slot_fi: Callable,
    get_cu_worker_fi,
    new_worker_report_data: Callable,
):

    r_cu = get_cu_worker_fi()
    requesting_pt_worker = get_pt_worker_fi(company_user=r_cu)
    schedule_time_slot = get_schedule_time_slot_fi(project_territory=requesting_pt_worker.project_territory)
    get_reservation_fi(project_territory_worker=requesting_pt_worker, schedule_time_slot=schedule_time_slot)

    data = new_worker_report_data(schedule_time_slot=schedule_time_slot)

    requesting_pt_worker.project_territory.project.is_deleted = True
    requesting_pt_worker.project_territory.project.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": NOT_TA_REQUESTING_PT_WORKER_REASON.format(
            reason=NOT_TA_PT_REASON.format(reason=PROJECT_IS_DELETED)
        )
    }
