import functools

import pytest
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.core.validators import EmailValidator
from rest_framework.exceptions import ValidationError

from tests.utils import (
    RAISE_TEST_ERR,
    get_random_email,
    get_random_phone,
    raise_test_error,
    request_response_create,
)
from ma_saas.constants.company import CompanyUserStatus
from ma_saas.constants.constant import ContactVerificationPurpose
from accounts.serializers.validators import EMAIL_OR_PHONE_REQUIRE
from accounts.models.contact_verification import ContactVerification
from clients.notifications.interfaces.sms import SendSMS
from clients.notifications.interfaces.email import SendEmail
from accounts.serializers.password.password_reset import TEST_USER_RESET_PASSWORD_CODE_REQUIRED

User = get_user_model()

__get_response = functools.partial(request_response_create, path="/api/v1/reset-password/")
_PURPOSE = ContactVerificationPurpose.PASSWORD_SET.value


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)}, {"email": get_random_email()}))
@pytest.mark.parametrize("is_authorised", (True, False))
def test__success(api_client, monkeypatch, get_user_fi, data, is_authorised):
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)
    user = get_user_fi(**data)
    assert not ContactVerification.objects.filter(Q(user=user) | Q(**data), purpose=_PURPOSE).exists()
    response = __get_response(api_client, data=data, user=user if is_authorised else None)
    contact_verifications = ContactVerification.objects.filter(user=user, purpose=_PURPOSE)
    assert contact_verifications.count() == 1
    contact_verification = contact_verifications.first()
    assert contact_verification.small_code
    assert not contact_verification.is_confirmed
    assert not response.exception
    assert not response.data


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)}, {"email": get_random_email()}))
def test__send_fail__fail(api_client, monkeypatch, get_user_fi, data):
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: raise_test_error())
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: raise_test_error())
    user = get_user_fi(**data)
    assert not ContactVerification.objects.filter(user=user, purpose=_PURPOSE).exists()
    response = __get_response(api_client, data=data, user=user, status_codes=ValidationError)
    assert response.data == [RAISE_TEST_ERR]
    assert ContactVerification.objects.filter(user=user, purpose=_PURPOSE, is_confirmed=False).exists()


def test__several_requests__success(api_client, monkeypatch, get_user_fi):
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    user = get_user_fi(email=get_random_email())

    assert not ContactVerification.objects.filter(user=user, purpose=_PURPOSE, is_confirmed=False).exists()
    response1 = __get_response(api_client, data={"email": user.email})
    contact_verifications = ContactVerification.objects.filter(
        user=user, purpose=_PURPOSE, is_confirmed=False
    )
    assert len(contact_verifications) == 1
    assert not response1.exception
    assert not response1.data

    assert ContactVerification.objects.filter(user=user, purpose=_PURPOSE).exists()
    response2 = __get_response(api_client, data={"email": user.email})
    contact_verifications = ContactVerification.objects.filter(
        user=user, purpose=_PURPOSE, is_confirmed=False
    )
    assert not response2.exception
    assert not response2.data

    assert len(contact_verifications) == 2
    for contact_verification in contact_verifications:
        assert contact_verification.small_code
        assert not contact_verification.is_confirmed


@pytest.mark.parametrize("status", CompanyUserStatus.values)
def test__without_contact__fail(api_client, monkeypatch, status):
    response = __get_response(api_client, data={}, status_codes=ValidationError)
    assert response.exception
    assert response.data["non_field_errors"][0] == EMAIL_OR_PHONE_REQUIRE


def test__not_existing_email_user__success(api_client):
    response = __get_response(api_client, data={"email": get_random_email()})
    assert not response.exception
    assert not response.data


def test__not_email__fail(api_client):
    response = __get_response(api_client, data={"email": get_random_string()}, status_codes=ValidationError)
    assert response.data["email"][0] == EmailValidator.message


@pytest.mark.parametrize("data", [{"email": get_random_email()}, {"phone": get_random_phone(7)}])
def test__if_test_user__without_confirmation__fail(api_client, monkeypatch, get_user_fi, data):
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: raise_test_error())
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: raise_test_error())

    user = get_user_fi(**data, is_test=True)
    assert not ContactVerification.objects.filter(
        Q(user=user) | Q(**data), purpose=_PURPOSE, is_confirmed=False
    ).exists()
    response = __get_response(api_client, data=data, user=user, status_codes=ValidationError)
    assert response.data == [TEST_USER_RESET_PASSWORD_CODE_REQUIRED]
    assert not ContactVerification.objects.filter(
        Q(user=user) | Q(**data), purpose=_PURPOSE, is_confirmed=False
    ).exists()


@pytest.mark.parametrize("data", [{"email": get_random_email()}, {"phone": get_random_phone(7)}])
def test__if_test_user__with_confirmation__code_not_send(api_client, monkeypatch, get_user_fi, data):
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: raise_test_error())
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: raise_test_error())

    user = get_user_fi(**data, is_test=True)

    ContactVerification.objects.create(user=user, **data, purpose=_PURPOSE, is_confirmed=False)
    response = __get_response(api_client, data=data, user=user)
    assert response.data == {}
    assert ContactVerification.objects.filter(
        Q(user=user) | Q(**data), purpose=_PURPOSE, is_confirmed=False
    ).exists()
