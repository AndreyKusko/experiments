import pytest
from rest_framework.exceptions import NotFound

from ma_saas.constants.report import ProcessedReportStatus
from ma_saas.constants.company import CUR, CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from clients.policies.interface import Policies
from reports.models.processed_report import ProcessedReport
from tests.test_app_reports.test_processed_reports.test_update.test_common import __get_response


@pytest.mark.parametrize(
    ("current_status", "target_status"),
    (
        (ProcessedReportStatus.CREATED, ProcessedReportStatus.CREATED),
        (ProcessedReportStatus.CREATED, ProcessedReportStatus.ACCEPTED),
        (ProcessedReportStatus.CREATED, ProcessedReportStatus.DECLINED),
        (ProcessedReportStatus.ACCEPTED, ProcessedReportStatus.ACCEPTED),
        (ProcessedReportStatus.DECLINED, ProcessedReportStatus.DECLINED),
    ),
)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__manager_status_update____success(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_fi,
    current_status,
    target_status,
    get_project_territory_fi,
):
    pt = get_project_territory_fi(company=r_cu.company)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [pt.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_processed_report_fi(company_user=r_cu, project_territory=pt, status=current_status.value)
    data = {"status": target_status.value}
    response = __get_response(api_client, instance.id, data, r_cu.user)
    updated_instance = ProcessedReport.objects.get(id=instance.id)
    assert response.data["status"] == target_status.value
    assert updated_instance.status == target_status.value


@pytest.mark.parametrize(
    ("current_status", "target_status"),
    (
        (ProcessedReportStatus.CREATED, ProcessedReportStatus.CREATED),
        (ProcessedReportStatus.CREATED, ProcessedReportStatus.ACCEPTED),
        (ProcessedReportStatus.CREATED, ProcessedReportStatus.DECLINED),
        (ProcessedReportStatus.ACCEPTED, ProcessedReportStatus.ACCEPTED),
        (ProcessedReportStatus.DECLINED, ProcessedReportStatus.DECLINED),
    ),
)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__any__manager_status_update__with_policy__success(
    api_client,
    monkeypatch,
    get_processed_report_fi,
    r_cu,
    current_status,
    target_status,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_processed_report_fi(company_user=r_cu, status=current_status.value)
    response = __get_response(api_client, instance.id, {"status": target_status.value}, r_cu.user)
    updated_instance = ProcessedReport.objects.get(id=instance.id)
    assert response.data["status"] == target_status.value
    assert updated_instance.status == target_status.value


@pytest.mark.parametrize(
    ("current_status", "target_status"),
    (
        (ProcessedReportStatus.CREATED, ProcessedReportStatus.CREATED),
        (ProcessedReportStatus.CREATED, ProcessedReportStatus.ACCEPTED),
        (ProcessedReportStatus.CREATED, ProcessedReportStatus.DECLINED),
        (ProcessedReportStatus.ACCEPTED, ProcessedReportStatus.ACCEPTED),
        (ProcessedReportStatus.DECLINED, ProcessedReportStatus.DECLINED),
    ),
)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__any_manager_status_update__without_policy__fail(
    api_client,
    mock_policies_false,
    get_processed_report_fi,
    r_cu,
    current_status,
    target_status,
):
    instance = get_processed_report_fi(company_user=r_cu, status=current_status.value)
    data = {"status": target_status.value}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize(
    ("current_status", "target_status"),
    (
        (ProcessedReportStatus.CREATED, ProcessedReportStatus.CREATED),
        (ProcessedReportStatus.CREATED, ProcessedReportStatus.ACCEPTED),
        (ProcessedReportStatus.CREATED, ProcessedReportStatus.DECLINED),
        (ProcessedReportStatus.ACCEPTED, ProcessedReportStatus.ACCEPTED),
        (ProcessedReportStatus.DECLINED, ProcessedReportStatus.DECLINED),
    ),
)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__owner_status_update__success(
    api_client,
    mock_policies_false,
    r_cu,
    get_cu_manager_fi,
    get_project_territory_fi,
    get_processed_report_fi,
    current_status,
    target_status,
):
    cu_manager = get_cu_manager_fi(company=r_cu.company)
    pt = get_project_territory_fi(company=r_cu.company)
    instance = get_processed_report_fi(
        company_user=cu_manager, project_territory=pt, status=current_status.value
    )
    response = __get_response(api_client, instance.id, {"status": target_status.value}, r_cu.user)
    updated_instance = ProcessedReport.objects.get(id=instance.id)
    assert response.data["status"] == target_status.value
    assert updated_instance.status == target_status.value


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_manager__fail(
    api_client,
    monkeypatch,
    get_cu_manager_fi,
    get_project_territory_fi,
    get_processed_report_fi,
    status,
):
    r_cu = get_cu_manager_fi(status=status)
    pt = get_project_territory_fi(company=r_cu.company)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    old_status, new_status = ProcessedReportStatus.CREATED.value, ProcessedReportStatus.ACCEPTED.value
    instance = get_processed_report_fi(company_user=r_cu, project_territory=pt, status=old_status)
    data = {"status": new_status}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("cu_manager", [pytest.lazy_fixture("cu_manager_fi")])
def test__different_company_user__fail(
    api_client, monkeypatch, r_cu, cu_manager, get_processed_report_fi, get_project_territory_fi
):

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    instance = get_processed_report_fi(
        company_user=cu_manager, project_territory=pt, status=ProcessedReportStatus.CREATED.value
    )
    data = {"status": ProcessedReportStatus.ACCEPTED.value}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__contractor_not_accepted_owner__fail(
    api_client,
    monkeypatch,
    get_cu_owner_fi,
    get_cu_manager_fi,
    get_project_territory_fi,
    get_processed_report_fi,
    status,
):
    r_cu = get_cu_owner_fi(status=status)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    cu_manager = get_cu_manager_fi(company=r_cu.company)
    pt = get_project_territory_fi(company=r_cu.company)

    old_status, new_status = ProcessedReportStatus.CREATED.value, ProcessedReportStatus.ACCEPTED.value
    instance = get_processed_report_fi(company_user=cu_manager, project_territory=pt, status=old_status)
    data = {"status": new_status}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_related__fail(
    api_client,
    monkeypatch,
    get_cu_fi,
    get_cu_manager_fi,
    get_processed_report_fi,
    role,
):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    cu_manager = get_cu_manager_fi()

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [cu_manager.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_processed_report_fi(company_user=cu_manager, status=ProcessedReportStatus.CREATED.value)
    data = {"status": ProcessedReportStatus.ACCEPTED.value}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}
