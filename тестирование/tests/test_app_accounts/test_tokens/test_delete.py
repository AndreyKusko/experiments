import functools
from http.client import responses

from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from authserv.clients.auth import AuthServ
from rest_framework.exceptions import NotAuthenticated

from tests.utils import get_authorization_token, request_response_delete
from accounts.models.token import Token
from ma_saas.constants.system import Callable

User = get_user_model()

__get_response = functools.partial(request_response_delete, path="/api/v1/tokens/")


def test__anonymous_user__fail(api_client, user_fi: User, get_authorization_token_instance_fi: Callable):
    token = get_authorization_token_instance_fi(user=user_fi)
    response = __get_response(api_client, instance_id=token.key, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


def test__authorised_user__success(api_client, monkeypatch, user_fi, get_authorization_token_instance_fi):
    monkeypatch.setattr(AuthServ, "delete_session", lambda *a, **kw: None)
    token = get_authorization_token_instance_fi(user=user_fi)
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user_fi))
    response = api_client.delete(f"/api/v1/tokens/{token.key}/")
    expected_codes = (status_code.HTTP_200_OK, status_code.HTTP_204_NO_CONTENT)
    assert response.status_code in expected_codes
    assert response.status_text in (responses[code] for code in expected_codes)
    assert not Token.objects.filter(key=token.key).exists()
