import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated

from tests.utils import request_response_get, retrieve_response_instance
from pg_logger.models import PgLog
from ma_saas.constants.report import WorkerReportPaymentStatus
from ma_saas.constants.system import DATETIME_FORMAT, Callable, PgLogLVL
from ma_saas.constants.company import (
    CUR,
    CUS,
    ROLES,
    NOT_ACCEPT_CUS,
    NOT_OWNER_ROLES,
    NOT_OWNER_AND_NOT_WORKER_ROLES,
)
from clients.policies.interface import Policies
from reports.models.worker_report import WorkerReport
from companies.models.company_user import CompanyUser

User = get_user_model()

__get_response = functools.partial(request_response_get, path="/api/v1/worker-reports/")


def test__anonymous_user__fail(api_client, get_worker_report_fi):

    instance = get_worker_report_fi()

    response = __get_response(api_client, instance.id, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(api_client, monkeypatch, get_worker_report_fi, r_cu):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_worker_report_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user)

    response_instance = response.data

    assert response_instance.pop("id") == instance.id

    if schedule_time_slot := retrieve_response_instance(response_instance, "schedule_time_slot", dict):
        assert schedule_time_slot.pop("id") == instance.schedule_time_slot.id
        assert schedule_time_slot.pop("reward") == instance.schedule_time_slot.reward
        if response_geo_point := retrieve_response_instance(schedule_time_slot, "geo_point", dict):
            assert response_geo_point.pop("id") == instance.schedule_time_slot.geo_point.id
            assert response_geo_point.pop("title") == instance.schedule_time_slot.geo_point.title
            assert response_geo_point.pop("city") == instance.schedule_time_slot.geo_point.city
            assert response_geo_point.pop("address") == instance.schedule_time_slot.geo_point.address
            assert response_geo_point.pop("lat") == instance.schedule_time_slot.geo_point.lat
            assert response_geo_point.pop("lon") == instance.schedule_time_slot.geo_point.lon

        assert not response_geo_point, f"response_geo_point = {response_geo_point}"

    assert not schedule_time_slot, f"schedule_time_slot = {schedule_time_slot}"

    if response_company_user := retrieve_response_instance(response_instance, "company_user", dict):
        assert response_company_user.pop("id") == instance.company_user.id
        if response_company := retrieve_response_instance(response_company_user, "company", dict):
            assert response_company.pop("id") == instance.company_user.company.id
            assert response_company.pop("title") == instance.company_user.company.title
        assert not response_company, f"response_company = {response_company}"

        if response_user := retrieve_response_instance(response_company_user, "user", dict):
            assert response_user.pop("id") == instance.company_user.user.id
            assert response_user.pop("first_name") == instance.company_user.user.first_name
            assert response_user.pop("middle_name") == instance.company_user.user.middle_name
            assert response_user.pop("last_name") == instance.company_user.user.last_name
            assert response_user.pop("phone") == instance.company_user.user.phone
            assert response_user.pop("email") == instance.company_user.user.email
        assert not response_user, f"response_user = {response_user}"
    assert not response_company_user, f"response_company_user = {response_company_user}"

    assert response_instance.pop("status") == instance.status
    assert response_instance.pop("comment") == instance.comment

    assert response_instance.pop("reward") == instance.reward
    assert response_instance.pop("payment_status") == WorkerReportPaymentStatus.UNPAID.value
    assert response_instance.pop("created_at") == instance.created_at.strftime(DATETIME_FORMAT)
    assert response_instance.pop("updated_at") == instance.updated_at.strftime(DATETIME_FORMAT)
    assert response_instance.pop("loaded_at") == instance.loaded_at.strftime(DATETIME_FORMAT)
    assert response_instance.pop("last_processed_report") == {}
    assert response_instance.pop("updated_by") == {"user": {}, "company_user": {}}
    assert response_instance.pop("payment_error_code") == None
    assert response_instance.pop("dispute_status") == instance.dispute_status
    assert response_instance.pop("dispute_result_comment") == instance.dispute_result_comment
    assert response_instance.pop("dispute_result_reward") == instance.dispute_result_reward
    assert response_instance.pop("payment_error_at") == instance.payment_error_at
    assert response_instance.pop("status_final_at") == instance.status_final_at
    assert response_instance.pop("reward_at_creation") == instance.reward_at_creation
    assert response_instance.pop("dispute_open_at") == instance.dispute_open_at
    assert response_instance.pop("dispute_result_at") == instance.dispute_result_at

    if response_project_scheme := retrieve_response_instance(response_instance, "project_scheme", dict):
        assert response_project_scheme.pop("id") == instance.project_scheme.id
        if response_project := retrieve_response_instance(response_project_scheme, "project", dict):
            assert response_project.pop("id") == instance.project_scheme.project.id
            assert response_project.pop("title") == instance.project_scheme.project.title
        assert not response_project, f"response_project = {response_project}"
    assert not response_project_scheme, f"response_project_scheme = {response_project_scheme}"

    assert response_instance.pop("json_fields")
    assert not response_instance, f"response_instance ={response_instance}"


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", CUS)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__updated_by_company_user_data(
    api_client,
    mock_policies_false,
    get_worker_report_fi,
    r_cu,
    get_cu_fi,
    status,
    role,
):
    company = r_cu.company

    instance = get_worker_report_fi(company=r_cu.company)
    updated_cu = get_cu_fi(company=company, role=role, status=status.value)

    PgLog.objects.create(
        level=PgLogLVL.info.value,
        user=updated_cu.user,
        model_name=WorkerReport._meta.concrete_model.__name__,
        model_id=instance.id,
        message="",
        params={},
    )
    response = __get_response(
        api_client,
        instance.id,
        r_cu.user,
    )
    response_instance = response.data
    assert response_instance
    assert response_instance["id"] == instance.id
    response_updated_by = response_instance.pop("updated_by")

    response_updated_by_company_user = response_updated_by.pop("company_user")
    assert response_updated_by_company_user
    if response_updated_by_company_user:
        assert response_updated_by_company_user.pop("id") == updated_cu.id
    assert not response_updated_by_company_user

    response_updated_by_user = response_updated_by.pop("user")
    assert response_updated_by_user
    if response_updated_by_user:
        assert response_updated_by_user.pop("id") == updated_cu.user.id
        assert response_updated_by_user.pop("first_name") == updated_cu.user.first_name
        assert response_updated_by_user.pop("last_name") == updated_cu.user.last_name
        assert response_updated_by_user.pop("middle_name") == updated_cu.user.middle_name
        assert response_updated_by_user.pop("email") == updated_cu.user.email
    assert not response_updated_by_user

    assert not response_updated_by_user


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__updated_by_admin_data(api_client, monkeypatch, get_worker_report_fi, get_user_fi, r_cu):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_worker_report_fi(company=r_cu.company)

    updated_user = get_user_fi()
    updated_user.is_superuser = True
    updated_user.save()

    PgLog.objects.create(
        level=PgLogLVL.info.value,
        user=updated_user,
        model_name=WorkerReport._meta.concrete_model.__name__,
        model_id=instance.id,
        message="",
        params={},
    )
    response = __get_response(
        api_client,
        instance.id,
        r_cu.user,
    )

    response_instance = response.data
    assert response_instance
    assert response_instance["id"] == instance.id
    response_updated_by = response_instance.pop("updated_by")

    response_updated_by_company_user = response_updated_by.pop("company_user")
    assert response_updated_by_company_user == {}

    response_updated_by_user = response_updated_by.pop("user")
    assert response_updated_by_user
    if response_updated_by_user:
        assert response_updated_by_user.pop("id") == updated_user.id
        assert response_updated_by_user.pop("first_name") == updated_user.first_name
        assert response_updated_by_user.pop("last_name") == updated_user.last_name
        assert response_updated_by_user.pop("middle_name") == updated_user.middle_name
        assert response_updated_by_user.pop("email") == updated_user.email
    assert not response_updated_by_user

    assert not response_updated_by_user


@pytest.mark.parametrize("is_pt_worker", (True, False))
@pytest.mark.parametrize("is_reservation", (True, False))
@pytest.mark.parametrize("status", CUS)
def test__related_via_reservation_worker_can_request_his_reports_in_any_case(
    api_client,
    monkeypatch,
    get_cu_worker_fi,
    get_pt_worker_fi,
    get_reservation_fi: Callable,
    get_worker_report_fi: Callable,
    get_schedule_time_slot_fi,
    is_pt_worker: bool,
    is_reservation: bool,
    status,
):
    """
    Worker
    with/out CompanyUser status ACCEPT
    with/out ProjectTerritoryWorker
    with/out Reservation
    """
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    monkeypatch.setattr(CompanyUser, "deactivate_policies", lambda *a, **kw: None)

    r_cu = get_cu_worker_fi(status=status.value)
    pt_worker = get_pt_worker_fi(company=r_cu.company)
    pt = pt_worker.project_territory

    sts = get_schedule_time_slot_fi(company=r_cu.company, project_territory=pt)
    reservation = get_reservation_fi(
        schedule_time_slot=sts, project_territory_worker=pt_worker, project_territory=pt
    )
    instance = get_worker_report_fi(project_territory_worker=reservation.project_territory_worker)
    if not is_reservation:
        reservation.is_deleted = True
        reservation.save()
    if not is_pt_worker:
        pt_worker.is_deleted = True
        pt_worker.save()

    company_user = pt_worker.company_user
    company_user.status = status.value
    company_user.save()

    response = __get_response(api_client, instance.id, company_user.user)

    assert response.data
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__related_manager__with_policy__success(
    api_client, monkeypatch, r_cu, get_worker_report_fi, get_project_territory_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    instance = get_worker_report_fi(project_territory=pt)
    response = __get_response(api_client, instance.id, r_cu.user)
    assert response.data
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, get_worker_report_fi):
    instance = get_worker_report_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user)
    assert response.data
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__fail(api_client, monkeypatch, get_cu_fi, get_worker_report_fi, status):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_worker_report_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_related_company_users__without_policy__fail(
    api_client, mock_policies_false, get_cu_fi, get_worker_report_fi, role
):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)

    instance = get_worker_report_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("role", NOT_OWNER_AND_NOT_WORKER_ROLES)
def test__not_related_company_users__with_policy__success(
    api_client,
    monkeypatch,
    get_cu_fi,
    get_worker_report_fi,
    role,
):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_worker_report_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.xfail
def test__not_related_worker__with_policy__fail(api_client, monkeypatch, get_cu_fi, get_worker_report_fi):
    r_cu = get_cu_fi(role=CUR.WORKER, status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_worker_report_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.xfail
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__users_from_different_company__with_policy__fail(
    api_client, monkeypatch, get_worker_report_fi, r_cu
):
    instance = get_worker_report_fi()
    r_cu = instance.company_user
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}
