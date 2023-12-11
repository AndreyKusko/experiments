import typing as tp
import functools
from http.client import responses

import pytest
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed

from tests.utils import request_response_get, get_authorization_token, request_response_update
from ma_saas.constants.system import GET, PATCH, Callable

User = get_user_model()


def __get_delete_response(api_client, status_code: int, user: tp.Optional[User] = None) -> Response:
    """Return response."""
    if user:
        api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user))
    response = api_client.get(f"/api/v1/tokens/")
    assert response.status_code == status_code, f"response.data = {response.data}"
    assert response.status_text == responses[status_code]

    return response


def test__delete_anonymous_user__fail(api_client, user_fi):
    response = __get_delete_response(api_client, MethodNotAllowed.status_code)
    assert response.data["detail"] == MethodNotAllowed.default_detail.format(method=GET)


def test__delete_authorised_user__fail(api_client, user_fi):
    response = __get_delete_response(api_client, MethodNotAllowed.status_code, user=user_fi)
    assert response.data["detail"] == MethodNotAllowed.default_detail.format(method=GET)


__get_response = functools.partial(request_response_get, path="/api/v1/tokens/")


def test__retrieve_anonymous_user__fail(
    api_client, user_fi: User, get_authorization_token_instance_fi: Callable
):
    token = get_authorization_token_instance_fi(user=user_fi)
    response = __get_response(api_client, instance_id=token.pk, status_codes=MethodNotAllowed.status_code)
    assert response.data["detail"] == MethodNotAllowed.default_detail.format(method=GET)


def test__retrieve_authorised_user__fail(
    api_client, user_fi: User, get_authorization_token_instance_fi: Callable
):
    token = get_authorization_token_instance_fi(user=user_fi)
    response = __get_response(api_client, token.pk, user_fi, status_codes=MethodNotAllowed)
    assert response.data["detail"] == MethodNotAllowed.default_detail.format(method=GET)


__get_update_response = functools.partial(request_response_update, path="/api/v1/tokens/")


def test__update_anonymous_user__fail(api_client, user_fi, get_authorization_token_instance_fi):
    token = get_authorization_token_instance_fi(user=user_fi)
    response = __get_update_response(api_client, token.pk, {}, user_fi, status_codes=MethodNotAllowed)
    assert response.data["detail"] == MethodNotAllowed.default_detail.format(method=PATCH)


def test__update_authorised_user__fail(api_client, user_fi, get_authorization_token_instance_fi):
    token = get_authorization_token_instance_fi(user=user_fi)
    response = __get_update_response(api_client, token.pk, {}, user_fi, status_codes=MethodNotAllowed)
    assert response.data["detail"] == MethodNotAllowed.default_detail.format(method=PATCH)
