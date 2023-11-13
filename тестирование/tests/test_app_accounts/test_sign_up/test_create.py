import functools
from copy import deepcopy

import pytest
from django.contrib.auth import get_user_model
from django.core.validators import EmailValidator
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from tests.utils import get_random_email, get_random_phone, request_response_create
from accounts.utils import CONTACT_NOT_FOUND, NOT_FOUND_NOT_CONFIRMED_CONTACT
from tests.fixtures.user import LONG_TEST_PASSWORD, SHORT_TEST_PASSWORD
from accounts.models.token import Token
from accounts.serializers.utils import PHONE_MUST_HAVE_NUMBERS_ONLY
from ma_saas.constants.constant import CONTACT_VERIFICATION_PURPOSE
from accounts.serializers.sign_up import (
    EMAIL_REQUIRE_CV_EMAIL_TOKEN,
    PHONE_REQUIRE_CV_PHONE_TOKEN,
    AT_LEAST_SINGLE_CONTACT_REQUIRED,
)
from accounts.models.contact_verification import ContactVerification

User = get_user_model()


__get_response = functools.partial(request_response_create, path="/api/v1/sign-up/")


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)}, {"email": get_random_email()}))
def test__single_contacts__success(api_client, monkeypatch, new_user_data, data):
    # phone = get_random_phone(7)
    contacts = deepcopy(data)
    cv = ContactVerification.objects.create(**data, purpose=CONTACT_VERIFICATION_PURPOSE)
    assert cv.small_code and not cv.is_confirmed
    assert not User.objects.filter(**data).exists()

    data = new_user_data(**data, password=LONG_TEST_PASSWORD)

    if data.get("phone"):
        data["phone_verification_code"] = cv.small_code
    if data.get("email"):
        data["email_verification_code"] = cv.small_code
    response = __get_response(api_client, data=data)

    assert response.data and len(response.data) == 1
    created_instances = User.objects.filter(**contacts)
    assert created_instances.count() == 1
    created_instance = created_instances.first()
    if data.get("phone"):
        assert created_instance.phone == data.get("phone")
        assert not created_instance.email
        assert created_instance.is_verified_phone
        assert not created_instance.is_verified_email

    if data.get("email"):
        assert created_instance.email == data.get("email")
        assert not created_instance.phone

        assert not created_instance.is_verified_phone
        assert created_instance.is_verified_email
    assert created_instance.check_password(LONG_TEST_PASSWORD)

    updated_phone_cv = ContactVerification.objects.get(id=cv.id)
    assert updated_phone_cv.is_confirmed

    token = Token.objects.get(user=created_instance)
    assert response.data["key"] == token.key


def test__via_email_and_phone__success(api_client, monkeypatch, new_user_data):
    email = get_random_email()
    email_cv = ContactVerification.objects.create(email=email, purpose=CONTACT_VERIFICATION_PURPOSE)
    assert email_cv.small_code and not email_cv.is_confirmed
    assert not User.objects.filter(email=email).exists()

    phone = get_random_phone("7")
    phone_cv = ContactVerification.objects.create(phone=phone, purpose=CONTACT_VERIFICATION_PURPOSE)
    assert phone_cv.small_code and not phone_cv.is_confirmed
    assert not User.objects.filter(phone=phone).exists()

    cv_data = {"phone_verification_code": phone_cv.small_code, "email_verification_code": email_cv.small_code}
    data = new_user_data(email=email, phone=phone, password=LONG_TEST_PASSWORD)
    # [data.pop(field_name, None) for field_name in ("is_password", "is_blocked")]
    response = __get_response(api_client, data={**data, **cv_data})

    assert response.data and len(response.data) == 1
    created_instances = User.objects.filter(email=email, phone=phone)
    assert created_instances.count() == 1
    created_instance = created_instances.first()
    assert created_instance.email == email
    assert created_instance.phone == phone
    assert created_instance.is_verified_email
    assert created_instance.is_verified_phone
    assert created_instance.check_password(LONG_TEST_PASSWORD)

    updated_email_cv = ContactVerification.objects.get(id=email_cv.id)
    assert updated_email_cv.is_confirmed

    updated_phone_cv = ContactVerification.objects.get(id=phone_cv.id)
    assert updated_phone_cv.is_confirmed

    token = Token.objects.get(user=created_instance)
    assert response.data["key"] == token.key


@pytest.mark.parametrize("password", (LONG_TEST_PASSWORD, SHORT_TEST_PASSWORD))
def test__different_passwords__success(api_client, monkeypatch, new_user_data, password):
    email = get_random_email()
    email_cv = ContactVerification.objects.create(email=email, purpose=CONTACT_VERIFICATION_PURPOSE)
    assert email_cv.small_code and not email_cv.is_confirmed
    assert not User.objects.filter(email=email).exists()

    phone = get_random_phone("7")
    phone_cv = ContactVerification.objects.create(phone=phone, purpose=CONTACT_VERIFICATION_PURPOSE)
    assert phone_cv.small_code and not phone_cv.is_confirmed
    assert not User.objects.filter(phone=phone).exists()

    data = new_user_data(email=email, phone=phone, password=password)
    # [data.pop(field_name, None) for field_name in ("is_password", "is_blocked")]

    data["phone_verification_code"] = phone_cv.small_code
    data["email_verification_code"] = email_cv.small_code
    response = __get_response(api_client, data=data)

    assert response.data and len(response.data) == 1
    created_instances = User.objects.filter(email=email, phone=phone)
    assert created_instances.count() == 1
    created_instance = created_instances.first()
    assert created_instance.email == email
    assert created_instance.phone == phone
    assert created_instance.is_verified_email
    assert created_instance.is_verified_phone
    assert created_instance.check_password(password)

    updated_email_cv = ContactVerification.objects.get(id=email_cv.id)
    assert updated_email_cv.is_confirmed

    updated_phone_cv = ContactVerification.objects.get(id=phone_cv.id)
    assert updated_phone_cv.is_confirmed

    token = Token.objects.get(user=created_instance)
    assert response.data["key"] == token.key


@pytest.mark.parametrize(
    ("contact", "cv_key", "password", "err"),
    [
        (
            {"phone": get_random_phone()},
            "",
            LONG_TEST_PASSWORD,
            {"non_field_errors": [PHONE_REQUIRE_CV_PHONE_TOKEN]},
        ),
        (
            {"phone": get_random_phone()},
            "phone_verification_code",
            "",
            {"password": ["This field is required."]},
        ),
        (
            {"phone": 123},
            "phone_verification_code",
            LONG_TEST_PASSWORD,
            {"non_field_errors": [CONTACT_NOT_FOUND]},
        ),
        (
            {"phone": "qwe"},
            "phone_verification_code",
            LONG_TEST_PASSWORD,
            {"phone": [PHONE_MUST_HAVE_NUMBERS_ONLY]},
        ),
        (
            {"phone": ""},
            "phone_verification_code",
            LONG_TEST_PASSWORD,
            {"non_field_errors": [AT_LEAST_SINGLE_CONTACT_REQUIRED]},
        ),
        (
            {},
            "phone_verification_code",
            LONG_TEST_PASSWORD,
            {"non_field_errors": [AT_LEAST_SINGLE_CONTACT_REQUIRED]},
        ),
        (
            {"email": get_random_email()},
            "",
            LONG_TEST_PASSWORD,
            {"non_field_errors": [EMAIL_REQUIRE_CV_EMAIL_TOKEN]},
        ),
        (
            {"email": get_random_email()},
            "email_verification_code",
            "",
            {"password": ["This field is required."]},
        ),
        ({"email": 123}, "email_verification_code", LONG_TEST_PASSWORD, {"email": [EmailValidator.message]}),
        (
            {"email": "qwe@qwe"},
            "email_verification_code",
            LONG_TEST_PASSWORD,
            {"email": [EmailValidator.message]},
        ),
        (
            {"email": ""},
            "email_verification_code",
            LONG_TEST_PASSWORD,
            {"non_field_errors": [AT_LEAST_SINGLE_CONTACT_REQUIRED]},
        ),
        (
            {},
            "email_verification_code",
            LONG_TEST_PASSWORD,
            {"non_field_errors": [AT_LEAST_SINGLE_CONTACT_REQUIRED]},
        ),
    ],
)
def test__contact_and_password_data_problems__fail(
    api_client, monkeypatch, contact, cv_key, password, err, new_user_data
):
    cv = ContactVerification.objects.create(**contact, purpose=CONTACT_VERIFICATION_PURPOSE)
    assert cv.small_code and not cv.is_confirmed
    if contact and list(contact.values())[0]:
        assert not User.objects.filter(**contact).exists()
    data = {**contact}
    if cv_key:
        data[cv_key] = cv.small_code
    if password:
        data["password"] = LONG_TEST_PASSWORD

    user_data = new_user_data()
    [user_data.pop(fn, None) for fn in ("is_password", "is_blocked", "email", "phone", "password")]

    data = {**data, **user_data}
    response = __get_response(api_client, data=data, status_codes=ValidationError)
    assert response.data == err


@pytest.mark.parametrize(
    "pop_field", ["first_name", "last_name", "middle_name", "city", "lat", "lon", "gender", "birthdate"]
)
@pytest.mark.parametrize("pop_contact", ["phone", "email"])
def test__credential_and_position_data_problems__fail(
    api_client, monkeypatch, pop_field, pop_contact, new_user_data
):
    data = new_user_data()
    [data.pop(fn, None) for fn in ("is_password", "is_blocked", "phone", "email", pop_field)]

    contact_data = {"phone": get_random_phone(7), "email": get_random_email()}
    contact_data.pop(pop_contact)
    assert not User.objects.filter(**contact_data).exists()

    cv = ContactVerification.objects.create(**contact_data, purpose=CONTACT_VERIFICATION_PURPOSE)
    assert cv.small_code and not cv.is_confirmed
    if "phone" in contact_data.keys():
        data["phone_verification_code"] = cv.small_code
    if "email" in contact_data.keys():
        data["email_verification_code"] = cv.small_code
    data = {**data, **contact_data}
    response = __get_response(api_client, data=data, status_codes=ValidationError)
    assert response.data[pop_field][0] == "This field is required."


@pytest.mark.parametrize("contacts", [{"email": get_random_email()}])
def test__contact_duplicates__fail(api_client, monkeypatch, contacts, new_user_data):
    data, cvs = {}, []
    for contact_name, value in contacts.items():
        contact_data = {contact_name: value}

        cv = ContactVerification.objects.create(**contact_data, purpose=CONTACT_VERIFICATION_PURPOSE)
        assert cv.small_code and not cv.is_confirmed
        cvs.append(cv)
        cv_key = "phone_verification_code" if contact_name == "phone" else "email_verification_code"
        data = {**data, **contact_data, cv_key: cv.small_code}
    User.objects.create(**contacts)
    assert User.objects.filter(**contacts).count() == 1

    fixture_data = new_user_data()
    [fixture_data.pop(fn, None) for fn in ("is_password", "is_blocked", "phone", "email")]
    data = {**data, **fixture_data}
    response = __get_response(api_client, data=data, status_codes=ValidationError)
    for key in contacts.keys():
        assert response.data[key][0] == UniqueValidator.message

    assert User.objects.filter(**contacts).count() == 1
    for cv in cvs:
        assert not ContactVerification.objects.get(id=cv.id).is_confirmed


@pytest.mark.parametrize(
    "contacts",
    [
        {"phone": get_random_phone(7)},
    ],
)
def test__if_phone_exists__user_updates(api_client, monkeypatch, contacts, new_user_data):
    data, cvs = {}, []
    for contact_name, value in contacts.items():
        contact_data = {contact_name: value}

        cv = ContactVerification.objects.create(**contact_data, purpose=CONTACT_VERIFICATION_PURPOSE)
        assert cv.small_code and not cv.is_confirmed
        cvs.append(cv)
        cv_key = "phone_verification_code" if contact_name == "phone" else "email_verification_code"
        data = {**data, **contact_data, cv_key: cv.small_code}
    user = User.objects.create(**contacts)
    assert User.objects.filter(**contacts).count() == 1

    fixture_data = new_user_data(**contacts)
    data = {**data, **fixture_data}
    response = __get_response(api_client, data=data)

    token = Token.objects.get(user=user)
    assert response.data["key"] == token.key


@pytest.mark.parametrize(
    "contacts",
    [
        {"phone": get_random_phone(7)},
        {"email": get_random_email()},
    ],
)
def test__already_confirmed_cv__fail(api_client, monkeypatch, contacts, new_user_data):
    data, cvs = {"password": LONG_TEST_PASSWORD}, []
    for contact_name, value in contacts.items():
        contact_data = {contact_name: value}
        cv = ContactVerification.objects.create(**contact_data, purpose=CONTACT_VERIFICATION_PURPOSE)
        cv.confirm()
        assert cv.small_code and cv.is_confirmed
        cvs.append(cv)
        cv_key = "phone_verification_code" if contact_name == "phone" else "email_verification_code"
        data = {**data, **contact_data, cv_key: cv.small_code}

    new_user_data = new_user_data(**contacts)
    data = {**data, **new_user_data}
    assert not User.objects.filter(**contacts)
    response = __get_response(api_client, data, status_codes=ValidationError)
    assert response.data["non_field_errors"] == [NOT_FOUND_NOT_CONFIRMED_CONTACT]
    assert not User.objects.filter(**contacts)
