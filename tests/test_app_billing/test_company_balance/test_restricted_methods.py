import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model

from tests.utils import get_authorization_token
from ma_saas.constants.system import API_V1
from companies.models.company_user import CompanyUser

User = get_user_model()
LINK = f"/{API_V1}/company-balance"


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__post__fail(api_client, r_cu: CompanyUser):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.post(f"{LINK}/{r_cu.company.id}/", data={})
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__patch__fail(api_client, r_cu: CompanyUser):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.patch(f"{LINK}/{r_cu.company.id}/", data={})
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__put__fail(api_client, r_cu: CompanyUser):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.put(f"{LINK}/{r_cu.company.id}/", data={})
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__delete__fail(api_client, r_cu: CompanyUser):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.delete(f"{LINK}/{r_cu.company.id}/")
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED
