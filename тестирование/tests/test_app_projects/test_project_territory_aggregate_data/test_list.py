import functools

import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from tests.utils import request_response_list
from ma_saas.utils import system
from tests.constants import FAKE_TIME
from ma_saas.constants.system import DATETIME_FORMAT
from ma_saas.constants.company import CUR, CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from clients.policies.interface import Policies
from projects.views.project_territory_aggreate_data import REQUESTING_USER_CANT_ACCESS_REQUESTED_SCHEME

User = get_user_model()

__get_response = functools.partial(request_response_list, path="/api/v1/project-territory-aggregate-data/")


def test__anonymous_user__fail(api_client, get_project_fi, get_project_territory_fi):
    pt = get_project_territory_fi()
    now = FAKE_TIME
    time_query = dict(
        active_till_local=(now - timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
        active_since_local=(now + timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
    )
    pt_query = dict(project_territory__in=pt.id)
    response = __get_response(
        api_client,
        query_kwargs={**pt_query, **time_query},
        status_codes=NotAuthenticated,
    )
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__without_policies__success(
    api_client,
    mock_policies_false,
    r_cu,
    get_project_territory_fi,
    get_project_scheme_fi,
    get_schedule_time_slot_fi,
):
    pt = get_project_territory_fi(company=r_cu.company)

    scheme = get_project_scheme_fi(project=pt.project)
    scheme_query = dict(project_scheme=scheme.id)

    now = system.get_now()
    get_schedule_time_slot_fi(
        project_territory=pt,
        project_scheme=scheme,
        active_since_local=now,
        active_till_local=now + timezone.timedelta(minutes=1),
    )
    time_query = dict(
        active_since_local=(now - timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
        active_till_local=(now + timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
    )
    pt_query = dict(project_territory__in=pt.id)

    response = __get_response(
        api_client, query_kwargs={**scheme_query, **time_query, **pt_query}, user=r_cu.user
    )
    assert response.data


@pytest.mark.xfail
@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__with_polices__fail(
    api_client,
    monkeypatch,
    get_cu_fi,
    get_project_territory_fi,
    get_project_scheme_fi,
    get_schedule_time_slot_fi,
    status,
):
    r_cu = get_cu_fi(status=status, role=CUR.OWNER)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)

    scheme = get_project_scheme_fi(project=pt.project)
    scheme_query = dict(project_scheme=scheme.id)

    now = FAKE_TIME
    get_schedule_time_slot_fi(
        project_territory=pt,
        project_scheme=scheme,
        active_since_local=now,
        active_till_local=now + timezone.timedelta(minutes=1),
    )
    time_query = dict(
        active_since_local=(now - timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
        active_till_local=(now + timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
    )
    pt_query = dict(project_territory__in=pt.id)

    response = __get_response(
        api_client, query_kwargs={**scheme_query, **time_query, **pt_query}, user=r_cu.user
    )
    # тут пустая выдача потому что не дается значений, когда ничего нет
    assert response.data == {}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__any_not_owner_role__with_policy__success(
    api_client,
    monkeypatch,
    get_cu_fi,
    get_project_territory_fi,
    get_project_scheme_fi,
    get_schedule_time_slot_fi,
    role,
):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)

    scheme = get_project_scheme_fi(project=pt.project)
    scheme_query = dict(project_scheme=scheme.id)
    now = FAKE_TIME
    get_schedule_time_slot_fi(
        project_territory=pt,
        project_scheme=scheme,
        active_since_local=now,
        active_till_local=now + timezone.timedelta(minutes=1),
    )
    time_query = dict(
        active_since_local=(now - timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
        active_till_local=(now + timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
    )
    pt_query = dict(project_territory__in=pt.id)

    response = __get_response(
        api_client, query_kwargs={**scheme_query, **time_query, **pt_query}, user=r_cu.user
    )
    # тут пустая выдача потому что не дается значений, когда ничего нет
    assert response.data == {
        pt.id: {
            f"{now.year}-{'{:02d}'.format(int(now.month))}-{'{:02d}'.format(int(now.day))}": {
                "schedule_time_slots_with_workers_qty": 0,
                "schedule_time_slots_without_workers_qty": 1,
                "worker_reports_qty": 0,
            }
        }
    }


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__any_not_owner_role__without_policy__fail(
    api_client,
    mock_policies_false,
    get_cu_fi,
    get_project_territory_fi,
    get_project_scheme_fi,
    get_schedule_time_slot_fi,
    role,
):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)

    pt = get_project_territory_fi(company=r_cu.company)
    scheme = get_project_scheme_fi(project=pt.project)
    scheme_query = dict(project_scheme=scheme.id)

    now = FAKE_TIME
    get_schedule_time_slot_fi(
        project_territory=pt,
        project_scheme=scheme,
        active_since_local=now - timezone.timedelta(hours=5),
        active_till_local=now + timezone.timedelta(hours=5),
    )
    time_query = dict(
        active_since_local=(now - timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
        active_till_local=(now + timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
    )
    pt_query = dict(project_territory__in=pt.id)
    response = __get_response(
        api_client,
        query_kwargs={**scheme_query, **time_query, **pt_query},
        user=r_cu.user,
        status_codes=PermissionDenied,
    )
    # тут пустая выдача потому что не дается значений, когда ничего нет
    assert response.data == {"detail": REQUESTING_USER_CANT_ACCESS_REQUESTED_SCHEME}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__with_scheme__response_data(
    api_client, monkeypatch, r_cu, get_project_territory_fi, get_project_scheme_fi, get_schedule_time_slot_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)

    scheme = get_project_scheme_fi(project=pt.project)
    scheme_query = dict(project_scheme=scheme.id)
    now = FAKE_TIME
    get_schedule_time_slot_fi(
        project_territory=pt,
        project_scheme=scheme,
        active_since_local=now,
        active_till_local=now + timezone.timedelta(minutes=1),
    )
    get_schedule_time_slot_fi(
        project_territory=pt, active_since_local=now, active_till_local=now + timezone.timedelta(minutes=1)
    )
    time_query = dict(
        active_since_local=(now - timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
        active_till_local=(now + timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
    )
    pt_query = dict(project_territory__in=pt.id)

    response = __get_response(
        api_client, query_kwargs={**scheme_query, **time_query, **pt_query}, user=r_cu.user
    )
    assert response.data == {
        pt.id: {
            f"{now.year}-{'{:02d}'.format(int(now.month))}-{'{:02d}'.format(int(now.day))}": {
                "schedule_time_slots_with_workers_qty": 0,
                "schedule_time_slots_without_workers_qty": 1,
                "worker_reports_qty": 0,
            }
        }
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__request_without_scheme__response_data(
    api_client, monkeypatch, r_cu, get_project_territory_fi, get_project_scheme_fi, get_schedule_time_slot_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    scheme = get_project_scheme_fi(project=pt.project)
    now = FAKE_TIME
    get_schedule_time_slot_fi(
        project_territory=pt,
        project_scheme=scheme,
        active_since_local=now,
        active_till_local=now + timezone.timedelta(minutes=1),
    )
    get_schedule_time_slot_fi(
        project_territory=pt, active_since_local=now, active_till_local=now + timezone.timedelta(minutes=1)
    )
    time_query = dict(
        active_since_local=(now - timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
        active_till_local=(now + timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
    )
    pt_query = dict(project_territory__in=pt.id)

    response = __get_response(api_client, query_kwargs={**time_query, **pt_query}, user=r_cu.user)
    assert response.data == {
        pt.id: {
            f"{now.year}-{'{:02d}'.format(int(now.month))}-{'{:02d}'.format(int(now.day))}": {
                "schedule_time_slots_with_workers_qty": 0,
                "schedule_time_slots_without_workers_qty": 2,
                "worker_reports_qty": 0,
            }
        }
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__request_with_scheme__response_data(
    api_client, monkeypatch, r_cu, get_project_territory_fi, get_project_scheme_fi, get_schedule_time_slot_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)

    scheme = get_project_scheme_fi(project=pt.project)

    now = FAKE_TIME
    get_schedule_time_slot_fi(
        project_territory=pt,
        project_scheme=scheme,
        active_since_local=now,
        active_till_local=now + timezone.timedelta(minutes=1),
    )
    get_schedule_time_slot_fi(
        project_territory=pt, active_since_local=now, active_till_local=now + timezone.timedelta(minutes=1)
    )
    time_query = dict(
        active_since_local=(now - timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
        active_till_local=(now + timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
    )
    pt_query = dict(project_territory__in=pt.id)
    scheme_query = dict(project_scheme=scheme.id)

    response = __get_response(
        api_client, query_kwargs={**time_query, **pt_query, **scheme_query}, user=r_cu.user
    )
    assert response.data == {
        pt.id: {
            f"{now.year}-{'{:02d}'.format(int(now.month))}-{'{:02d}'.format(int(now.day))}": {
                "schedule_time_slots_with_workers_qty": 0,
                "schedule_time_slots_without_workers_qty": 1,
                "worker_reports_qty": 0,
            }
        }
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("is_scheme", [True, False])
def test__without_workers__response_data(
    api_client,
    monkeypatch,
    r_cu,
    get_project_territory_fi,
    get_project_scheme_fi,
    get_schedule_time_slot_fi,
    is_scheme,
):

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)

    scheme = get_project_scheme_fi(project=pt.project)
    scheme_query = dict(project_scheme=scheme.id) if is_scheme else {}

    now = FAKE_TIME
    get_schedule_time_slot_fi(
        project_territory=pt,
        project_scheme=scheme,
        active_since_local=now,
        active_till_local=now + timezone.timedelta(minutes=1),
    )
    time_query = dict(
        active_since_local=(now - timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
        active_till_local=(now + timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
    )
    pt_query = dict(project_territory__in=pt.id)
    query_kwargs = {**scheme_query, **time_query, **pt_query}
    response = __get_response(api_client, query_kwargs=query_kwargs, user=r_cu.user)
    assert response.data == {
        pt.id: {
            f"{now.year}-{'{:02d}'.format(int(now.month))}-{'{:02d}'.format(int(now.day))}": {
                "schedule_time_slots_with_workers_qty": 0,
                "schedule_time_slots_without_workers_qty": 1,
                "worker_reports_qty": 0,
            }
        }
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("is_scheme", [True, False])
def test__with_workers__response_data(
    api_client,
    monkeypatch,
    r_cu,
    get_project_territory_fi,
    get_project_scheme_fi,
    get_schedule_time_slot_fi,
    get_reservation_fi,
    is_scheme,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)

    scheme = get_project_scheme_fi(project=pt.project)
    scheme_query = dict(project_scheme=scheme.id) if is_scheme else {}

    now = FAKE_TIME
    sts = get_schedule_time_slot_fi(
        project_territory=pt,
        project_scheme=scheme,
        active_since_local=now,
        active_till_local=now + timezone.timedelta(minutes=1),
    )
    get_reservation_fi(schedule_time_slot=sts)

    time_query = dict(
        active_since_local=(now - timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
        active_till_local=(now + timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
    )
    pt_query = dict(project_territory__in=pt.id)

    response = __get_response(
        api_client, query_kwargs={**scheme_query, **time_query, **pt_query}, user=r_cu.user
    )
    assert response.data == {
        pt.id: {
            f"{now.year}-{'{:02d}'.format(int(now.month))}-{'{:02d}'.format(int(now.day))}": {
                "schedule_time_slots_with_workers_qty": 1,
                "schedule_time_slots_without_workers_qty": 0,
                "worker_reports_qty": 0,
            }
        }
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("is_scheme", [True, False])
def test__worker_reports__response_data(
    api_client,
    monkeypatch,
    r_cu,
    get_project_territory_fi,
    get_project_scheme_fi,
    get_schedule_time_slot_fi,
    get_worker_report_fi,
    is_scheme,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)

    scheme = get_project_scheme_fi(project=pt.project)
    scheme_query = dict(project_scheme=scheme.id) if is_scheme else {}

    now = FAKE_TIME
    sts = get_schedule_time_slot_fi(
        project_territory=pt,
        project_scheme=scheme,
        active_since_local=now - timezone.timedelta(hours=5),
        active_till_local=now + timezone.timedelta(hours=5),
    )
    get_worker_report_fi(schedule_time_slot=sts)

    time_query = dict(
        active_since_local=(now - timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
        active_till_local=(now + timezone.timedelta(days=30)).strftime(DATETIME_FORMAT),
    )
    pt_query = dict(project_territory__in=pt.id)

    response = __get_response(
        api_client, query_kwargs={**scheme_query, **time_query, **pt_query}, user=r_cu.user
    )
    assert response.data == {
        pt.id: {
            f"{now.year}-{'{:02d}'.format(int(now.month))}-{'{:02d}'.format(int(now.day))}": {
                "schedule_time_slots_with_workers_qty": 1,
                "schedule_time_slots_without_workers_qty": 0,
                "worker_reports_qty": 1,
            }
        }
    }
