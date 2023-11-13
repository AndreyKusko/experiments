import datetime as dt
import functools

import pytest
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework.exceptions import NotFound, ValidationError

from tests.utils import get_random_int, get_random_email, get_random_phone, request_response_create
from ma_saas.utils import system
from tests.fixtures.user import LONG_TEST_PASSWORD
from accounts.permissions import CONFIRMATION_TOKEN_EXPIRED
from accounts.models.token import Token
from ma_saas.constants.company import CUR
from ma_saas.constants.constant import ContactVerificationPurpose
from accounts.serializers.validators import NO_CODE
from accounts.models.contact_verification import VERIFICATION_CODE_EXPIRATION, ContactVerification
from accounts.serializers.password.password_set import SET_PASSWORD_CODE_INVALID, SET_PASSWORD_CODE_NOT_FOUND

User = get_user_model()


__get_response = functools.partial(request_response_create, path="/api/v1/set-password/")

_PURPOSE = ContactVerificationPurpose.PASSWORD_SET.value


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)}, {"email": get_random_email()}))
@pytest.mark.parametrize("is_authorised", (True, False))
@pytest.mark.parametrize("is_user_with_password", (True, False))
def test__small_code__success(api_client, get_user_fi, data, is_authorised, is_user_with_password):
    r_user = get_user_fi(**data)
    if not is_user_with_password:
        r_user.password = ""
        r_user.save()

    new_password = get_random_string()
    assert not r_user.check_password(new_password)
    cv = ContactVerification.objects.create(user=r_user, **data, purpose=_PURPOSE)
    assert not cv.is_confirmed

    data = {**data, "password": new_password, "small_code": cv.small_code}
    response = __get_response(api_client, data=data, user=r_user if is_authorised else None)
    cv = ContactVerification.objects.get(id=cv.id)
    assert cv.small_code
    assert cv.is_confirmed
    assert response.data == {}
    assert cv.user.check_password(new_password)


@pytest.mark.parametrize("data", ({"email": get_random_email()},))
@pytest.mark.parametrize("is_authorised", (True, False))
@pytest.mark.parametrize("is_user_with_password", (True, False))
def test__code__success(api_client, get_user_fi, data, is_authorised, is_user_with_password):
    r_user = get_user_fi(**data, is_verified_email=False)
    if not is_user_with_password:
        r_user.password = ""
        r_user.save()
    assert not r_user.is_verified_email
    new_password = get_random_string()
    assert not r_user.check_password(new_password)
    cv = ContactVerification.objects.create(
        user=r_user, **data, purpose=ContactVerificationPurpose.INVITED_CU_PASSWORD_SET.value
    )
    assert not cv.is_confirmed

    data = {**data, "password": new_password, "code": cv.large_code}
    response = __get_response(api_client, data=data, user=r_user if is_authorised else None)
    cv = ContactVerification.objects.get(id=cv.id)
    assert not cv.small_code
    assert cv.large_code
    assert cv.is_confirmed
    assert response.data == {}
    assert cv.user.check_password(new_password)
    created_user = User.objects.get(id=r_user.id)

    assert created_user.is_verified_email


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)}, {"email": get_random_email()}))
def test__existing_token_deleted(api_client, get_user_fi, data):
    user = get_user_fi(**data)
    cv = ContactVerification.objects.create(user=user, **data, purpose=_PURPOSE)
    assert not cv.is_confirmed
    assert not cv.is_confirmed

    Token.objects.create(user=user)
    data = {**data, "password": LONG_TEST_PASSWORD, "small_code": cv.small_code}
    response = __get_response(api_client, data=data, user=user)
    cv = ContactVerification.objects.filter(user=user, purpose=_PURPOSE).order_by("id").last()
    assert cv
    assert cv.small_code
    assert cv.is_confirmed
    assert not response.exception
    assert not response.data
    assert not Token.objects.filter(user=user).exists()


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)}, {"email": get_random_email()}))
def test__not_verified_contact_confirmed(api_client, get_user_fi, data):
    user = get_user_fi(**data, is_verified_email=False, is_verified_phone=False)
    assert not user.is_verified_email
    assert not user.is_verified_phone

    cv = ContactVerification.objects.create(user=user, **data, purpose=_PURPOSE)
    data = {**data, "password": LONG_TEST_PASSWORD, "small_code": cv.small_code}
    assert not cv.is_confirmed
    response = __get_response(api_client, data=data, user=user)
    assert not response.data
    updated_user = User.objects.get(id=user.id)
    assert not updated_user.is_verified_phone
    assert not updated_user.is_verified_email


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)}, {"email": get_random_email()}))
def test__wrong_token__fail(monkeypatch, api_client, get_user_fi, data):
    r_user = get_user_fi(**data)
    cv = ContactVerification.objects.create(user=r_user, **data, purpose=_PURPOSE)
    assert not cv.is_confirmed
    data = {**data, "password": LONG_TEST_PASSWORD, "small_code": get_random_int(length=4)}
    response = __get_response(api_client, data=data, status_codes=NotFound)
    assert response.data == {"detail": SET_PASSWORD_CODE_INVALID}


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)}, {"email": get_random_email()}))
def test__confirmed_token__fail(monkeypatch, api_client, get_user_fi, data):

    r_user = get_user_fi(**data)
    cv = ContactVerification.objects.create(user=r_user, **data, is_confirmed=True)
    assert cv.is_confirmed
    data = {**data, "password": LONG_TEST_PASSWORD, "small_code": cv.small_code}
    response = __get_response(api_client, data=data, status_codes=NotFound)
    assert response.data == {"detail": SET_PASSWORD_CODE_NOT_FOUND}


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)}, {"email": get_random_email()}))
def test__expired_token__fail(monkeypatch, api_client, get_user_fi, data):

    r_user = get_user_fi(**data)
    created_at = system.get_now() - dt.timedelta(seconds=VERIFICATION_CODE_EXPIRATION + 1)
    cv = ContactVerification.objects.create(user=r_user, **data, purpose=_PURPOSE)
    cv.created_at = created_at
    cv.save()
    assert not cv.is_confirmed
    data = {**data, "password": LONG_TEST_PASSWORD, "small_code": cv.small_code}
    response = __get_response(api_client, data=data, status_codes=ValidationError)
    assert response.data == [CONFIRMATION_TOKEN_EXPIRED]


@pytest.mark.parametrize(
    ("field", "err"),
    (
        ("password", {"password": ["This field is required."]}),
        ("small_code", {"non_field_errors": [NO_CODE]}),
    ),
)
def test__lost_field__required(monkeypatch, api_client, get_cu_fi, field, err):
    r_cu = get_cu_fi(role=CUR.OWNER)
    cv = ContactVerification.objects.create(user=r_cu.user)
    assert cv.is_totally_active_()
    data = {"password": LONG_TEST_PASSWORD, "small_code": cv.small_code}
    del data[field]
    response = __get_response(api_client, data=data, status_codes=ValidationError)
    assert response.data == err
