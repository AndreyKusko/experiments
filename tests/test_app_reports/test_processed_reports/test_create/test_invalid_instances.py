import pytest
from rest_framework.exceptions import NotFound, PermissionDenied

from accounts.models import USER_IS_BLOCKED, USER_IS_DELETED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from projects.models.project import PROJECT_IS_DELETED, NOT_TA_PROJECT_REASON, PROJECT_STATUS_MUST_BE_ACTIVE
from companies.models.company import COMPANY_IS_DELETED, NOT_TA_COMPANY_REASON
from ma_saas.constants.report import WorkerReportStatus
from ma_saas.constants.project import NOT_ACTIVE_OR_SETUP_PROJECT_STATUS_VALUES
from clients.policies.interface import Policies
from reports.models.worker_report import NOT_TA_WORKER_REPORT_REASON
from companies.models.company_user import NOT_TA_RCU_REASON, CompanyUser
from projects.models.project_scheme import NOT_TA_PROJECT_SCHEME_REASON
from tests.test_app_reports.test_processed_reports.test_create.test_common import __get_response


@pytest.mark.parametrize("project_status", NOT_ACTIVE_OR_SETUP_PROJECT_STATUS_VALUES)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__not_active_or_setup_project__fail(
    api_client, r_cu, new_processed_report_data_fi, project_status, get_project_territory_fi
):
    pt = get_project_territory_fi(company=r_cu.company)
    data = new_processed_report_data_fi(project_territory=pt)
    pt.project.status = project_status
    pt.project.save()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PROJECT_STATUS_MUST_BE_ACTIVE}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__blocked_user__fail(api_client, r_cu, get_project_territory_fi, new_processed_report_data_fi):
    pt = get_project_territory_fi(company=r_cu.company)
    data = new_processed_report_data_fi(project_territory=pt)
    r_cu.user.is_blocked = True
    r_cu.user.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)

    assert response.data == {"detail": NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_BLOCKED)}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__deleted_user__fail(api_client, r_cu, get_project_territory_fi, new_processed_report_data_fi):
    pt = get_project_territory_fi(company=r_cu.company)
    data = new_processed_report_data_fi(project_territory=pt)
    r_cu.user.is_deleted = True
    r_cu.user.save()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_DELETED)}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__deleted_r_cu__fail(
    api_client, monkeypatch, r_cu, new_processed_report_data_fi, get_project_territory_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    pt = get_project_territory_fi(company=r_cu.company)
    data = new_processed_report_data_fi(project_territory=pt)

    r_cu.is_deleted = True
    r_cu.save()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__deleted_company__fail(api_client, r_cu, new_processed_report_data_fi, get_project_territory_fi):
    pt = get_project_territory_fi(company=r_cu.company)
    data = new_processed_report_data_fi(project_territory=pt)
    r_cu.company.is_deleted = True
    r_cu.company.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": NOT_TA_RCU_REASON.format(reason=NOT_TA_COMPANY_REASON.format(reason=COMPANY_IS_DELETED))
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__deleted_project__fail(api_client, r_cu, new_processed_report_data_fi, get_project_territory_fi):
    pt = get_project_territory_fi(company=r_cu.company)
    data = new_processed_report_data_fi(project_territory=pt)
    pt.project.is_deleted = True
    pt.project.save()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": "Отчет рабочего не активен. Причина: Схема проекта не активена. Причина: Проект не активен. Причина: Проект удален."
    }
    assert response.data == {
        "detail": NOT_TA_WORKER_REPORT_REASON.format(
            reason=NOT_TA_PROJECT_SCHEME_REASON.format(
                reason=NOT_TA_PROJECT_REASON.format(reason=PROJECT_IS_DELETED)
            )
        )
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__deleted_worker_report__fail(
    api_client,
    new_processed_report_data_fi,
    get_project_territory_fi,
    get_reservation_fi,
    get_schedule_time_slot_fi,
    get_worker_report_fi,
    r_cu,
):
    pt = get_project_territory_fi(company=r_cu.company)
    schedule_time_slot = get_schedule_time_slot_fi(project_territory=pt)
    reservation = get_reservation_fi(schedule_time_slot=schedule_time_slot)
    worker_report = get_worker_report_fi(
        project_territory_worker=reservation.project_territory_worker,
        schedule_time_slot=schedule_time_slot,
        status=WorkerReportStatus.ACCEPTED.value,
    )
    data = new_processed_report_data_fi(worker_report=worker_report)
    worker_report.is_deleted = True
    worker_report.save()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": "WorkerReport not found"}
