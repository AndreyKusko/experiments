from rest_framework.exceptions import NotFound, MethodNotAllowed

from tests.utils import get_authorization_token

LINK = "/api/v1/contact-verification-confirm/"


def test__list__fail(api_client, user_fi):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user_fi))
    response = api_client.get(f"{LINK}")
    assert response.status_code == MethodNotAllowed.status_code


def test__get__fail(api_client, user_fi):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user_fi))
    response = api_client.get(f"{LINK}1/")
    assert response.status_code == NotFound.status_code


def test__patch__fail(api_client, user_fi):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user_fi))
    response = api_client.patch(f"{LINK}")
    assert response.status_code == MethodNotAllowed.status_code


def test__put__fail(api_client, user_fi):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user_fi))
    response = api_client.put(f"{LINK}")
    assert response.status_code == MethodNotAllowed.status_code


def test__delete__fail(api_client, user_fi):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user_fi))
    response = api_client.delete(f"{LINK}")
    assert response.status_code == MethodNotAllowed.status_code
