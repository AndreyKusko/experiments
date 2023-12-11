import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, NotAuthenticated

from tests.utils import (
    RAISE_TEST_ERR,
    get_random_email,
    get_random_phone,
    raise_test_error,
    request_response_create,
)
from accounts.models import EMAIL_MUST_BE_UNIQ, PHONE_MUST_BE_UNIQ
from accounts.serializers.utils import parse_phone_number
from ma_saas.constants.constant import ContactVerificationPurpose
from accounts.serializers.validators import EMAIL_OR_PHONE_REQUIRE
from accounts.models.contact_verification import ContactVerification
from clients.notifications.interfaces.sms import SendSMS
from clients.notifications.interfaces.email import SendEmail
from accounts.serializers.contact.change_contact_code_send import (
    USER_EMAIL_REQUIRED,
    NEW_CONTACT_CODE_REQUIRED,
    OLD_CONTACT_CODE_REQUIRED,
    USER_VERIFIED_EMAIL_REQUIRED,
)

"""
Тестируется посылание кода
"""

User = get_user_model()

__get_response = functools.partial(request_response_create, path="/api/v1/change-contact/")
_PURPOSE = ContactVerificationPurpose.CHANGE_CONTACT.value


@pytest.mark.parametrize("contact", [{"phone": get_random_phone()}, {"email": get_random_email()}])
def test__anonymous__fail(api_client, monkeypatch, contact):
    response = __get_response(api_client, data=contact, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize(
    "data",
    ({"phone": get_random_phone(7)}, {"phone": get_random_phone(8)}, {"phone": get_random_phone()}),
)
def test__phone__success(api_client, monkeypatch, get_user_fi, data):
    monkeypatch.setattr(SendSMS, "send_sms_via_service_with_template", lambda *args, **kwargs: None)
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)

    phone = data["phone"]
    old_phone = parse_phone_number(raw_phone_number=get_random_phone(7))
    user = get_user_fi(phone=old_phone, email=get_random_email())

    assert not ContactVerification.objects.filter(user=user, purpose=_PURPOSE).exists()

    response = __get_response(api_client, user=user, data={"phone": phone})
    assert response.data == {}
    assert ContactVerification.objects.filter(
        user=user, email=user.email, purpose=_PURPOSE, is_confirmed=False
    ).exists()

    clean_phone = parse_phone_number(raw_phone_number=phone)
    assert ContactVerification.objects.filter(
        user=user, phone=clean_phone, purpose=_PURPOSE, is_confirmed=False
    ).exists()


@pytest.mark.parametrize("data", [{"email": get_random_email()}])
def test__email__success(api_client, monkeypatch, get_user_fi, data):
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    email = data["email"]
    user = get_user_fi(email=get_random_email())

    assert not ContactVerification.objects.filter(user=user, email=user.email, purpose=_PURPOSE).exists()
    assert not ContactVerification.objects.filter(user=user, email=email, purpose=_PURPOSE).exists()

    response = __get_response(api_client, user=user, data={"email": email})

    assert response.data == {}
    assert ContactVerification.objects.filter(
        user=user, email=user.email, purpose=_PURPOSE, is_confirmed=False
    ).exists()
    assert ContactVerification.objects.filter(
        user=user, email=email, purpose=_PURPOSE, is_confirmed=False
    ).exists()


@pytest.mark.parametrize("data", [{"email": get_random_email()}, {"phone": get_random_phone(7)}])
def test__if_send_fail__fail(api_client, monkeypatch, get_user_fi, data):
    monkeypatch.setattr(
        SendSMS, "send_sms_via_service_with_template", lambda *args, **kwargs: raise_test_error()
    )
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: raise_test_error())
    user = get_user_fi(email=get_random_email())
    assert not ContactVerification.objects.filter(user=user, purpose=_PURPOSE).exists()
    response = __get_response(api_client, user=user, data=data, status_codes=ValidationError)
    assert response.data == [RAISE_TEST_ERR]


@pytest.mark.parametrize("data", [{"email": get_random_email()}, {"phone": get_random_phone(7)}])
@pytest.mark.parametrize(
    ("is_code_old", "err_msg"), [(True, NEW_CONTACT_CODE_REQUIRED), (False, OLD_CONTACT_CODE_REQUIRED)]
)  # должный существовать обе модель подтверждения на новый и старый контакт
def test__if_test_user__without_confirmation__fail(
    api_client, monkeypatch, get_user_fi, data, is_code_old, err_msg
):
    monkeypatch.setattr(
        SendSMS, "send_sms_via_service_with_template", lambda *args, **kwargs: raise_test_error()
    )
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: raise_test_error())
    user = get_user_fi(phone=get_random_phone(7), email=get_random_email(), is_test=True)
    if is_code_old:
        ContactVerification.objects.create(user=user, phone=user.phone, email=user.email, purpose=_PURPOSE)
    else:
        ContactVerification.objects.create(user=user, **data, purpose=_PURPOSE)
    response = __get_response(api_client, user=user, data=data, status_codes=ValidationError)
    assert response.data == [err_msg]


@pytest.mark.parametrize("data", [{"email": get_random_email()}, {"phone": get_random_phone(7)}])
def test__if_test_user__code_not_sending(api_client, monkeypatch, get_user_fi, data):
    monkeypatch.setattr(
        SendSMS, "send_sms_via_service_with_template", lambda *args, **kwargs: raise_test_error()
    )
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: raise_test_error())

    user = get_user_fi(phone=get_random_phone(7), email=get_random_email(), is_test=True)

    ContactVerification.objects.create(user=user, phone=user.phone, email=user.email, purpose=_PURPOSE)
    ContactVerification.objects.create(user=user, **data, purpose=_PURPOSE)

    response = __get_response(api_client, user=user, data=data)
    assert response.data == {}


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)},))
def test__duplicate_phone__fail(api_client, monkeypatch, get_user_fi, data):
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)
    # monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    phone = data["phone"]
    old_phone = parse_phone_number(raw_phone_number=get_random_phone(7))
    user = get_user_fi(phone=old_phone, email=get_random_email())
    clean_phone = parse_phone_number(raw_phone_number=phone)

    assert not ContactVerification.objects.filter(user=user, purpose=_PURPOSE).exists()
    _duplicate_user = get_user_fi(phone=clean_phone)
    response = __get_response(api_client, user=user, data={"phone": phone}, status_codes=ValidationError)
    assert response.data == {"phone": [PHONE_MUST_BE_UNIQ]}


@pytest.mark.parametrize("data", [{"email": get_random_email()}])
def test__duplicate_email__fail(api_client, monkeypatch, get_user_fi, data):
    # monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    email = data["email"]
    user = get_user_fi(email=get_random_email())

    assert not ContactVerification.objects.filter(user=user, email=user.email, purpose=_PURPOSE).exists()
    assert not ContactVerification.objects.filter(user=user, email=email, purpose=_PURPOSE).exists()

    _duplicate_user = get_user_fi(email=email)
    response = __get_response(api_client, user=user, data={"email": email}, status_codes=ValidationError)
    assert response.data == {"email": [EMAIL_MUST_BE_UNIQ]}


@pytest.mark.parametrize(
    "data",
    ({"phone": get_random_phone(7)}, {"phone": get_random_phone(8)}, {"phone": get_random_phone()}),
)
def test__user_without_email__fail(api_client, monkeypatch, get_user_fi, data):
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)
    # monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    phone = data["phone"]
    old_phone = parse_phone_number(raw_phone_number=get_random_phone(7))
    user = get_user_fi(phone=old_phone)
    assert not user.email
    assert not ContactVerification.objects.filter(user=user, purpose=_PURPOSE).exists()
    response = __get_response(api_client, user=user, data={"phone": phone}, status_codes=ValidationError)
    assert response.data == {"non_field_errors": [USER_EMAIL_REQUIRED]}


@pytest.mark.parametrize("data", [{"email": get_random_email()}])
def test__not_verified_email__success(api_client, monkeypatch, get_user_fi, data):
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    email = data["email"]
    user = get_user_fi(email=get_random_email(), is_verified_email=False)
    assert not user.is_verified_email

    response = __get_response(api_client, user=user, data={"email": email}, status_codes=ValidationError)
    assert response.data == {"non_field_errors": [USER_VERIFIED_EMAIL_REQUIRED]}


def test__no_contact__fail(api_client, get_user_fi):
    user = get_user_fi(email=get_random_email())
    assert not ContactVerification.objects.filter(user=user, purpose=_PURPOSE).exists()

    response = __get_response(api_client, user=user, data={}, status_codes=ValidationError)

    assert response.data == {"non_field_errors": [EMAIL_OR_PHONE_REQUIRE]}
    assert not ContactVerification.objects.filter(
        user=user, email=user.email, purpose=_PURPOSE, is_confirmed=False
    ).exists()


@pytest.mark.parametrize("email", ["t", 123, "123", "t.tt", "t@mail"])
def test__invalid_email__fail(api_client, get_user_fi, email):
    user = get_user_fi(email=get_random_email())
    assert not ContactVerification.objects.filter(user=user, purpose=_PURPOSE).exists()

    response = __get_response(api_client, user=user, data={"email": email}, status_codes=ValidationError)
    assert response.data == {"email": ["Enter a valid email address."]}
    assert not ContactVerification.objects.filter(
        user=user, email=user.email, purpose=_PURPOSE, is_confirmed=False
    ).exists()
    assert not ContactVerification.objects.filter(
        user=user, email=email, purpose=_PURPOSE, is_confirmed=False
    ).exists()


@pytest.mark.parametrize(
    ("phone", "err_txt"),
    [
        ("77878", "Ensure this field has at least 10 characters."),
        ("71234512036789123", "Ensure this field has no more than 16 characters."),
        ("qwйждйцбвe", "Телефон не должен иметь букв."),
    ],
)
def test__invalid_phone__fail(api_client, get_user_fi, phone, err_txt):
    old_phone = parse_phone_number(raw_phone_number=get_random_phone())
    user = get_user_fi(email=get_random_email(), phone=old_phone)
    assert not ContactVerification.objects.filter(user=user, purpose=_PURPOSE).exists()

    response = __get_response(api_client, user=user, data={"phone": phone}, status_codes=ValidationError)
    assert response.data == {"phone": [err_txt]}
    assert not ContactVerification.objects.filter(
        user=user, email=user.email, purpose=_PURPOSE, is_confirmed=False
    ).exists()
    assert not ContactVerification.objects.filter(
        user=user, phone=phone, purpose=_PURPOSE, is_confirmed=False
    ).exists()
