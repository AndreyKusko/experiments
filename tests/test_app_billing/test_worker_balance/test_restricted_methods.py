from rest_framework import status as status_code
from django.contrib.auth import get_user_model

from tests.utils import get_authorization_token
from ma_saas.constants.system import API_V1

User = get_user_model()
LINK = f"/{API_V1}/worker-balance"


def test__post__fail(api_client, get_user_fi):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(get_user_fi()))
    response = api_client.post(f"{LINK}/", data={})
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


def test__patch__fail(api_client, get_user_fi):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(get_user_fi()))
    response = api_client.patch(f"{LINK}/1/", data={})
    assert response.status_code == status_code.HTTP_404_NOT_FOUND


def test__put__fail(api_client, get_user_fi):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(get_user_fi()))
    response = api_client.put(f"{LINK}/1/", data={})
    assert response.status_code == status_code.HTTP_404_NOT_FOUND


def test__delete__fail(api_client, get_user_fi):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(get_user_fi()))
    response = api_client.delete(f"{LINK}/1/")
    assert response.status_code == status_code.HTTP_404_NOT_FOUND


def test__get__fail(api_client, get_user_fi):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(get_user_fi()))
    response = api_client.get(f"{LINK}/1/")
    assert response.status_code == status_code.HTTP_404_NOT_FOUND
