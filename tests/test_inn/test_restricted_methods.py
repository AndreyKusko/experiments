import pytest
from rest_framework import status as status_code

from tests.utils import get_authorization_token

LINK = "/api/v1/inn/"


def test__patch__fail(api_client, get_user_fi):
    user = get_user_fi()
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user))
    response = api_client.patch(f"{LINK}")
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


def test__put__fail(api_client, get_user_fi):
    user = get_user_fi()
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user))
    response = api_client.put(f"{LINK}")
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


def test__delete__fail(api_client, get_user_fi):
    user = get_user_fi()
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user))
    response = api_client.delete(f"{LINK}")
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


#
# def test__get__fail(api_client, get_user_fi: Callable):
#     user = get_user_fi()
#     api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user))
#     response = api_client.get(f"{LINK}")
#     assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED
