from rest_framework.exceptions import NotFound, MethodNotAllowed

from tests.utils import get_authorization_token
from ma_saas.constants.system import GET


def test__delete(api_client, user_fi):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user_fi))
    response = api_client.delete(f"/api/v1/sign-up-new-company-owner-via-invite/{user_fi.id}/")
    assert response.status_code == NotFound.status_code


def test__update(api_client, user_fi):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user_fi))
    response = api_client.patch(f"/api/v1/sign-up-new-company-owner-via-invite/{user_fi.id}/", data={})
    assert response.status_code == NotFound.status_code


def test__retrieve(api_client, user_fi):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user_fi))
    response = api_client.get(f"/api/v1/sign-up-new-company-owner-via-invite/{user_fi.id}/")
    assert response.status_code == NotFound.status_code


def test__list(api_client, user_fi):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user_fi))
    response = api_client.get(f"/api/v1/sign-up-new-company-owner-via-invite/")
    assert response.status_code == MethodNotAllowed.status_code
    assert response.data == {"detail": MethodNotAllowed.default_detail.format(method=GET)}
