import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, PermissionDenied

from tests.utils import get_authorization_token
from ma_saas.constants.system import API_V1

User = get_user_model()
LINK = f"/{API_V1}/top-up-company-billing-account"


def test__post__fail(api_client, get_user_fi):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(get_user_fi()))
    response = api_client.post(f"{LINK}/", data={})
    assert response.status_code == PermissionDenied.status_code
    assert response.data["detail"] == PermissionDenied.default_detail


def test__delete__fail(api_client, get_user_fi):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(get_user_fi()))
    response = api_client.delete(f"{LINK}/1/")
    assert response.status_code == PermissionDenied.status_code
    assert response.data["detail"] == PermissionDenied.default_detail


def test__get__fail(api_client, get_user_fi):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(get_user_fi()))
    response = api_client.get(f"{LINK}/1/")
    assert response.status_code == PermissionDenied.status_code
    assert response.data["detail"] == PermissionDenied.default_detail


def test__list__fail(api_client, get_user_fi):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(get_user_fi()))
    response = api_client.get(f"{LINK}/", data={})
    assert response.status_code == PermissionDenied.status_code
    assert response.data["detail"] == PermissionDenied.default_detail
