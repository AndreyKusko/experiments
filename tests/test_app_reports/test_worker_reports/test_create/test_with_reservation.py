import json
import datetime as dt
from copy import deepcopy

import pytest
import requests
from rest_framework.exceptions import ValidationError, PermissionDenied

from tests.utils import retrieve_response_instance
from ma_saas.utils import system
from tests.mocked_instances import MockResponse
from ma_saas.constants.system import Callable
from clients.policies.interface import Policies
from reports.models.worker_report import (
    ALLOWED_REPORTS_QTY_EXCEEDED,
    SCHEDULE_TIME_SLOT_ACTIVE_INTERVAL_IS_IN_PAST,
    SCHEDULE_TIME_SLOT_ACTIVE_INTERVAL_IS_IN_FUTURE,
    WorkerReport,
)
from projects.models.project_scheme import ProjectScheme
from tasks.models.schedule_time_slot import ScheduleTimeSlot
from reports.permissions.worker_report import ACTIVE_RESERVATION_REQUIRED
from reports.serializers.worker_report_create import RESERVATION_IS_IN_PAST, RESERVATION_IS_IN_FUTURE
from tests.test_app_reports.test_worker_reports.test_create.test_common import __get_response


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__response_data(
    api_client,
    monkeypatch,
    get_project_scheme_fi: Callable,
    pt_worker,
    get_reservation_fi: Callable,
    get_schedule_time_slot_fi: Callable,
    new_worker_report_data: Callable,
):
    r_cu, pt = pt_worker.company_user, pt_worker.project_territory

    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])

    project_scheme = get_project_scheme_fi(project=pt.project)
    sts = get_schedule_time_slot_fi(project_territory=pt, project_scheme=project_scheme)
    reservation = get_reservation_fi(project_territory_worker=pt_worker, schedule_time_slot=sts)
    data = new_worker_report_data(
        project_territory_worker=pt_worker, schedule_time_slot=sts, project_scheme=project_scheme
    )
    del data["reward"]
    response = __get_response(api_client, data, r_cu.user)
    response_instance = response.data

    assert response_instance.pop("id")

    if response_company_user := retrieve_response_instance(response_instance, "company_user", dict):
        assert response_company_user.pop("id") == pt_worker.company_user.id

        if response_user := retrieve_response_instance(response_company_user, "user", dict):
            assert response_user.pop("id") == pt_worker.company_user.user.id
            assert response_user.pop("first_name") == pt_worker.company_user.user.first_name
            assert response_user.pop("middle_name") == pt_worker.company_user.user.middle_name
            assert response_user.pop("last_name") == pt_worker.company_user.user.last_name
            assert response_user.pop("phone") == pt_worker.company_user.user.phone
            assert response_user.pop("email") == pt_worker.company_user.user.email
        assert not response_user

        if response_company := retrieve_response_instance(response_company_user, "company", dict):
            assert response_company.pop("id") == pt_worker.company_user.company.id
            assert response_company.pop("title") == pt_worker.company_user.company.title
        assert not response_company

    assert not response_company_user

    if response_sts := retrieve_response_instance(response_instance, "schedule_time_slot", dict):
        assert response_sts.pop("id") == sts.id
        assert response_sts.pop("reward") == sts.reward
        if response_geo_point := retrieve_response_instance(response_sts, "geo_point", dict):
            assert response_geo_point.pop("id") == sts.geo_point.id == reservation.geo_point.id
            assert response_geo_point.pop("title") == sts.geo_point.title
            assert response_geo_point.pop("city") == sts.geo_point.city
            assert response_geo_point.pop("address") == sts.geo_point.address
            assert response_geo_point.pop("lat") == sts.geo_point.lat
            assert response_geo_point.pop("lon") == sts.geo_point.lon
        assert not response_geo_point
    assert not response_sts

    if response_project_scheme := retrieve_response_instance(response_instance, "project_scheme", dict):
        assert response_project_scheme.pop("id") == project_scheme.id
        if response_project := retrieve_response_instance(response_project_scheme, "project", dict):
            assert response_project.pop("id") == project_scheme.project.id
            assert response_project.pop("title") == project_scheme.project.title
        assert not response_project, f"response_project = {response_project}"
    assert not response_project_scheme, f"response_project_scheme = {response_project_scheme}"

    assert response_instance.pop("json_fields")
    assert (
        response_instance.pop("updated_at")
        != response_instance.pop("created_at")
        != response_instance.pop("status_final_at")
    )
    assert response_instance.pop("status") == data["status"]

    assert not response_instance


@pytest.mark.parametrize(
    ("is_too_early", "err_msg"),
    [
        (True, SCHEDULE_TIME_SLOT_ACTIVE_INTERVAL_IS_IN_FUTURE),
        (False, SCHEDULE_TIME_SLOT_ACTIVE_INTERVAL_IS_IN_PAST),
    ],
)
@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__pt_worker_with_invalid_schedule_timeslot_interval__fail(
    api_client,
    monkeypatch,
    get_schedule_time_slot_fi,
    pt_worker,
    get_reservation_fi,
    new_worker_report_data,
    is_too_early,
    get_geo_point_fi,
    err_msg,
):
    r_cu, pt = pt_worker.company_user, pt_worker.project_territory

    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])

    geo_point = get_geo_point_fi(project_territory=pt)

    td = dt.timedelta(minutes=30) if is_too_early else -dt.timedelta(minutes=30)
    active_since = system.get_now() + td + dt.timedelta(hours=float(geo_point.utc_offset))

    active_till = active_since + dt.timedelta(minutes=10)
    schedule_time_slot = get_schedule_time_slot_fi(
        project_territory=pt, active_since_local=active_since, active_till_local=active_till
    )
    get_reservation_fi(project_territory_worker=pt_worker, schedule_time_slot=schedule_time_slot)

    data = new_worker_report_data(project_territory_worker=pt_worker, schedule_time_slot=schedule_time_slot)
    response = __get_response(api_client, data, r_cu.user, status_codes=ValidationError)
    assert response.data == {"schedule_time_slot": [err_msg]}


@pytest.mark.parametrize(
    ("is_too_early", "err_msg"), [(True, RESERVATION_IS_IN_FUTURE), (False, RESERVATION_IS_IN_PAST)]
)
@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__pt_worker_with_invalid_schedule_reservation__fail(
    api_client,
    monkeypatch,
    get_schedule_time_slot_fi,
    pt_worker,
    get_reservation_fi,
    new_worker_report_data,
    is_too_early,
    err_msg,
):
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])

    td = dt.timedelta(days=1) if is_too_early else -dt.timedelta(days=1)
    active_since = system.get_now() + td
    active_till = active_since + dt.timedelta(days=1)

    sts = get_schedule_time_slot_fi(project_territory=pt_worker.project_territory)
    get_reservation_fi(
        project_territory_worker=pt_worker,
        schedule_time_slot=sts,
        active_since_local=active_since,
        active_till_local=active_till,
    )

    data = new_worker_report_data(project_territory_worker=pt_worker, schedule_time_slot=sts)

    del data["reward"]
    r_cu = pt_worker.company_user
    response = __get_response(api_client, data, r_cu.user, status_codes=ValidationError)
    assert response.data == {"non_field_errors": [err_msg]}


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__pt_worker_with_deleted_reservations__fail(
    api_client,
    monkeypatch,
    get_reservation_fi: Callable,
    pt_worker,
    new_worker_report_data: Callable,
    get_schedule_time_slot_fi,
):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])

    sts = get_schedule_time_slot_fi(project_territory=pt_worker.project_territory)
    reservation = get_reservation_fi(project_territory_worker=pt_worker, schedule_time_slot=sts)
    data = new_worker_report_data(schedule_time_slot=sts)
    reservation.is_deleted = True
    reservation.save()

    response = __get_response(api_client, data, pt_worker.company_user.user, status_codes=PermissionDenied)
    assert response.data == {"detail": ACTIVE_RESERVATION_REQUIRED}


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__worker_with_different_reservation__fail(
    api_client,
    monkeypatch,
    pt_worker,
    get_reservation_fi: Callable,
    new_worker_report_data: Callable,
    get_schedule_time_slot_fi,
):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])

    pt, ptw_data = pt_worker.project_territory, dict(project_territory_worker=pt_worker)

    _another_schedule_time_slot = get_schedule_time_slot_fi(project_territory=pt)
    _another_reservation = get_reservation_fi(**ptw_data, schedule_time_slot=_another_schedule_time_slot)
    sts = get_schedule_time_slot_fi(project_territory=pt)
    inactive_reservation = get_reservation_fi(**ptw_data, schedule_time_slot=sts)
    data = new_worker_report_data(schedule_time_slot=sts)
    inactive_reservation.is_deleted = True
    inactive_reservation.save()
    response = __get_response(api_client, data, pt_worker.company_user.user, status_codes=PermissionDenied)
    assert response.data == {"detail": ACTIVE_RESERVATION_REQUIRED}


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__worker_without_reservation__fail(
    api_client, monkeypatch, get_reservation_fi, pt_worker, new_worker_report_data, get_schedule_time_slot_fi
):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])

    sts = get_schedule_time_slot_fi(project_territory=pt_worker.project_territory)
    reservation = get_reservation_fi(project_territory_worker=pt_worker, schedule_time_slot=sts)
    data = new_worker_report_data(schedule_time_slot=sts)

    reservation.delete()

    response = __get_response(api_client, data, pt_worker.company_user.user, status_codes=PermissionDenied)
    assert response.data == {"detail": ACTIVE_RESERVATION_REQUIRED}


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__duplicate_with_reservation__success(
    api_client,
    monkeypatch,
    pt_worker,
    get_schedule_time_slot_fi: Callable,
    get_reservation_fi: Callable,
    new_worker_report_data: Callable,
):
    r_cu = pt_worker.company_user
    monkeypatch.setattr(requests, "get", MockResponse)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    sts = get_schedule_time_slot_fi(project_territory=pt_worker.project_territory, max_reports_qty=2)
    get_reservation_fi(project_territory_worker=pt_worker, schedule_time_slot=sts)
    data = new_worker_report_data(project_territory_worker=pt_worker, schedule_time_slot=sts)

    duplicate_data = deepcopy(data)
    duplicate_data["project_scheme"] = ProjectScheme.objects.get(id=data["project_scheme"])
    duplicate_data["schedule_time_slot"] = ScheduleTimeSlot.objects.get(id=data["schedule_time_slot"])
    duplicate_data["json_fields"] = json.loads(duplicate_data["json_fields"])
    duplicate_data["company_user"] = r_cu
    WorkerReport.objects.create(**duplicate_data)
    del data["reward"]
    response = __get_response(api_client, data, r_cu.user)
    assert response.data.get("id")


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__more_than_max_reports_qty__fail(
    api_client,
    monkeypatch,
    pt_worker,
    get_schedule_time_slot_fi: Callable,
    get_reservation_fi: Callable,
    new_worker_report_data: Callable,
):
    r_cu, pt = pt_worker.company_user, pt_worker.project_territory

    monkeypatch.setattr(requests, "get", MockResponse)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])

    max_qty = 1
    schedule_time_slot = get_schedule_time_slot_fi(project_territory=pt, max_reports_qty=max_qty)
    _schedule_time_slot = dict(schedule_time_slot=schedule_time_slot)
    get_reservation_fi(project_territory_worker=pt_worker, **_schedule_time_slot)
    data = new_worker_report_data(project_territory_worker=pt_worker, **_schedule_time_slot)
    for i in range(max_qty):
        response = __get_response(api_client, data, r_cu.user)
        assert response.data.get("id")
    response = __get_response(api_client, data, r_cu.user, status_codes=ValidationError)
    assert response.data == {"schedule_time_slot": [ALLOWED_REPORTS_QTY_EXCEEDED]}
