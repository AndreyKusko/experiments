import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated

from tests.utils import request_response_list, retrieve_response_instance
from ma_saas.constants.report import ProcessedReportStatus, WorkerReportPaymentStatus
from ma_saas.constants.system import DATETIME_FORMAT, Callable
from ma_saas.constants.company import CUR, CUS, NOT_ACCEPT_CUS, NOT_OWNER_AND_NOT_WORKER_ROLES
from clients.policies.interface import Policies
from companies.models.company_user import CompanyUser

User = get_user_model()


__get_response = functools.partial(request_response_list, path="/api/v1/worker-reports/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


def test__user_without_companies__got_nothing(
    api_client, monkeypatch, user_fi, get_worker_report_fi, get_schedule_time_slot_fi, get_reservation_fi
):
    instance = get_worker_report_fi()
    company_id = instance.schedule_time_slot.geo_point.project_territory.project.company.id
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [company_id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    response = __get_response(api_client, user=user_fi)
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(api_client, monkeypatch, get_worker_report_fi, r_cu):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    instance = get_worker_report_fi(company=r_cu.company)
    response = __get_response(api_client, r_cu.user)
    assert len(response.data) == 1
    response_instance = response.data[0]
    assert response_instance.pop("id") == instance.id
    if response_sts := retrieve_response_instance(response_instance, "schedule_time_slot", dict):
        assert response_sts.pop("id") == instance.schedule_time_slot.id
        assert response_sts.pop("reward") == instance.schedule_time_slot.reward
        if response_geo_point := retrieve_response_instance(response_sts, "geo_point", dict):
            assert response_geo_point.pop("id") == instance.schedule_time_slot.geo_point.id
            assert response_geo_point.pop("title") == instance.schedule_time_slot.geo_point.title
            assert response_geo_point.pop("city") == instance.schedule_time_slot.geo_point.city
            assert response_geo_point.pop("address") == instance.schedule_time_slot.geo_point.address
            assert response_geo_point.pop("lat") == instance.schedule_time_slot.geo_point.lat
            assert response_geo_point.pop("lon") == instance.schedule_time_slot.geo_point.lon
        assert not response_geo_point, f"response_geo_point = {response_geo_point}"
    assert not response_sts, f"response_schedule_time_slot = {response_sts}"
    assert response_instance.pop("status") == instance.status
    assert response_instance.pop("comment") == instance.comment
    if response_company_user := retrieve_response_instance(response_instance, "company_user", dict):
        assert response_company_user.pop("id") == instance.company_user.id
        response_company = response_company_user.pop("company")
        assert response_company
        if response_company:
            assert response_company.pop("id") == instance.company_user.company.id
            assert response_company.pop("title") == instance.company_user.company.title
        assert not response_company
    assert not response_company_user, f"response_company_user = {response_company_user}"
    if response_project_scheme := retrieve_response_instance(response_instance, "project_scheme", dict):
        assert response_project_scheme.pop("id") == instance.project_scheme.id
        if response_project := retrieve_response_instance(response_project_scheme, "project", dict):
            assert response_project.pop("id") == instance.project_scheme.project.id
            assert response_project.pop("title") == instance.project_scheme.project.title
        assert not response_project, f"response_project = {response_project}"
    assert not response_project_scheme, f"response_project_scheme = {response_project_scheme}"
    assert response_instance.pop("reward") == instance.reward
    assert response_instance.pop("reward_at_creation") == instance.schedule_time_slot.reward
    assert response_instance.pop("payment_error_code") is None
    assert response_instance.pop("dispute_status")
    assert response_instance.pop("last_processed_report") == {}
    assert response_instance.pop("payment_status") == WorkerReportPaymentStatus.UNPAID.value
    assert response_instance.pop("created_at") == instance.created_at.strftime(DATETIME_FORMAT)
    assert response_instance.pop("updated_at") == instance.updated_at.strftime(DATETIME_FORMAT)
    assert response_instance.pop("loaded_at") == instance.loaded_at.strftime(DATETIME_FORMAT)
    assert not response_instance, f"response_instance = {response_instance}"


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__processed_report_status_field_data__second_processed_report(
    api_client, monkeypatch, get_worker_report_fi: Callable, get_processed_report_fi, r_cu
):
    """Если нет принятых репортов, берется статус последнего репорта менеджера."""
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_worker_report_fi(company=r_cu.company)
    expecting_report_status = ProcessedReportStatus.CREATED.value
    get_processed_report_fi(worker_report=instance, status=ProcessedReportStatus.DECLINED.value)
    last_processed_report = get_processed_report_fi(worker_report=instance, status=expecting_report_status)

    response = __get_response(api_client, r_cu.user)
    assert len(response.data) == 1
    assert response.data[0]["last_processed_report"] == {
        "id": last_processed_report.id,
        "status": last_processed_report.status,
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_processed_report__status_display(
    api_client,
    monkeypatch,
    get_worker_report_fi,
    get_processed_report_fi,
    r_cu,
):
    """Если если есть принятые репорт, берется статус первого приянтого репорта."""
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_worker_report_fi(company=r_cu.company)
    accepted_status = ProcessedReportStatus.ACCEPTED.value
    get_processed_report_fi(worker_report=instance, status=accepted_status)
    last_processed_report = get_processed_report_fi(
        worker_report=instance, status=ProcessedReportStatus.DECLINED.value
    )
    response = __get_response(api_client, r_cu.user)
    assert len(response.data) == 1
    assert response.data[0]["last_processed_report"] == {
        "id": last_processed_report.id,
        "status": last_processed_report.status,
    }


@pytest.mark.parametrize("is_pt_worker", (True, False))
@pytest.mark.parametrize("is_reservation", (True, False))
@pytest.mark.parametrize("status", CUS)
@pytest.mark.parametrize("qty", [3])
@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__related_via_reservation_worker_can_request_his_reports_in_any_case(
    api_client,
    monkeypatch,
    pt_worker,
    get_reservation_fi: Callable,
    get_worker_report_fi: Callable,
    get_schedule_time_slot_fi,
    is_pt_worker: bool,
    is_reservation: bool,
    status,
    qty,
):
    """
    Worker
    with/out CompanyUser status ACCEPT
    with/out ProjectTerritoryWorker
    with/out Reservation
    """
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    monkeypatch.setattr(CompanyUser, "deactivate_policies", lambda *a, **kw: None)

    sts = get_schedule_time_slot_fi(project_territory=pt_worker.project_territory, max_reports_qty=qty)
    reservation = get_reservation_fi(schedule_time_slot=sts, project_territory_worker=pt_worker)
    [get_worker_report_fi(project_territory_worker=pt_worker, schedule_time_slot=sts) for _ in range(qty)]

    if not is_reservation:
        reservation.is_deleted = True
        reservation.save()
    if not is_pt_worker:
        pt_worker.is_deleted = True
        pt_worker.save()
    pt_worker.company_user.status = status.value
    pt_worker.company_user.save()

    response = __get_response(api_client, pt_worker.company_user.user)
    assert len(response.data) == qty


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_related_manager__without_policy__empty(
    api_client, monkeypatch, r_cu, get_worker_report_fi, get_project_territory_fi
):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    get_worker_report_fi(project_territory=pt)
    response = __get_response(api_client, r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_related_manager__with_policy__success(
    api_client, monkeypatch, r_cu, get_worker_report_fi, get_project_territory_fi
):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    instance = get_worker_report_fi(project_territory=pt)
    response = __get_response(api_client, r_cu.user)
    assert response.data[0]["id"] == instance.id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_related_manager__fail(
    api_client, monkeypatch, get_cu_manager_fi, get_worker_report_fi, status
):
    r_cu = get_cu_manager_fi(status=status.value)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    get_worker_report_fi(company=r_cu.company)
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == 0


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, get_worker_report_fi):
    instance = get_worker_report_fi(company=r_cu.company)
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == 1
    assert response.data[0]["id"] == instance.id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__fail(
    api_client, monkeypatch, get_cu_fi, get_pt_worker_fi, get_worker_report_fi, status
):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    pt_worker = get_pt_worker_fi(company=r_cu.company)
    get_worker_report_fi(project_territory=pt_worker.project_territory)
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == 0


@pytest.mark.parametrize("role", NOT_OWNER_AND_NOT_WORKER_ROLES)
def test__not_owner__with_policy__success(api_client, monkeypatch, get_cu_fi, get_worker_report_fi, role):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    instance = get_worker_report_fi(company=r_cu.company)
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == 1
    assert response.data[0]["id"] == instance.id


@pytest.mark.parametrize("role", NOT_OWNER_AND_NOT_WORKER_ROLES)
def test__not_owner__without_policy__empty_response(
    api_client, monkeypatch, get_cu_fi, get_worker_report_fi, role
):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    get_worker_report_fi(company=r_cu.company)
    response = __get_response(api_client, user=r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__not_related_to_company__empty_response(api_client, monkeypatch, get_worker_report_fi, r_cu):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    instance = get_worker_report_fi()
    company = instance.company_user.company
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [company.id])
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == 0
