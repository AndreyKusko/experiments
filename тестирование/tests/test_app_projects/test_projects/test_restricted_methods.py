from http.client import responses

import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model

from tests.utils import get_authorization_token
from companies.models.company_user import CompanyUser

User = get_user_model()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__method__fail(api_client, get_project_fi, r_cu: CompanyUser):
    instance = get_project_fi(company=r_cu.company)
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.delete(f"/api/v1/projects/{instance.id}/")
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED
    assert response.status_text == responses[status_code.HTTP_405_METHOD_NOT_ALLOWED]
