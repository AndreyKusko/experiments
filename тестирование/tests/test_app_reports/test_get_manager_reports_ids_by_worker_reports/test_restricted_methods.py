import pytest
from rest_framework import status as status_code

from tests.utils import get_authorization_token
from ma_saas.constants.system import Callable
from companies.models.company_user import CompanyUser

LINK = "/api/v1/get-manager-reports-ids-by-worker-reports"


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__patch__fail(api_client, r_cu: CompanyUser):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.post(f"{LINK}/", data={})
    assert response.status_code == status_code.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__patch__fail(
    api_client,
    r_cu: CompanyUser,
    get_project_territory_fi: Callable,
    get_worker_report_fi: Callable,
    get_processed_report_fi,
):
    pt = get_project_territory_fi(company=r_cu.company)
    worker_report = get_worker_report_fi(project_territory=pt)
    instance = get_processed_report_fi(worker_report=worker_report)

    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.patch(f"{LINK}/{instance.id}/", data={})
    assert response.status_code == status_code.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__put__fail(
    api_client,
    r_cu: CompanyUser,
    get_project_territory_fi: Callable,
    get_worker_report_fi: Callable,
    get_processed_report_fi,
):
    pt = get_project_territory_fi(company=r_cu.company)
    worker_report = get_worker_report_fi(project_territory=pt)
    instance = get_processed_report_fi(worker_report=worker_report)
    response = api_client.put(f"{LINK}/{instance.id}/", data={})
    assert response.status_code == status_code.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__delete__fail(
    api_client,
    r_cu: CompanyUser,
    get_project_territory_fi: Callable,
    get_worker_report_fi: Callable,
    get_processed_report_fi,
):
    pt = get_project_territory_fi(company=r_cu.company)
    worker_report = get_worker_report_fi(project_territory=pt)
    instance = get_processed_report_fi(worker_report=worker_report)
    response = api_client.delete(f"{LINK}/{instance.id}/")
    status_codes = status_code.HTTP_404_NOT_FOUND
    assert response.status_code == status_codes


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__get__fail(
    api_client,
    r_cu: CompanyUser,
    get_project_territory_fi: Callable,
    get_worker_report_fi: Callable,
    get_processed_report_fi,
):
    pt = get_project_territory_fi(company=r_cu.company)
    worker_report = get_worker_report_fi(project_territory=pt)
    instance = get_processed_report_fi(worker_report=worker_report)
    response = api_client.get(f"{LINK}/{instance.id}/")
    assert response.status_code == status_code.HTTP_404_NOT_FOUND
