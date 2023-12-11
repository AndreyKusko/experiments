import pytest
from rest_framework import status as status_code

from tests.utils import get_authorization_token
from companies.models.company_user import CompanyUser


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__patch__fail(api_client, r_cu: CompanyUser, get_cu_fi):
    instance = get_cu_fi(company=r_cu.company)
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.patch(f"/api/v1/company-user-invites/{instance.id}/", data={})
    assert response.status_code == status_code.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__put__fail(api_client, r_cu: CompanyUser, get_cu_fi):
    instance = get_cu_fi(company=r_cu.company)
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.put(f"/api/v1/company-user-invites/{instance.id}/", data={})
    assert response.status_code == status_code.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__delete__fail(api_client, r_cu: CompanyUser, get_cu_fi):
    instance = get_cu_fi(company=r_cu.company)
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.delete(f"/api/v1/company-user-invites/{instance.id}/")
    status_codes = status_code.HTTP_404_NOT_FOUND
    assert response.status_code == status_codes


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__get__fail(api_client, r_cu: CompanyUser, get_cu_fi):
    instance = get_cu_fi(company=r_cu.company)
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.get(f"/api/v1/company-user-invites/{instance.id}/")
    assert response.status_code == status_code.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__list__method__fail(api_client, r_cu: CompanyUser, get_cu_fi):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.get(f"/api/v1/company-user-invites/")
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED
