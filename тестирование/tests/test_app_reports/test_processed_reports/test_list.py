import functools

import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated

from tests.utils import request_response_list
from ma_saas.constants.report import NOT_ACCEPTED_PROCESSED_REPORT_STATUSES_VALUES, ProcessedReportStatus
from ma_saas.constants.system import Callable
from ma_saas.constants.company import CUR, NOT_ACCEPT_CUS
from companies.models.company_user import CompanyUser
from projects.models.contractor_project_territory_manager import ContractorProjectTerritoryManager
from tests.test_app_reports.test_processed_reports.constants import PROCESSED_REPORTS_PATH

User = get_user_model()


__get_response = functools.partial(request_response_list, path=PROCESSED_REPORTS_PATH)


def test__anonymous_user__unauthorised(api_client):
    response = __get_response(api_client, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


def test__user_without_companies_got_nothing(api_client, user_fi: User):
    response = __get_response(api_client, user=user_fi)
    assert not response.data


@pytest.mark.parametrize("qty", (0, 1, 3))
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__contractor__manager_model_owner__success(
    api_client, r_cu, get_processed_report_fi, get_project_territory_fi, qty: int
):
    pt = get_project_territory_fi(company=r_cu.company)
    [get_processed_report_fi(company_user=r_cu, project_territory=pt) for _ in range(qty)]
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == qty


@pytest.mark.parametrize("qty", (0, 1, 3))
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__contractor__manager__success(
    api_client,
    r_cu,
    get_processed_report_fi,
    qty: int,
    get_project_territory_fi,
):
    pt = get_project_territory_fi(company=r_cu.company)
    [get_processed_report_fi(project_territory=pt) for _ in range(qty)]
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == qty


@pytest.mark.parametrize("qty", (1, 3))
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__client_project_manager_accepted_report__success(
    api_client,
    get_client_project_manager_fi: Callable,
    get_project_territory_fi: Callable,
    r_cu: CompanyUser,
    get_project_fi,
    get_processed_report_fi,
    qty,
):
    project = get_project_fi(company=r_cu.company)
    requesting_project_manager = get_client_project_manager_fi(project=project, company_user=r_cu)
    pt = get_project_territory_fi(project=project)
    [
        get_processed_report_fi(project_territory=pt, status=ProcessedReportStatus.ACCEPTED.value)
        for _ in range(qty)
    ]
    response = __get_response(api_client, user=requesting_project_manager.company_user.user)
    assert len(response.data) == qty


#
# @pytest.mark.parametrize("qty", (1, 3))
# @pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
# @pytest.mark.parametrize("invited_company_status", NOT_ACCEPT_PROJECT_partner_status_VALUES)
# def test__client_project_manager_not_accept_project_partner_status__fail(
#     api_client,
#     get_client_project_manager_fi: Callable,
#     get_project_territory_fi: Callable,
#     get_company_fi,
#     r_cu: CompanyUser,
#         get_project_fi,
#     get_processed_report_fi: Callable,
#     qty,
#     partner_status,
# ):
#     company = get_company_fi(kind=CompanyKind.CONTRACTOR.value)
#     project = get_project_fi(
#         company=company, company=r_cu.company, partner_status=partner_status,
#     )
#     requesting_project_manager = get_client_project_manager_fi(project=project, company_user=r_cu)
#     pt = get_project_territory_fi(project=project)
#     [
#         get_processed_report_fi(project_territory=pt, status=ManagerReportStatus.ACCEPTED.value)
#         for _ in range(qty)
#     ]
#     response = __get_response(
#         api_client,
#         user=requesting_project_manager.company_user.user,
#         status_codes=status_code.HTTP_200_OK,
#     )
#     assert len(response.data) == 0
#
#
#
# @pytest.mark.parametrize("qty", (1, 3))
# @pytest.mark.parametrize("report_status", NOT_ACCEPTED_PROCESSED_REPORT_STATUSES_VALUES)
# @pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
# def test__client_project_manager_accepted_report__not_display(
#     api_client,
#     get_client_project_manager_fi: Callable,
#     get_project_territory_fi: Callable,
#     get_company_fi,
#     r_cu: CompanyUser,
#         get_project_fi,
#     get_processed_report_fi: Callable,
#     qty,
#     report_status,
# ):
#     company = get_company_fi(kind=CompanyKind.CONTRACTOR.value)
#     project = get_project_fi(company=company, company=r_cu.company)
#     get_client_project_manager_fi(project=project, company_user=r_cu)
#     pt = get_project_territory_fi(project=project)
#     [get_processed_report_fi(project_territory=pt, status=report_status) for _ in range(qty)]
#     response = __get_response(
#         api_client, user=r_cu.user, status_codes=status_code.HTTP_200_OK,
#     )
#     assert not response.data


@pytest.mark.parametrize("qty", (0, 1, 3))
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(
    api_client,
    mock_policies_false,
    r_cu,
    get_project_territory_fi,
    get_processed_report_fi,
    qty,
):
    pt = get_project_territory_fi(company=r_cu)
    [get_processed_report_fi(company_user=r_cu, project_territory=pt) for _ in range(qty)]
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == qty


@pytest.mark.parametrize("qty", (1, 3))
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("cu_manager", [pytest.lazy_fixture("cu_manager_fi")])
def test__client_owner_accepted_report__success(
    api_client,
    r_cu,
    cu_manager,
    get_processed_report_fi,
    get_project_territory_fi,
    qty,
):
    pt = get_project_territory_fi(company=r_cu.comapny)
    s = ProcessedReportStatus.ACCEPTED.value
    [get_processed_report_fi(company_user=cu_manager, project_territory=pt, status=s) for _ in range(qty)]
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == qty


@pytest.mark.parametrize("qty", (1, 3))
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__client_owner__project_not_accept_partner_status__empty_response(
    api_client,
    r_cu,
    get_cu_manager_fi,
    get_processed_report_fi,
    get_project_territory_fi,
    get_company_fi,
    qty,
):
    company = r_cu.company
    pt = get_project_territory_fi(company=company)
    manager_cu = get_cu_manager_fi(company=company)
    s = ProcessedReportStatus.ACCEPTED.value
    [get_processed_report_fi(company_user=manager_cu, project_territory=pt, status=s) for _ in range(qty)]

    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == 0


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("report_status", NOT_ACCEPTED_PROCESSED_REPORT_STATUSES_VALUES)
def test__client_owner_not_accepted_report__not_display(
    api_client,
    r_cu: CompanyUser,
    get_processed_report_fi,
    get_project_territory_fi,
    report_status,
):
    pt = get_project_territory_fi(company=r_cu.company)
    get_processed_report_fi(project_territory=pt, status=report_status)
    response = __get_response(api_client, user=r_cu.user)
    assert not response.data


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__contractor_not_accepted_owner__not_display(
    api_client,
    get_cu_fi,
    get_processed_report_fi,
    get_project_territory_fi,
    status,
):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status)
    pt = get_project_territory_fi(company=r_cu.company)
    get_processed_report_fi(project_territory=pt)
    response = __get_response(api_client, user=r_cu.user)
    assert not response.data


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__client_not_accepted_owner__not_display(
    api_client,
    get_cu_fi,
    get_processed_report_fi,
    get_project_fi,
    get_project_territory_fi: Callable,
    get_company_fi,
    status,
):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status)
    project = get_project_fi(company=r_cu.company)
    pt = get_project_territory_fi(project=project)
    get_processed_report_fi(project_territory=pt)
    response = __get_response(api_client, user=r_cu.user)
    assert not response.data


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__contractor_not_related_project_manager__fail(
    api_client,
    get_cu_fi,
    get_project_territory_fi,
    get_processed_report_fi,
    get_project_fi,
    get_company_fi,
    status,
):
    r_cu = get_cu_fi(role=CUR.PROJECT_MANAGER, status=status)
    pt = get_project_territory_fi(company=r_cu.company)
    get_processed_report_fi(project_territory=pt)
    response = __get_response(api_client, user=r_cu.user)
    assert not response.data


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__contractor_not_accepted__manager__fail(api_client, get_cu_fi, get_processed_report_fi, status):
    r_cu = get_cu_fi(role=CUR.PROJECT_MANAGER, status=status)
    get_processed_report_fi(company=r_cu.company)
    response = __get_response(api_client, user=r_cu.user)
    assert not response.data


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__client_not_accepted_project_manager__fail(
    api_client,
    r_cu,
    get_client_project_manager_fi: Callable,
    get_project_territory_fi: Callable,
    get_company_fi,
    get_project_fi,
    get_processed_report_fi,
    status,
):
    project = get_project_fi(company=r_cu.company)
    requesting_project_manager = get_client_project_manager_fi(project=project, company_user=r_cu)

    requesting_project_manager.company_user.status = status
    requesting_project_manager.company_user.save()

    pt = get_project_territory_fi(project=project)
    get_processed_report_fi(project_territory=pt)
    response = __get_response(
        api_client,
        user=requesting_project_manager.company_user.user,
    )
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__contractor_user_from_different_company__fail(
    api_client, get_processed_report_fi, r_cu, get_project_territory_fi, get_cu_manager_fi
):
    pt = get_project_territory_fi()
    get_processed_report_fi(pt=pt)
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == 0
