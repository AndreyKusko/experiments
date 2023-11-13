import datetime as dt
import functools

import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_create
from ma_saas.utils import system
from tasks.models.utils import ACTIVE_SINCE_MUST_NOT_BE_IN_PAST
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from clients.policies.interface import Policies
from tasks.models.schedule_time_slot import (
    ACTIVE_SINCE_LOCAL_TIME_MUST_BE_BEFORE_LOCAL_ACTIVE_TILL_LOCAL_TIME,
    ScheduleTimeSlot,
)

User = get_user_model()

__get_response = functools.partial(request_response_create, path="/api/v1/schedule-time-slots/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, data={}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policy_true, r_cu, new_schedule_time_slot_data):
    mock_policy_true(r_cu.company)
    data = new_schedule_time_slot_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user)
    assert ScheduleTimeSlot.objects.filter(id=response.data["id"]).exists()


@pytest.mark.xfail
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_worker_fi")])
@pytest.mark.parametrize("has_object_policy", [True, False])
def test__worker__any_policy__fail(
    api_client, monkeypatch, r_cu, new_schedule_time_slot_data, has_object_policy
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    data = new_schedule_time_slot_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert not response.data.get["id"]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__manager__with_policy__success(api_client, monkeypatch, r_cu, new_schedule_time_slot_data):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    data = new_schedule_time_slot_data(company=r_cu.company)

    response = __get_response(api_client, data=data, user=r_cu.user)
    assert ScheduleTimeSlot.objects.filter(id=response.data["id"]).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__manager__without_policy__fail(api_client, monkeypatch, r_cu, new_schedule_time_slot_data):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    data = new_schedule_time_slot_data(company=r_cu.company)

    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PermissionDenied.default_detail}, f"response.data = {response.data}"


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__from_different_company__fail(api_client, monkeypatch, r_cu, new_schedule_time_slot_data):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    data = new_schedule_time_slot_data()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}


@pytest.mark.xfail
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__active_since_in_past__fail(
    api_client, monkeypatch, mock_datetime_to_noon, r_cu, new_schedule_time_slot_data
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    active_since = system.get_now() - dt.timedelta(days=1)
    active_till = active_since + dt.timedelta(hours=3)
    data = new_schedule_time_slot_data(
        company=r_cu.company, active_since_local=active_since, active_till_local=active_till
    )
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == {"non_field_errors": [ACTIVE_SINCE_MUST_NOT_BE_IN_PAST]}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__active_till__than__active_since__fail(api_client, monkeypatch, r_cu, new_schedule_time_slot_data):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])

    active_since = system.get_now() + dt.timedelta(days=1)
    active_till = active_since - dt.timedelta(seconds=1)
    data = new_schedule_time_slot_data(
        company=r_cu.company, active_since_local=active_since, active_till_local=active_till
    )
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == [
        ACTIVE_SINCE_LOCAL_TIME_MUST_BE_BEFORE_LOCAL_ACTIVE_TILL_LOCAL_TIME
    ], f"response.data = {response.data}"


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__start_of_current_day__success(api_client, monkeypatch, r_cu, new_schedule_time_slot_data):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    active_since_local = system.get_now().replace(hour=00, minute=00, second=00, microsecond=00)
    data = new_schedule_time_slot_data(company=r_cu.company, active_since_local=active_since_local)
    response = __get_response(api_client, data=data, user=r_cu.user)
    assert ScheduleTimeSlot.objects.filter(id=response.data["id"]).exists()


@pytest.mark.xfail
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__earlier_than_start_of_current_data__fail(
    api_client, monkeypatch, r_cu, new_schedule_time_slot_data
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])

    active_since_local = system.get_now().replace(
        hour=00, minute=00, second=00, microsecond=00
    ) - timezone.timedelta(minutes=2)

    data = new_schedule_time_slot_data(company=r_cu.company, active_since_local=active_since_local)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == {"non_field_errors": [ACTIVE_SINCE_MUST_NOT_BE_IN_PAST]}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(api_client, monkeypatch, r_cu, new_schedule_time_slot_data):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])

    data = new_schedule_time_slot_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instance = ScheduleTimeSlot.objects.get(**data)
    response_instance = response.data
    assert response_instance.pop("id") == created_instance.id
    assert response_instance.pop("geo_point") == {"id": created_instance.geo_point.id}
    assert response_instance.pop("project_scheme") == {
        "id": created_instance.project_scheme.id,
        "color": created_instance.project_scheme.color,
        "title": created_instance.project_scheme.title,
    }
    assert response_instance.pop("reward") == created_instance.reward
    assert response_instance.pop("active_since")
    assert response_instance.pop("active_since_local")
    assert response_instance.pop("active_till")
    assert response_instance.pop("active_till_local")
    assert response_instance.pop("max_reports_qty") == created_instance.max_reports_qty
    assert response_instance.pop("created_at")
    assert response_instance.pop("updated_at")
    assert not response_instance
