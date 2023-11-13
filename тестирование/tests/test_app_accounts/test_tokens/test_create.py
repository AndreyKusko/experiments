import functools

from django.contrib.auth import get_user_model
from rest_framework.fields import Field
from rest_framework.exceptions import ValidationError

from tests.utils import get_random_email, get_random_phone, request_response_create
from tests.fixtures.user import LONG_TEST_PASSWORD, SHORT_TEST_PASSWORD
from accounts.serializers.validators import EMAIL_OR_PHONE_REQUIRE

User = get_user_model()


__get_response = functools.partial(request_response_create, path="/api/v1/tokens/")


def test__anonymous_creating_via_email(api_client, get_user_fi, get_authorization_token_fi):
    password = LONG_TEST_PASSWORD
    requesting_user = get_user_fi(email=get_random_email(), password=password)
    response = __get_response(api_client, data={"email": requesting_user.email, "password": password})
    assert "Token " + response.data["key"] == get_authorization_token_fi(requesting_user)


def test__anonymous_creating_via_phone(api_client, get_user_fi, get_authorization_token_fi):
    requesting_user = get_user_fi(phone=get_random_phone(), password=SHORT_TEST_PASSWORD)
    response = __get_response(
        api_client, data={"phone": requesting_user.phone, "password": SHORT_TEST_PASSWORD}
    )
    assert "Token " + response.data["key"] == get_authorization_token_fi(requesting_user)


def test__authorised_creating_via_phone__success(api_client, get_user_fi, get_authorization_token_fi):
    requesting_user = get_user_fi(phone=get_random_phone(), password=SHORT_TEST_PASSWORD)
    data = {"phone": requesting_user.phone, "password": SHORT_TEST_PASSWORD}
    response = __get_response(api_client, data=data, user=requesting_user)
    assert "Token " + response.data["key"] == get_authorization_token_fi(requesting_user)


def test__authorised_creating_via_email__success(api_client, get_user_fi, get_authorization_token_fi):
    requesting_user = get_user_fi(email=get_random_email(), password=LONG_TEST_PASSWORD)
    data = {"email": requesting_user.email, "password": LONG_TEST_PASSWORD}
    response = __get_response(api_client, data=data, user=requesting_user)
    assert "Token " + response.data["key"] == get_authorization_token_fi(requesting_user)


def test__contact_require__fail(api_client, get_user_fi):
    get_user_fi(email=get_random_email(), password=LONG_TEST_PASSWORD)
    data = {"password": LONG_TEST_PASSWORD}
    response = __get_response(api_client, data=data, status_codes=ValidationError)
    assert response.data[0] == EMAIL_OR_PHONE_REQUIRE


def test__password_require__fail(api_client, get_user_fi):
    user = get_user_fi(email=get_random_email(), password=LONG_TEST_PASSWORD)
    data = {"email": user.email}
    response = __get_response(api_client, data=data, status_codes=ValidationError)
    assert response.data["password"][0] == Field.default_error_messages["required"]

    user = get_user_fi(phone=get_random_phone(), password=LONG_TEST_PASSWORD)
    data = {"phone": user.phone}
    response = __get_response(api_client, data=data, status_codes=ValidationError)
    assert response.data["password"][0] == Field.default_error_messages["required"]
