import typing as tp
import posixpath

from requests import Response
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework.exceptions import ValidationError

from accounts.models.token import Token

User = get_user_model()


RAISE_TEST_ERR = "Поднять тестовую ошибку"


def raise_test_error(err_class=ValidationError, err_txt=RAISE_TEST_ERR):
    raise err_class(err_txt)


def get_authorization_token(user: User):
    token, _ = Token.objects.get_or_create(user=user)
    return f"Token {token.key}"


def get_random_email():
    """Сгенерировать почту для тестирования."""
    return f"{get_random_string().lower()}@test.test"


def get_random_phone(prefix=""):
    """
    Сгенерировать телефон для тестирования.

    Телефон генерируется без префиксов: +7, 7, 8.
    Колтичество цифр соответсвует русскому телефону.
    """
    return f'{prefix}{get_random_string(length=10, allowed_chars="12345689")}'


def get_random_int(length=5):
    """
    Сгенерировать случайное число для тестирования
    """
    return int(get_random_string(length=length, allowed_chars="12345689"))


def retrieve_response_instance(data, name, instance_type):
    response_instance = data.pop(name)
    if instance_type:
        assert isinstance(response_instance, instance_type)
    else:
        assert response_instance == instance_type
    return response_instance


def _process_status_codes(status_codes, default):
    status_codes = default if not status_codes else status_codes
    status_codes = {status_codes} if not isinstance(status_codes, set) else status_codes

    codes = set()
    for code in status_codes:
        if isinstance(code, int):
            codes.add(code)
        else:
            codes.add(code.status_code)
    return codes


def _validate_path(path):
    if not path:
        raise ValueError("path is required DUDE!!!!")


def _aut_user(api_client, user):
    if user:
        api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user))


def request_response_list(
    api_client,
    user: tp.Optional[User] = None,
    status_codes: tp.Optional[tp.Union[int, set]] = None,
    path="",
    query_kwargs: tp.Optional[dict] = None,
) -> Response:
    """Return response."""
    _validate_path(path)
    _aut_user(api_client, user)

    url_query_attrs = ""
    if query_kwargs:
        url_query_attrs = "?" + "&".join((f"{k}={v}" for k, v in query_kwargs.items()))
    url = posixpath.join(path, url_query_attrs)
    response = api_client.get(url)

    expecting_status_codes = _process_status_codes(status_codes, default={status_code.HTTP_200_OK})
    response_status_code = response.status_code
    is_correct_response_status_code = response_status_code in expecting_status_codes
    assert (
        is_correct_response_status_code
    ), f"response_status_code {response_status_code} not in {expecting_status_codes} | response.data = {response.data}"
    return response


def request_response_get(
    api_client, instance_id: int, user: tp.Optional[User] = None, status_codes=None, path=""
) -> Response:
    """Return response."""
    _validate_path(path)
    _aut_user(api_client, user)
    response = api_client.get(posixpath.join(path, f"{instance_id}", ""))
    expecting_status_codes = _process_status_codes(status_codes, default={status_code.HTTP_200_OK})
    response_status_code = response.status_code
    is_correct_response_status_code = response_status_code in expecting_status_codes
    assert (
        is_correct_response_status_code
    ), f"response_status_code {response_status_code} not in {expecting_status_codes} | response.data = {response.data}"

    return response


def request_response_update(api_client, instance_id, data, user=None, status_codes=None, path="") -> Response:
    """Return response."""
    _validate_path(path)
    _aut_user(api_client, user)
    response = api_client.patch(posixpath.join(path, f"{instance_id}", ""), data=data, format="json")

    expecting_status_codes = _process_status_codes(status_codes, default={status_code.HTTP_200_OK})
    response_status_code = response.status_code
    is_correct_response_status_code = response_status_code in expecting_status_codes
    assert (
        is_correct_response_status_code
    ), f"response_status_code {response_status_code} not in {expecting_status_codes} | response.data = {response.data}"
    return response


def request_response_delete(api_client, instance_id: int, user=None, status_codes=None, path="") -> Response:
    """Return response."""
    _validate_path(path)
    _aut_user(api_client, user)
    response = api_client.delete(posixpath.join(path, f"{instance_id}", ""))
    assert response.status_code in _process_status_codes(
        status_codes, default={status_code.HTTP_200_OK, status_code.HTTP_204_NO_CONTENT}
    ), f"response.status_code = {response.status_code} | response = {response.data}"
    return response


def request_response_create(api_client, data, user=None, status_codes=None, path="") -> Response:
    """Return response."""
    _validate_path(path)
    _aut_user(api_client, user)
    response = api_client.post(path, data=data)
    scs = _process_status_codes(status_codes, default={status_code.HTTP_200_OK, status_code.HTTP_201_CREATED})
    assert (
        response.status_code in scs
    ), f"response.status_code = {response.status_code} | response = {response.data}"
    return response
