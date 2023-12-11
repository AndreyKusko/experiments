from http.client import responses

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import MethodNotAllowed

from tests.utils import get_authorization_token
from companies.models.company_user import CompanyUser

User = get_user_model()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__method_delete__fail(api_client, r_cu: CompanyUser):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.delete(f"/api/v1/project-partnerships/{1}/")
    assert response.status_code == MethodNotAllowed.status_code
    assert response.status_text == responses[MethodNotAllowed.status_code]
    assert response.data["detail"] == MethodNotAllowed.default_detail.format(method="DELETE")
