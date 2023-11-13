import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_create
from accounts.models import (
    USER_IS_BLOCKED,
    NOT_TA_USER_REASON,
    NOT_TA_R_U__DELETED,
    NOT_TA_REQUESTING_USER_REASON,
)
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from companies.models.company import COMPANY_IS_DELETED, NOT_TA_COMPANY_REASON
from tasks.models.reservation import (
    UNIQ_CONSTRAINT_ERR,
    PROJECT_TERRITORY__OF_GEO_POINT__AND_PT_WORKER__MUST_BE_SAME,
    Reservation,
)
from ma_saas.constants.company import CUR, CompanyUserStatus
from clients.policies.interface import Policies
from companies.models.company_user import (
    CU_IS_DELETED,
    NOT_TA_RCU_REASON,
    NOT_TA_COMPANY_USER_REASON,
    CompanyUser,
)
from projects.models.project_territory import NOT_TA_PT_REASON, NOT_TA_ACTIVE_PT_IS_DELETED
from projects.models.contractor_project_territory_worker import NOT_TA_PT_WORKER_REASON

User = get_user_model()

RESERVATION_AND_TASK_CHECK_FIELDS_NAMES = ("id", "geo_point", "project_territory", "project_territory_worker")


__get_response = functools.partial(request_response_create, path="/api/v1/reservations/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, data={}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policy_true, r_cu, new_reservation_data):
    mock_policy_true(r_cu.company)
    data = new_reservation_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user)
    assert Reservation.objects.filter(id=response.data["id"]).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__duplicates__fail(
    api_client, mock_policy_true, r_cu, get_schedule_time_slot_fi, new_reservation_data, get_reservation_fi
):
    mock_policy_true(r_cu.company)
    sts = get_schedule_time_slot_fi(company=r_cu.company)
    duplicate_data = new_reservation_data(schedule_time_slot=sts, _is_relations_ids=False)
    duplicate = get_reservation_fi(**duplicate_data)
    data = new_reservation_data(**duplicate_data)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == [
        UNIQ_CONSTRAINT_ERR.format(
            schedule_time_slot=duplicate.schedule_time_slot.id,
            project_territory_worker=duplicate.project_territory_worker.id,
        )
    ]
    assert (
        Reservation.objects.filter(
            schedule_time_slot=duplicate.schedule_time_slot,
            project_territory_worker=duplicate.project_territory_worker,
        ).count()
        == 1
    )


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__related_manager__success(
    api_client, monkeypatch, r_cu, new_reservation_data, get_project_territory_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    pt = get_project_territory_fi(company=r_cu.company)
    data = new_reservation_data(project_territory=pt)
    response = __get_response(api_client, data=data, user=r_cu.user)
    assert Reservation.objects.filter(id=response.data["id"]).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__with_worker__success(api_client, monkeypatch, r_cu, new_reservation_data, get_pt_worker_fi):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    pt_worker = get_pt_worker_fi(company=r_cu.company)
    data = new_reservation_data(project_territory=pt_worker.project_territory)
    response = __get_response(api_client, data, user=pt_worker.company_user.user)
    assert Reservation.objects.filter(id=response.data["id"]).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__worker_from_different_company__fail(
    api_client, monkeypatch, r_cu, get_cu_fi, new_reservation_data, get_project_territory_fi, get_pt_worker_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    target_cu = get_cu_fi(status=CompanyUserStatus.ACCEPT.value, role=CUR.WORKER)
    pt = get_project_territory_fi(company=target_cu.company)
    project_territory_worker = get_pt_worker_fi(project_territory=pt, company_user=target_cu)
    data = new_reservation_data(project_territory_worker=project_territory_worker)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__appoint_worker_not_appointed_to_pt__fail(
    api_client, monkeypatch, r_cu, new_reservation_data, get_geo_point_fi, get_pt_worker_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    company = r_cu.company
    geo_point = get_geo_point_fi(company=company)
    pt_worker = get_pt_worker_fi(company=company)
    data = new_reservation_data(company=company, geo_point=geo_point, project_territory_worker=pt_worker)
    response = __get_response(api_client, data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == [PROJECT_TERRITORY__OF_GEO_POINT__AND_PT_WORKER__MUST_BE_SAME]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("is_user", "field", "err_text"),
    (
        (True, "is_blocked", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_BLOCKED)),
        (True, "is_deleted", NOT_TA_R_U__DELETED),
        (False, "is_deleted", REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY),
    ),
)
@pytest.mark.parametrize("has_object_policy", [True, False])
def test__not_ta__cu__fail(
    api_client, monkeypatch, r_cu, new_reservation_data, has_object_policy, is_user, field, err_text
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    data = new_reservation_data(company=r_cu.company)
    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()
    else:
        setattr(r_cu, field, True)
        r_cu.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": err_text}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_company__fail(api_client, r_cu, new_reservation_data):
    data = new_reservation_data(company=r_cu.company)
    r_cu.company.is_deleted = True
    r_cu.company.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": NOT_TA_RCU_REASON.format(reason=NOT_TA_COMPANY_REASON.format(reason=COMPANY_IS_DELETED))
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__blocked_target_user__fail(
    api_client, mock_policy_true, r_cu, get_pt_worker_fi, new_reservation_data
):
    mock_policy_true(r_cu.company)
    target_pt_worker = get_pt_worker_fi(company=r_cu.company)
    data = new_reservation_data(project_territory_worker=target_pt_worker)
    target_pt_worker.company_user.user.is_blocked = True
    target_pt_worker.company_user.user.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": NOT_TA_PT_WORKER_REASON.format(
            reason=NOT_TA_COMPANY_USER_REASON.format(reason=NOT_TA_USER_REASON.format(reason=USER_IS_BLOCKED))
        )
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_target_user__fail(
    api_client, mock_policy_true, r_cu, new_reservation_data, get_pt_worker_fi
):
    mock_policy_true(r_cu.company)
    target_pt_worker = get_pt_worker_fi(company=r_cu.company)
    data = new_reservation_data(project_territory_worker=target_pt_worker)
    target_pt_worker.company_user.user.is_deleted = True
    target_pt_worker.company_user.user.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": NOT_TA_PT_WORKER_REASON.format(
            reason=NOT_TA_COMPANY_USER_REASON.format(reason=NOT_TA_R_U__DELETED)
        )
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_target_cu__fail(api_client, monkeypatch, r_cu, new_reservation_data, get_pt_worker_fi):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    target_pt_worker = get_pt_worker_fi(company=r_cu.company)
    data = new_reservation_data(project_territory_worker=target_pt_worker)
    target_pt_worker.company_user.is_deleted = True
    target_pt_worker.company_user.save()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": NOT_TA_PT_WORKER_REASON.format(
            reason=NOT_TA_COMPANY_USER_REASON.format(reason=CU_IS_DELETED)
        )
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_target_company__fail(api_client, r_cu, new_reservation_data, get_pt_worker_fi):
    target_pt_worker = get_pt_worker_fi(company=r_cu.company)
    data = new_reservation_data(project_territory_worker=target_pt_worker)
    target_pt_worker.company_user.company.is_deleted = True
    target_pt_worker.company_user.company.save()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": NOT_TA_RCU_REASON.format(reason=NOT_TA_COMPANY_REASON.format(reason=COMPANY_IS_DELETED))
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__target_pt_deleted__fail(api_client, mock_policy_true, r_cu, new_reservation_data, get_pt_worker_fi):
    mock_policy_true(r_cu.company)
    target_pt_worker = get_pt_worker_fi(company=r_cu.company)
    data = new_reservation_data(project_territory_worker=target_pt_worker)
    target_pt_worker.project_territory.is_deleted = True
    target_pt_worker.project_territory.save()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": NOT_TA_PT_WORKER_REASON.format(
            reason=NOT_TA_PT_REASON.format(reason=NOT_TA_ACTIVE_PT_IS_DELETED)
        )
    }
