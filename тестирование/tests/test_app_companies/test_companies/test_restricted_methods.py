import functools
from http.client import responses

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import MethodNotAllowed, NotAuthenticated

from tests.utils import get_authorization_token, request_response_create
from ma_saas.constants.system import Callable
from companies.models.company_user import CompanyUser

User = get_user_model()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__method__fail(api_client, r_cu: CompanyUser):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.delete(f"/api/v1/companies/{r_cu.company.id}/")
    assert response.status_code == MethodNotAllowed.status_code
    assert response.status_text == responses[MethodNotAllowed.status_code]
    assert response.data == {"detail": MethodNotAllowed.default_detail.format(method="DELETE")}


__get_create_response = functools.partial(request_response_create, path="/api/v1/companies/")


def test__create_anonymous_user(api_client, new_company_data):
    response = __get_create_response(api_client, data=new_company_data(), status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


def test__create_authenticated(monkeypatch, api_client, user_fi: User, new_company_data: Callable):
    response = __get_create_response(api_client, new_company_data(), user_fi, status_codes=MethodNotAllowed)
    assert response.data == {"detail": MethodNotAllowed.default_detail.format(method="POST")}
