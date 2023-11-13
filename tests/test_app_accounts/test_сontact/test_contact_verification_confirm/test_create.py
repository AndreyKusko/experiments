import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, ValidationError

from tests.utils import get_random_email, get_random_phone, request_response_create
from accounts.serializers.utils import parse_phone_number
from ma_saas.constants.constant import CONTACT_VERIFICATION_PURPOSE
from accounts.serializers.validators import VERIFICATION_NOT_FOUND, ACTIVE_VERIFICATION_NOT_FOUND
from accounts.models.contact_verification import VERIFICATION_CODE_EXPIRATION_TD, ContactVerification

User = get_user_model()

__get_response = functools.partial(request_response_create, path="/api/v1/contact-verification-confirm/")

_PURPOSE = dict(purpose=CONTACT_VERIFICATION_PURPOSE)


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)},))
def test__not_existing__fail(api_client, data: dict, get_user_fi):
    check_data = {k: v for k, v in data.items() if v}
    if data.get("phone"):
        check_data["phone"] = parse_phone_number(raw_phone_number=data["phone"])
    assert not ContactVerification.objects.filter(**check_data, **_PURPOSE, is_confirmed=False).exists()
    user = get_user_fi(**check_data)

    response = __get_response(api_client, user=user, data=data, status_codes=ValidationError)
    assert response.data == {"small_code": ["This field is required."]}


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)}, {"email": get_random_email()}))
def test__confirmed_cv__fail(api_client, data: dict, get_user_fi):
    check_data = {k: v for k, v in data.items() if v}
    if data.get("phone"):
        check_data["phone"] = parse_phone_number(raw_phone_number=data["phone"])
    assert not ContactVerification.objects.filter(**check_data, **_PURPOSE).exists()
    cv = ContactVerification.objects.create(**check_data, **_PURPOSE, is_confirmed=True)
    user = get_user_fi(**check_data)
    data["small_code"] = cv.small_code
    response = __get_response(api_client, user=user, data=data, status_codes=ValidationError)
    assert response.data == [ACTIVE_VERIFICATION_NOT_FOUND]


@pytest.mark.parametrize(
    "data",
    (
        {"phone": get_random_phone(7)},
        {"phone": get_random_phone(7), "email": ""},
        {"phone": get_random_phone(8), "email": ""},
        {"phone": get_random_phone(""), "email": ""},
        {"phone": "", "email": get_random_email()},
        {"email": get_random_email()},
    ),
)
def test__invalid_code__fail(api_client, data: dict, get_user_fi):
    check_data = {k: v for k, v in data.items() if v}
    if data.get("phone"):
        check_data["phone"] = parse_phone_number(raw_phone_number=data["phone"])

    assert not ContactVerification.objects.filter(**check_data, **_PURPOSE, is_confirmed=False).exists()

    ContactVerification.objects.create(**check_data, **_PURPOSE, is_confirmed=False)
    user = get_user_fi(**check_data)

    data["small_code"] = "1234"
    response = __get_response(api_client, user=user, data=data, status_codes=ValidationError)
    assert response.data == [VERIFICATION_NOT_FOUND]


@pytest.mark.parametrize(
    "data",
    (
        {"phone": get_random_phone(7)},
        {"phone": get_random_phone(7), "email": ""},
        {"phone": get_random_phone(8), "email": ""},
        {"phone": get_random_phone(""), "email": ""},
        {"phone": "", "email": get_random_email()},
        {"email": get_random_email()},
    ),
)
def test__verified__success(api_client, data: dict, get_user_fi):
    check_data = {k: v for k, v in data.items() if v}
    if data.get("phone"):
        check_data["phone"] = parse_phone_number(raw_phone_number=data["phone"])
    instance = ContactVerification.objects.create(
        **check_data, purpose=CONTACT_VERIFICATION_PURPOSE, is_confirmed=False
    )
    user = get_user_fi(**check_data, is_verified_phone=True, is_verified_email=True)
    assert user.is_verified_phone
    assert user.is_verified_email
    data["small_code"] = instance.small_code
    response = __get_response(api_client, user=user, data=data)
    updated_user = User.objects.get(id=user.id)
    assert updated_user.is_verified_phone
    assert updated_user.is_verified_email
    updated_instance = ContactVerification.objects.get(id=instance.id)
    assert updated_instance.is_confirmed
    assert response.data == {"verification_code": None}


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)}, {"email": get_random_email()}))
def test__confirmed_cv__fail(api_client, data: dict, get_user_fi):
    check_data = {k: v for k, v in data.items() if v}
    if data.get("phone"):
        check_data["phone"] = parse_phone_number(raw_phone_number=data["phone"])
    assert not ContactVerification.objects.filter(**check_data, **_PURPOSE).exists()
    instance = ContactVerification.objects.create(**check_data, **_PURPOSE, is_confirmed=True)
    instance.created_at = instance.created_at - VERIFICATION_CODE_EXPIRATION_TD
    instance.save()
    user = get_user_fi(**check_data, is_verified_phone=True, is_verified_email=True)
    data["small_code"] = instance.small_code
    response = __get_response(api_client, user=user, data=data, status_codes=ValidationError)
    assert response.data == [ACTIVE_VERIFICATION_NOT_FOUND]


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)}, {"email": get_random_email()}))
def test__confirmed__fail(api_client, data: dict, get_user_fi):
    check_data = {k: v for k, v in data.items() if v}
    if data.get("phone"):
        check_data["phone"] = parse_phone_number(raw_phone_number=data["phone"])
    cv = ContactVerification.objects.create(
        **check_data, purpose=CONTACT_VERIFICATION_PURPOSE, is_confirmed=True
    )
    user = get_user_fi(**check_data, is_verified_phone=False, is_verified_email=False)
    assert not user.is_verified_phone
    assert not user.is_verified_email
    data["small_code"] = cv.small_code
    response = __get_response(api_client, user=user, data=data, status_codes=ValidationError)
    updated_user = User.objects.get(id=user.id)
    assert not updated_user.is_verified_phone
    assert not updated_user.is_verified_email
    assert response.data == [ACTIVE_VERIFICATION_NOT_FOUND]


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)}, {"email": get_random_email()}))
def test__not_verified__success(api_client, data: dict, get_user_fi):
    check_data = {k: v for k, v in data.items() if v}
    if data.get("phone"):
        check_data["phone"] = parse_phone_number(raw_phone_number=data["phone"])
    instance = ContactVerification.objects.create(
        **check_data, purpose=CONTACT_VERIFICATION_PURPOSE, is_confirmed=False
    )
    user = get_user_fi(**check_data, is_verified_phone=False, is_verified_email=False)
    assert not user.is_verified_phone
    assert not user.is_verified_email
    data["small_code"] = instance.small_code
    response = __get_response(api_client, user=user, data=data)
    updated_user = User.objects.get(id=user.id)
    if data.get("phone"):
        assert updated_user.is_verified_phone
    if data.get("email"):
        assert updated_user.is_verified_email
    updated_instance = ContactVerification.objects.get(id=instance.id)
    assert updated_instance.is_confirmed
    assert response.data == {"verification_code": None}


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)}, {"email": get_random_email()}))
def test__without_password__success(api_client, data: dict, get_user_fi):
    check_data = {k: v for k, v in data.items() if v}
    if data.get("phone"):
        check_data["phone"] = parse_phone_number(raw_phone_number=data["phone"])
    instance = ContactVerification.objects.create(
        **check_data, purpose=CONTACT_VERIFICATION_PURPOSE, is_confirmed=False
    )
    user = get_user_fi(**check_data, is_verified_phone=False, is_verified_email=False)
    user.password = ""
    user.save()
    assert not user.is_verified_phone
    assert not user.is_verified_email
    data["small_code"] = instance.small_code
    response = __get_response(api_client, user=user, data=data)
    updated_user = User.objects.get(id=user.id)
    if data.get("phone"):
        assert updated_user.is_verified_phone
    if data.get("email"):
        assert updated_user.is_verified_email
    updated_instance = ContactVerification.objects.get(id=instance.id)
    assert updated_instance.is_confirmed
