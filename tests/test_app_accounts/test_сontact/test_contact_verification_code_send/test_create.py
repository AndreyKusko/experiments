import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from tests.utils import (
    RAISE_TEST_ERR,
    get_random_email,
    get_random_phone,
    raise_test_error,
    request_response_create,
)
from accounts.serializers.utils import parse_phone_number
from ma_saas.constants.constant import CONTACT_VERIFICATION_PURPOSE
from accounts.models.contact_verification import ContactVerification
from clients.notifications.interfaces.sms import SendSMS
from clients.notifications.interfaces.email import SendEmail
from accounts.serializers.contact.contact_verification_code_send import TEST_USER_VERIFICATION_CODE_REQUIRED

User = get_user_model()

__get_response = functools.partial(request_response_create, path="/api/v1/contact-verification-code-send/")
_PURPOSE = CONTACT_VERIFICATION_PURPOSE


@pytest.mark.parametrize(
    "data",
    (
        {"phone": get_random_phone(7)},
        {"phone": get_random_phone(7), "email": ""},
        {"phone": get_random_phone(8)},
        {"phone": get_random_phone()},
        {"phone": "", "email": get_random_email()},
        {"email": get_random_email()},
    ),
)
def test__any_contact_without_password__success(api_client, monkeypatch, data: dict, get_user_fi):
    monkeypatch.setattr(SendSMS, "verification_code", lambda *a, **kw: None)
    monkeypatch.setattr(SendEmail, "verification_code", lambda *a, **kw: None)

    user = get_user_fi(**data, password="")
    user.password = ""
    user.save(update_fields=["password"])

    check_data = {k: v for k, v in data.items() if v}
    if data.get("phone"):
        check_data["phone"] = parse_phone_number(raw_phone_number=data["phone"])

    assert not ContactVerification.objects.filter(**check_data, purpose=_PURPOSE, is_confirmed=False).exists()
    response = __get_response(api_client, data=data)
    assert response.data["is_password"] is False
    assert ContactVerification.objects.filter(**check_data, purpose=_PURPOSE, is_confirmed=False).exists()


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
def test__any_contact__with_password__success(api_client, monkeypatch, data: dict, get_user_fi):
    monkeypatch.setattr(SendSMS, "verification_code", lambda *a, **kw: None)
    monkeypatch.setattr(SendEmail, "verification_code", lambda *a, **kw: None)

    get_user_fi(**data)
    check_data = {k: v for k, v in data.items() if v}
    if data.get("phone"):
        check_data["phone"] = parse_phone_number(raw_phone_number=data["phone"])

    assert not ContactVerification.objects.filter(**check_data, purpose=_PURPOSE, is_confirmed=False).exists()
    response = __get_response(api_client, data=data)
    assert response.data["is_password"] is True
    assert ContactVerification.objects.filter(**check_data, purpose=_PURPOSE, is_confirmed=False).exists()


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
def test__not_existing_user__success(api_client, monkeypatch, data: dict):
    monkeypatch.setattr(SendSMS, "verification_code", lambda *a, **kw: None)
    monkeypatch.setattr(SendEmail, "verification_code", lambda *a, **kw: None)

    check_data = {k: v for k, v in data.items() if v}
    if data.get("phone"):
        check_data["phone"] = parse_phone_number(raw_phone_number=data["phone"])

    assert not ContactVerification.objects.filter(**check_data, purpose=_PURPOSE, is_confirmed=False).exists()
    response = __get_response(api_client, data=data)
    assert response.data["is_password"] == False
    assert ContactVerification.objects.filter(**check_data, purpose=_PURPOSE, is_confirmed=False).exists()


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)}, {"email": get_random_email()}))
def test__response_data(api_client, monkeypatch, data: dict):
    monkeypatch.setattr(SendSMS, "verification_code", lambda *a, **kw: None)
    monkeypatch.setattr(SendEmail, "verification_code", lambda *a, **kw: None)

    check_data = {k: v for k, v in data.items() if v}
    if data.get("phone"):
        check_data["phone"] = parse_phone_number(raw_phone_number=data["phone"])

    assert not ContactVerification.objects.filter(**check_data, purpose=_PURPOSE, is_confirmed=False).exists()
    response = __get_response(api_client, data=data)
    assert response.data == {
        "phone": data.get("phone", None),
        "email": data.get("email", None),
        "is_password": False,
    }


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)}, {"email": get_random_email()}))
def test__if_send_fail__fail(api_client, monkeypatch, data: dict, get_user_fi):
    monkeypatch.setattr(SendSMS, "verification_code", lambda *a, **kw: raise_test_error())
    monkeypatch.setattr(SendEmail, "verification_code", lambda *a, **kw: raise_test_error())

    check_data = {k: v for k, v in data.items() if v}
    if data.get("phone"):
        check_data["phone"] = parse_phone_number(raw_phone_number=data["phone"])

    assert not ContactVerification.objects.filter(**check_data, purpose=_PURPOSE, is_confirmed=False).exists()
    response = __get_response(api_client, data=data, status_codes=ValidationError)
    assert response.data == [RAISE_TEST_ERR]


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
def test__verified_contacts__success(api_client, monkeypatch, data: dict, get_user_fi):
    monkeypatch.setattr(SendSMS, "verification_code", lambda *a, **kw: None)
    monkeypatch.setattr(SendEmail, "verification_code", lambda *a, **kw: None)

    if data.get("phone"):
        get_user_fi(**data, is_verified_phone=True)
    if data.get("email"):
        get_user_fi(**data, is_verified_email=True)

    check_data = {k: v for k, v in data.items() if v}
    if data.get("phone"):
        check_data["phone"] = parse_phone_number(raw_phone_number=data["phone"])

    assert not ContactVerification.objects.filter(**check_data, purpose=_PURPOSE, is_confirmed=False).exists()
    response = __get_response(api_client, data=data)
    assert response.data["is_password"] == True
    assert ContactVerification.objects.filter(**check_data, purpose=_PURPOSE, is_confirmed=False).exists()


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)}, {"email": get_random_email()}))
def test__test_user__without_code__fail(api_client, monkeypatch, data: dict, get_user_fi):
    monkeypatch.setattr(SendSMS, "verification_code", lambda *a, **kw: raise_test_error())
    monkeypatch.setattr(SendEmail, "verification_code", lambda *a, **kw: raise_test_error())
    get_user_fi(**data, is_test=True)
    assert not ContactVerification.objects.filter(**data, purpose=_PURPOSE, is_confirmed=False).exists()
    response = __get_response(api_client, data=data, status_codes=ValidationError)
    assert response.data == [TEST_USER_VERIFICATION_CODE_REQUIRED]


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)}, {"email": get_random_email()}))
def test__test_user__code_not_sending(api_client, monkeypatch, data: dict, get_user_fi):
    monkeypatch.setattr(SendSMS, "verification_code", lambda *a, **kw: raise_test_error())
    monkeypatch.setattr(SendEmail, "verification_code", lambda *a, **kw: raise_test_error())
    user = get_user_fi(**data, is_test=True)
    ContactVerification.objects.create(**data, user=user, purpose=_PURPOSE, is_confirmed=False)
    response = __get_response(api_client, data=data)
    assert response.data
