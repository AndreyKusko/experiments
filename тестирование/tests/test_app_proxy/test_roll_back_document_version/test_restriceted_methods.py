from http.client import responses

import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model

from tests.utils import get_authorization_token
from ma_saas.constants.system import Callable
from companies.models.company_user import CompanyUser

User = get_user_model()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__delete_method__fail(api_client, r_cu: CompanyUser):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.delete(f"/api/v1/roll-back-document-version/{1}/")
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED
    assert response.status_text == responses[status_code.HTTP_405_METHOD_NOT_ALLOWED]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__retrieve_method__fail(api_client, r_cu: CompanyUser):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.get(f"/api/v1/roll-back-document-version/{1}/")
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED
    assert response.status_text == responses[status_code.HTTP_405_METHOD_NOT_ALLOWED]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__create_method__fail(api_client, r_cu: CompanyUser):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.post(f"/api/v1/roll-back-document-version/", data={})
    assert response.status_code == status_code.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__list_method__fail(api_client, r_cu: CompanyUser):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.get(f"/api/v1/roll-back-document-version/")
    assert response.status_code == status_code.HTTP_404_NOT_FOUND
