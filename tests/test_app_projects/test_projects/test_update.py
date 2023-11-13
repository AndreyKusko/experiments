import functools

import pytest
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework.exceptions import NotFound, ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_update, retrieve_response_instance
from accounts.models import USER_IS_BLOCKED, USER_IS_DELETED, NOT_TA_REQUESTING_USER_REASON
from geo_objects.models import GeoPoint
from projects.models.project import PROJECT_STATUS_MUST_BE_SETUP, Project
from ma_saas.constants.report import WorkerReportStatus, ProcessedReportStatus
from ma_saas.constants.system import DATETIME_FORMAT, Callable
from ma_saas.constants.company import CUR, CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from ma_saas.constants.project import ProjectStatus
from projects.validators.project import (
    PROJECT_GOT_NOT_MODERATED_REPORTS,
    PROJECT_SCHEMES_MUST_HAVE_SERVICE_NAME_FOR_RECEIPTS,
)
from reports.models.worker_report import WorkerReport
from companies.models.company_user import CompanyUser

User = get_user_model()

__get_response = functools.partial(request_response_update, path="/api/v1/projects/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("project_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, {}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_contractor_owner__fail(api_client, mock_policies_false, get_cu_fi, get_project_fi, role):

    company_user = get_cu_fi(status=CUS.ACCEPT.value, role=role)
    instance = get_project_fi(company=company_user.company)
    response = __get_response(api_client, instance.id, {}, company_user.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_client_owner__fail(api_client, mock_policies_false, get_cu_fi, get_project_fi, role):

    company_user = get_cu_fi(role=role)
    instance = get_project_fi(company=company_user.company, status=ProjectStatus.SETUP.value)
    response = __get_response(api_client, instance.id, {}, company_user.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_contractor_owner__fail(
    api_client, mock_policies_false, get_cu_fi, get_project_fi, status
):
    company_user = get_cu_fi(status=status.value, role=CUR.OWNER)
    project = get_project_fi(company=company_user.company, status=ProjectStatus.SETUP.value)
    response = __get_response(api_client, project.id, {}, company_user.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_client_owner__fail(api_client, mock_policies_false, get_cu_fi, get_project_fi, status):
    company_user = get_cu_fi(status=status.value, role=CUR.OWNER)
    project = get_project_fi(company=company_user.company, status=ProjectStatus.SETUP.value)
    response = __get_response(api_client, project.id, {}, company_user.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("status", [s.value for s in ProjectStatus if s != ProjectStatus.SETUP])
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__update_if_status_not_setup__fail(api_client, mock_policies_false, r_cu, get_project_fi, status):
    instance = get_project_fi(company=r_cu.company, status=status)
    data = {"status": status, "title": get_random_string()}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    assert response.data == [PROJECT_STATUS_MUST_BE_SETUP]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__update_if_status_setup__success(api_client, mock_policies_false, r_cu, get_project_fi):
    instance = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    response = __get_response(api_client, instance.id, data={}, user=r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(api_client, mock_policies_false, r_cu, get_project_fi, new_project_data):
    instance = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    data = new_project_data()
    del data["company"]
    response = __get_response(api_client, instance_id=instance.id, data=data, user=r_cu.user)
    updated_instance = Project.objects.get(id=instance.id)
    response_instance = response.data
    assert response_instance.pop("id") == updated_instance.id
    assert response_instance.pop("title") == updated_instance.title

    if response_company := retrieve_response_instance(response_instance, "company", dict):
        assert response_company.pop("id") == updated_instance.company.id == instance.company.id
    assert not response_company

    assert response_instance.pop("description") == updated_instance.description
    assert response_instance.pop("status") == updated_instance.status
    assert response_instance.pop("created_at") == updated_instance.created_at.strftime(DATETIME_FORMAT)
    assert response_instance.pop("updated_at") == updated_instance.updated_at.strftime(DATETIME_FORMAT)
    assert not response_instance


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("worker_reports_status", (WorkerReportStatus.PENDING, WorkerReportStatus.LOADED))
@pytest.mark.parametrize("target_project_status", (ProjectStatus.SETUP, ProjectStatus.ARCHIVED))
def test__if_not_moderated_worker_reports__status_conversion__fail(
    api_client,
    monkeypatch,
    mock_policies_false,
    r_cu,
    get_project_fi,
    get_worker_report_fi: Callable,
    get_project_territory_fi: Callable,
    worker_reports_status,
    target_project_status,
):
    monkeypatch.setattr(GeoPoint, "set_utc_offset", lambda *a, **kw: 1)
    monkeypatch.setattr(WorkerReport, "check_if_reports_not_exceed_and_interval_qty", lambda *a, **kw: None)

    instance = get_project_fi(company=r_cu.company, status=ProjectStatus.ACTIVE.value)
    project_territory = get_project_territory_fi(project=instance)

    _fd_worker_report = dict(project_territory=project_territory, status=worker_reports_status.value)
    worker_report = get_worker_report_fi(**_fd_worker_report)

    data = {"status": target_project_status.value}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    assert response.data[0] == PROJECT_GOT_NOT_MODERATED_REPORTS.format(worker_reports=f"{worker_report.id}")


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("target_project_status", (ProjectStatus.SETUP, ProjectStatus.ARCHIVED))
def test__if_not_moderated_processed_reports__status_conversion__success(
    api_client,
    monkeypatch,
    mock_policies_false,
    r_cu,
    get_project_fi,
    get_worker_report_fi: Callable,
    get_processed_report_fi,
    get_project_territory_fi: Callable,
    target_project_status,
):

    monkeypatch.setattr(GeoPoint, "set_utc_offset", lambda *a, **kw: 1)
    monkeypatch.setattr(WorkerReport, "check_if_reports_not_exceed_and_interval_qty", lambda *a, **kw: None)

    instance = get_project_fi(company=r_cu.company, status=ProjectStatus.ACTIVE.value)
    project_territory = get_project_territory_fi(project=instance)

    _fd_worker_report = dict(project_territory=project_territory, status=WorkerReportStatus.ACCEPTED)
    worker_report = get_worker_report_fi(**_fd_worker_report)
    _fd_processed_report = dict(
        project_territory=project_territory, status=ProcessedReportStatus.CREATED.value
    )
    get_processed_report_fi(**_fd_processed_report, worker_report=worker_report)

    data = {"status": target_project_status.value}
    response = __get_response(api_client, instance.id, data, user=r_cu.user)
    assert response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("target_project_status", (ProjectStatus.SETUP, ProjectStatus.ARCHIVED))
@pytest.mark.parametrize("target_processed_report_status", ProcessedReportStatus)
@pytest.mark.parametrize(
    "target_worker_report_status", (WorkerReportStatus.PENDING, WorkerReportStatus.LOADED)
)
def test__if_not_moderated_worker_reports__with_processed_report__status_conversion__success(
    api_client,
    monkeypatch,
    mock_policies_false,
    r_cu,
    get_project_fi,
    get_worker_report_fi,
    get_processed_report_fi,
    get_project_territory_fi,
    target_project_status,
    target_processed_report_status,
    target_worker_report_status,
):

    monkeypatch.setattr(GeoPoint, "set_utc_offset", lambda *a, **kw: 1)
    monkeypatch.setattr(WorkerReport, "check_if_reports_not_exceed_and_interval_qty", lambda *a, **kw: None)

    instance = get_project_fi(company=r_cu.company, status=ProjectStatus.ACTIVE.value)
    project_territory = get_project_territory_fi(project=instance)

    _fd_worker_report = dict(project_territory=project_territory, status=target_worker_report_status.value)
    worker_report = get_worker_report_fi(**_fd_worker_report)
    _fd_processed_report = dict(
        project_territory=project_territory, status=target_processed_report_status.value
    )
    get_processed_report_fi(**_fd_processed_report, worker_report=worker_report)

    data = {"status": target_project_status.value}
    response = __get_response(api_client, instance.id, data, user=r_cu.user)
    assert response.data


@pytest.mark.parametrize("worker_reports_qty", (0, 1))
@pytest.mark.parametrize("processed_reports_qty", (0, 1))
@pytest.mark.parametrize("worker_reports_status", (WorkerReportStatus.ACCEPTED, WorkerReportStatus.DECLINED))
@pytest.mark.parametrize(
    "processed_reports_status", (ProcessedReportStatus.ACCEPTED, ProcessedReportStatus.DECLINED)
)
@pytest.mark.parametrize(
    "target_project_status", (ProjectStatus.SETUP, ProjectStatus.ACTIVE, ProjectStatus.ARCHIVED)
)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__if_all_reports_were_moderated__status_conversion__success(
    api_client,
    monkeypatch,
    mock_policies_false,
    r_cu,
    get_project_fi,
    get_worker_report_fi: Callable,
    get_processed_report_fi,
    get_project_territory_fi: Callable,
    worker_reports_qty,
    processed_reports_qty,
    worker_reports_status,
    processed_reports_status,
    target_project_status,
):

    monkeypatch.setattr(GeoPoint, "set_utc_offset", lambda *a, **kw: 1)
    monkeypatch.setattr(WorkerReport, "check_if_reports_not_exceed_and_interval_qty", lambda *a, **kw: None)

    if not worker_reports_qty and not processed_reports_qty:
        return
    instance = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    project_territory = get_project_territory_fi(project=instance)

    _fd_worker_report = dict(project_territory=project_territory, status=worker_reports_status.value)
    [get_worker_report_fi(**_fd_worker_report) for _ in range(worker_reports_qty)]

    _fd_processed_report = dict(project_territory=project_territory, status=processed_reports_status.value)
    [get_processed_report_fi(**_fd_processed_report) for _ in range(processed_reports_qty)]
    response = __get_response(
        api_client, instance.id, {"status": target_project_status.value}, user=r_cu.user
    )
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("current_status", "target_status"),
    (
        (ProjectStatus.SETUP, ProjectStatus.SETUP),
        (ProjectStatus.SETUP, ProjectStatus.ACTIVE),
        (ProjectStatus.SETUP, ProjectStatus.ARCHIVED),
        (ProjectStatus.ACTIVE, ProjectStatus.ACTIVE),
        (ProjectStatus.ACTIVE, ProjectStatus.ARCHIVED),
        (ProjectStatus.ACTIVE, ProjectStatus.SETUP),
        (ProjectStatus.ARCHIVED, ProjectStatus.ARCHIVED),
        (ProjectStatus.ARCHIVED, ProjectStatus.ACTIVE),
        (ProjectStatus.ARCHIVED, ProjectStatus.SETUP),
    ),
)
def test__accepted_owner__success(
    api_client, mock_policies_false, r_cu, get_project_fi, current_status, target_status
):
    instance = get_project_fi(company=r_cu.company, status=current_status.value)
    response = __get_response(api_client, instance.id, {"status": target_status.value}, user=r_cu.user)
    assert response.data["id"] == instance.id
    assert response.data["status"] == target_status.value


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__blocked_user__fail(api_client, mock_policies_false, r_cu, get_project_fi):

    instance = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    r_cu.user.is_blocked = True
    r_cu.user.save()
    response = __get_response(api_client, instance.id, {}, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_BLOCKED)}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_user__fail(api_client, mock_policies_false, r_cu, get_project_fi):
    instance = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    r_cu.user.is_deleted = True
    r_cu.user.save()
    response = __get_response(api_client, instance.id, {}, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_DELETED)}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_cu__fail(api_client, monkeypatch, mock_policies_false, r_cu, get_project_fi):

    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    instance = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    r_cu.is_deleted = True
    r_cu.save()
    response = __get_response(api_client, instance.id, {}, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_project__fail(api_client, mock_policies_false, r_cu, get_project_fi):
    instance = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance.is_deleted = True
    instance.save()
    response = __get_response(api_client, instance.id, {}, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__set_status_to_active__if_project_schemes_without__service_name_for_receipt__fail(
    api_client, mock_policies_false, r_cu, get_project_fi, get_project_scheme_fi
):
    current_status, target_status = ProjectStatus.SETUP, ProjectStatus.ACTIVE
    instance = get_project_fi(company=r_cu.company, status=current_status.value)
    get_project_scheme_fi(project=instance, service_name_for_receipt="")
    data = {"status": target_status.value}
    response = __get_response(api_client, instance.id, data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == [PROJECT_SCHEMES_MUST_HAVE_SERVICE_NAME_FOR_RECEIPTS]
