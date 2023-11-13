import datetime as dt
import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import get_random_email, get_random_phone, request_response_update
from accounts.models import EMAIL_MUST_BE_UNIQ, PHONE_MUST_BE_UNIQ
from accounts.serializers.utils import parse_phone_number
from ma_saas.constants.constant import ContactVerificationPurpose
from accounts.serializers.validators import EMAIL_OR_PHONE_REQUIRE, CONTACT_VERIFICATION_CODE_EXPIRED
from accounts.models.contact_verification import VERIFICATION_CODE_EXPIRATION_TD, ContactVerification
from accounts.serializers.contact.change_contact import (
    ACTIVE_VERIFICATION_NEW_CONTACT_NOT_FOUND,
    ACTIVE_VERIFICATION_CURRENT_CONTACT_NOT_FOUND,
)

"""
Тестируется замена контакта 
"""

User = get_user_model()

__get_response = functools.partial(request_response_update, path="/api/v1/change-contact/")
_PURPOSE = dict(purpose=ContactVerificationPurpose.CHANGE_CONTACT.value)


@pytest.mark.parametrize("contact", [{"phone": get_random_phone()}, {"email": get_random_email()}])
def test__anonymous__fail(api_client, monkeypatch, get_user_fi, contact):
    user = get_user_fi(phone=get_random_phone(), email=get_random_email())

    response = __get_response(api_client, instance_id=user.id, data=contact, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize(
    "data", [{"phone": get_random_phone(7)}, {"phone": get_random_phone(8)}, {"phone": get_random_phone()}]
)
def test__phone__success(api_client, get_user_fi, data):
    phone = data["phone"]
    old_phone = parse_phone_number(raw_phone_number=get_random_phone())
    assert old_phone != phone
    user = get_user_fi(phone=old_phone, email=get_random_email())
    assert user.is_verified_phone

    current_contact_cv = ContactVerification.objects.create(user=user, email=user.email, **_PURPOSE)
    assert not current_contact_cv.is_confirmed

    clean_phone = parse_phone_number(raw_phone_number=phone)
    new_contact_cv = ContactVerification.objects.create(user=user, phone=clean_phone, **_PURPOSE)
    assert not new_contact_cv.is_confirmed

    response = __get_response(
        api_client,
        instance_id=user.id,
        user=user,
        data={
            "phone": phone,
            "current_contact_small_code": current_contact_cv.small_code,
            "new_contact_small_code": new_contact_cv.small_code,
        },
    )
    assert response.data == {"email": user.email, "id": user.id, "phone": clean_phone}
    updated_current_contact_cv = ContactVerification.objects.get(id=current_contact_cv.id)
    assert updated_current_contact_cv.is_confirmed
    new_contact_cv = ContactVerification.objects.get(id=new_contact_cv.id)
    assert new_contact_cv.is_confirmed
    updated_user = User.objects.get(id=user.id)
    assert updated_user.phone == clean_phone
    assert updated_user.is_verified_phone


@pytest.mark.parametrize("data", [{"email": get_random_email()}])
def test__email__success(api_client, get_user_fi, data):
    email = data["email"]
    old_email = get_random_email()
    assert old_email != email
    user = get_user_fi(email=old_email)
    assert user.is_verified_email

    current_contact_cv = ContactVerification.objects.create(user=user, email=user.email, **_PURPOSE)
    assert not current_contact_cv.is_confirmed

    new_contact_cv = ContactVerification.objects.create(user=user, email=email, **_PURPOSE)
    assert not new_contact_cv.is_confirmed

    response = __get_response(
        api_client,
        instance_id=user.id,
        user=user,
        data={
            "email": email,
            "current_contact_small_code": current_contact_cv.small_code,
            "new_contact_small_code": new_contact_cv.small_code,
        },
    )
    assert response.data == {"email": email, "id": user.id, "phone": None}
    updated_current_contact_cv = ContactVerification.objects.get(id=current_contact_cv.id)
    assert updated_current_contact_cv.is_confirmed
    updated_new_contact_cv = ContactVerification.objects.get(id=new_contact_cv.id)
    assert updated_new_contact_cv.is_confirmed
    updated_user = User.objects.get(id=user.id)
    assert updated_user.email == email
    assert updated_user.is_verified_email


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)}, {"email": get_random_email()}))
@pytest.mark.parametrize("cv", ("current_contact_cv", "new_contact_cv"))
def test__expired_cv__fail(api_client, not_mock_datetime, data: dict, get_user_fi, cv):
    old_phone = parse_phone_number(raw_phone_number=get_random_phone())

    check_data = {k: v for k, v in data.items() if v}
    if data.get("phone"):
        check_data["phone"] = parse_phone_number(raw_phone_number=data.get("phone"))
        assert old_phone != check_data["phone"]

    old_email = get_random_email()
    if email := data.get("email"):
        assert old_email != email

    user = get_user_fi(phone=old_phone, email=old_email)

    current_contact_cv = ContactVerification.objects.create(user=user, email=user.email, **_PURPOSE)
    assert not current_contact_cv.is_confirmed
    new_contact_cv = ContactVerification.objects.create(user=user, **check_data, **_PURPOSE)
    assert not new_contact_cv.is_confirmed

    if cv == "new_contact_cv":
        instance = new_contact_cv
    elif cv == "current_contact_cv":
        instance = current_contact_cv
    instance.created_at = instance.created_at - VERIFICATION_CODE_EXPIRATION_TD - dt.timedelta(minutes=1)
    instance.save()
    data = {
        **check_data,
        "current_contact_small_code": current_contact_cv.small_code,
        "new_contact_small_code": new_contact_cv.small_code,
    }
    response = __get_response(
        api_client, instance_id=user.id, user=user, data=data, status_codes=ValidationError
    )
    assert response.data == [CONTACT_VERIFICATION_CODE_EXPIRED]


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)}, {"email": get_random_email()}))
@pytest.mark.parametrize(
    ("cv", "err_msg"),
    [
        ("current_contact_cv", ACTIVE_VERIFICATION_CURRENT_CONTACT_NOT_FOUND),
        ("new_contact_cv", ACTIVE_VERIFICATION_NEW_CONTACT_NOT_FOUND),
    ],
)
def test__confirmed_cv__fail(api_client, data: dict, get_user_fi, cv, err_msg):
    old_phone = parse_phone_number(raw_phone_number=get_random_phone())

    check_data = {k: v for k, v in data.items() if v}
    if data.get("phone"):
        check_data["phone"] = parse_phone_number(raw_phone_number=data.get("phone"))
        assert old_phone != check_data["phone"]

    old_email = get_random_email()
    if email := data.get("email"):
        assert old_email != email

    user = get_user_fi(phone=old_phone, email=old_email)

    current_contact_cv = ContactVerification.objects.create(user=user, email=user.email, **_PURPOSE)
    assert not current_contact_cv.is_confirmed
    new_contact_cv = ContactVerification.objects.create(user=user, **check_data, **_PURPOSE)
    assert not new_contact_cv.is_confirmed

    if cv == "new_contact_cv":
        instance = new_contact_cv
    elif cv == "current_contact_cv":
        instance = current_contact_cv
    instance.is_confirmed = True
    instance.save()
    data = {
        **check_data,
        "current_contact_small_code": current_contact_cv.small_code,
        "new_contact_small_code": new_contact_cv.small_code,
    }
    response = __get_response(
        api_client, instance_id=user.id, user=user, data=data, status_codes=ValidationError
    )
    assert response.data == [err_msg]


@pytest.mark.parametrize("data", [{"email": get_random_email()}])
def test__email_duplicate__fail(api_client, get_user_fi, data):
    new_email = data["email"]
    old_email = (get_random_email(),)
    assert old_email != new_email
    user = get_user_fi(email=old_email)
    assert user.is_verified_email

    current_contact_cv = ContactVerification.objects.create(user=user, email=user.email, **_PURPOSE)
    assert not current_contact_cv.is_confirmed

    new_contact_cv = ContactVerification.objects.create(user=user, email=new_email, **_PURPOSE)
    assert not new_contact_cv.is_confirmed

    _duplicate_user = get_user_fi(email=new_email)
    response = __get_response(
        api_client,
        instance_id=user.id,
        user=user,
        data={
            "email": new_email,
            "current_contact_small_code": current_contact_cv.small_code,
            "new_contact_small_code": new_contact_cv.small_code,
        },
        status_codes=ValidationError,
    )
    assert response.data == [EMAIL_MUST_BE_UNIQ]


@pytest.mark.parametrize("data", [{"phone": get_random_phone(7)}])
def test__phone_duplicate__fail(api_client, get_user_fi, data):
    new_phone = data["phone"]
    old_phone = parse_phone_number(raw_phone_number=get_random_phone())
    assert old_phone != new_phone
    user = get_user_fi(phone=old_phone, email=get_random_email())
    assert user.is_verified_phone

    current_contact_cv = ContactVerification.objects.create(user=user, email=user.email, **_PURPOSE)
    assert not current_contact_cv.is_confirmed

    clean_phone = parse_phone_number(raw_phone_number=new_phone)
    new_contact_cv = ContactVerification.objects.create(user=user, phone=clean_phone, **_PURPOSE)
    assert not new_contact_cv.is_confirmed
    _duplicate_user = get_user_fi(phone=clean_phone)

    response = __get_response(
        api_client,
        instance_id=user.id,
        user=user,
        data={
            "phone": new_phone,
            "current_contact_small_code": current_contact_cv.small_code,
            "new_contact_small_code": new_contact_cv.small_code,
        },
        status_codes=ValidationError,
    )
    assert response.data == [PHONE_MUST_BE_UNIQ]


def test__no_contact__fail(api_client, get_user_fi):
    old_email, email = get_random_email(), get_random_email()
    assert old_email != email
    user = get_user_fi(email=old_email)
    assert user.is_verified_email

    response = __get_response(
        api_client,
        instance_id=user.id,
        user=user,
        data={"current_contact_small_code": 1234, "new_contact_small_code": 1234},
        status_codes=ValidationError,
    )
    assert response.data == [EMAIL_OR_PHONE_REQUIRE]
    updated_user = User.objects.get(id=user.id)
    assert updated_user.is_verified_email
    assert updated_user.email == old_email


@pytest.mark.parametrize("email", ["t", 123, "123", "t.tt", "t@mail"])
def test__invalid_email__fail(api_client, get_user_fi, email):
    old_email = get_random_email()
    assert old_email != email
    user = get_user_fi(email=old_email)

    response = __get_response(
        api_client,
        instance_id=user.id,
        user=user,
        data={"email": email, "current_contact_small_code": 1234, "new_contact_small_code": 1234},
        status_codes=ValidationError,
    )

    assert response.data == {"email": ["Enter a valid email address."]}

    updated_user = User.objects.get(id=user.id)
    assert updated_user.is_verified_email
    assert updated_user.email == old_email


@pytest.mark.parametrize(
    ("phone", "err_txt"),
    [
        ("77878", "Ensure this field has at least 10 characters."),
        ("71234512036789123", "Ensure this field has no more than 16 characters."),
        ("qwйждйцбвe", "Телефон не должен иметь букв."),
    ],
)
def test__invalid_phone__fail(api_client, get_user_fi, phone, err_txt):
    user = get_user_fi(email=get_random_email(), phone=get_random_phone(7))
    assert user.phone != phone

    response = __get_response(
        api_client,
        instance_id=user.id,
        user=user,
        data={"phone": phone, "current_contact_small_code": 1234, "new_contact_small_code": 1234},
        status_codes=ValidationError,
    )
    assert response.data == {"phone": [err_txt]}
    updated_user = User.objects.get(id=user.id)
    assert updated_user.is_verified_phone
    assert updated_user.phone == user.phone


@pytest.mark.parametrize("data", [{"email": get_random_email()}])
def test__another_user__fail(api_client, get_user_fi, data):
    email = data["email"]
    old_email = (get_random_email(),)
    assert old_email != email
    user = get_user_fi(email=old_email)
    assert user.is_verified_email

    current_contact_cv = ContactVerification.objects.create(user=user, email=user.email, **_PURPOSE)
    assert not current_contact_cv.is_confirmed

    new_contact_cv = ContactVerification.objects.create(user=user, email=email, **_PURPOSE)
    assert not new_contact_cv.is_confirmed

    another_user = get_user_fi(email=get_random_email())
    assert another_user.is_verified_email

    response = __get_response(
        api_client,
        instance_id=another_user.id,
        user=user,
        data={
            "email": email,
            "current_contact_small_code": current_contact_cv.small_code,
            "new_contact_small_code": new_contact_cv.small_code,
        },
        status_codes=PermissionDenied,
    )
    assert response.data == {"detail": PermissionDenied.default_detail}
    updated_user = User.objects.get(id=another_user.id)
    assert updated_user.email == another_user.email
    assert updated_user.is_verified_email
