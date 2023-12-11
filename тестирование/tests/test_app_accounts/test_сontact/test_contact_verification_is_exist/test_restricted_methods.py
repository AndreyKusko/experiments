from rest_framework.exceptions import MethodNotAllowed

LINK = "/api/v1/contact-verification-is-exist/"


def test__post__fail(api_client):
    response = api_client.post(f"{LINK}")
    assert response.status_code == MethodNotAllowed.status_code


def test__patch__fail(api_client):
    response = api_client.patch(f"{LINK}")
    assert response.status_code == MethodNotAllowed.status_code


def test__put__fail(api_client):
    response = api_client.put(f"{LINK}")
    assert response.status_code == MethodNotAllowed.status_code


def test__delete__fail(api_client):
    response = api_client.delete(f"{LINK}")
    assert response.status_code == MethodNotAllowed.status_code
