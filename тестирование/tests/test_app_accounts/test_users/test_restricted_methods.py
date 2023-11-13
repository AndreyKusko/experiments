from http.client import responses

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import MethodNotAllowed

from tests.utils import get_authorization_token
from ma_saas.constants.system import POST, DELETE

User = get_user_model()


def test__create(api_client, user_fi):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user_fi))
    response = api_client.post(f"/api/v1/users/", data={})
    assert response.status_code == MethodNotAllowed.status_code
    assert response.status_text == responses[MethodNotAllowed.status_code]
    assert response.data["detail"] == MethodNotAllowed.default_detail.format(method=POST)


def test__delete(api_client, user_fi):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user_fi))
    response = api_client.delete(f"/api/v1/users/{user_fi.id}/")
    assert response.status_code == MethodNotAllowed.status_code
    assert response.data["detail"] == MethodNotAllowed.default_detail.format(method=DELETE)
