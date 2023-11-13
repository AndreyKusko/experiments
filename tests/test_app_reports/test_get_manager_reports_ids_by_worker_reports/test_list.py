import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated

from tests.utils import request_response_list
from ma_saas.constants.report import ProcessedReportStatus
from ma_saas.constants.system import Callable
from ma_saas.constants.company import NOT_ACCEPT_CUS_VALUES
from companies.models.company_user import CompanyUser

User = get_user_model()


__get_response = functools.partial(
    request_response_list, path="/api/v1/get-manager-reports-ids-by-worker-reports/"
)


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


def test__user_without_companies_got_nothing(api_client, user_fi: User):
    response = __get_response(api_client, user=user_fi)
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(
    api_client,
    r_cu,
    get_project_territory_fi: Callable,
    get_worker_report_fi: Callable,
    get_processed_report_fi,
):
    pt = get_project_territory_fi(company=r_cu.company)

    worker_report1 = get_worker_report_fi(project_territory=pt)
    instance1 = get_processed_report_fi(
        worker_report=worker_report1, status=ProcessedReportStatus.DECLINED.value
    )
    instance2 = get_processed_report_fi(worker_report=worker_report1)

    worker_report2 = get_worker_report_fi(project_territory=pt)
    instance3 = get_processed_report_fi(worker_report=worker_report2)

    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == 3
    assert instance1.id in response.data
    assert instance2.id in response.data
    assert instance3.id in response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(
    api_client,
    mock_policies_false,
    r_cu,
    get_project_territory_fi: Callable,
    get_worker_report_fi: Callable,
    get_processed_report_fi,
):
    pt = get_project_territory_fi(company=r_cu.company)

    worker_report = get_worker_report_fi(project_territory=pt)
    get_processed_report_fi(worker_report=worker_report)
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == 1


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("cu_status", NOT_ACCEPT_CUS_VALUES)
def test__not_accepted_cu_owner__fail(
    api_client,
    r_cu,
    get_project_territory_fi: Callable,
    get_worker_report_fi: Callable,
    get_processed_report_fi,
    cu_status,
):
    pt = get_project_territory_fi(company=r_cu.company)
    r_cu.status = cu_status
    r_cu.save()

    worker_report = get_worker_report_fi(project_territory=pt)
    get_processed_report_fi(worker_report=worker_report)
    response = __get_response(api_client, user=r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__manager__success(
    api_client,
    r_cu,
    get_worker_report_fi,
    get_project_territory_fi,
    get_processed_report_fi,
):
    pt = get_project_territory_fi(company=r_cu.company)
    worker_report = get_worker_report_fi(project_territory=pt)
    get_processed_report_fi(worker_report=worker_report)
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == 1


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
@pytest.mark.parametrize("cu_status", NOT_ACCEPT_CUS_VALUES)
def test__not_accepted__manager__fail(
    api_client,
    r_cu,
    get_worker_report_fi,
    get_project_territory_fi,
    get_processed_report_fi,
    cu_status,
):
    pt = get_project_territory_fi(company=r_cu.company)
    worker_report = get_worker_report_fi(project_territory=pt)
    get_processed_report_fi(worker_report=worker_report)
    response = __get_response(api_client, user=r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__not_related_manager__fail(
    api_client,
    r_cu,
    get_project_territory_fi: Callable,
    get_worker_report_fi: Callable,
    get_processed_report_fi,
):
    pt = get_project_territory_fi(company=r_cu.company)
    worker_report = get_worker_report_fi(project_territory=pt)
    get_processed_report_fi(worker_report=worker_report)
    response = __get_response(api_client, user=r_cu.user)
    assert response.data == []
