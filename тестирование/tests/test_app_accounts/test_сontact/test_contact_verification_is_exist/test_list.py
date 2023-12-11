import posixpath

import pytest
from django.contrib.auth import get_user_model

from tests.utils import get_random_email, get_random_phone
from accounts.serializers.utils import parse_phone_number
from ma_saas.constants.constant import CONTACT_VERIFICATION_PURPOSE
from accounts.models.contact_verification import ContactVerification

User = get_user_model()

PATH = "/api/v1/contact-verification-is-exist/"

_PURPOSE = CONTACT_VERIFICATION_PURPOSE


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)},))
def test__small_code__required(api_client, data: dict, get_user_fi):

    check_data = {k: v for k, v in data.items() if v}
    if data.get("phone"):
        check_data["phone"] = parse_phone_number(raw_phone_number=data["phone"])
    assert not ContactVerification.objects.filter(**check_data, purpose=_PURPOSE, is_confirmed=False).exists()

    s = posixpath.join(PATH, "?" + "".join((f"{k}={v}" for k, v in check_data.items())))
    response = api_client.get(s)
    assert response.data == {"detail": "small_code required"}


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
    assert not ContactVerification.objects.filter(**check_data, purpose=_PURPOSE, is_confirmed=False).exists()

    s = posixpath.join(PATH, "?" + "".join((f"{k}={v}" for k, v in check_data.items())) + f"small_code=1234")
    response = api_client.get(s)
    assert response.data == {"detail": "small_code required"}


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
def test__not_verified__success(api_client, data: dict, get_user_fi):
    check_data = {k: v for k, v in data.items() if v}
    if data.get("phone"):
        check_data["phone"] = parse_phone_number(raw_phone_number=data["phone"])
    cv = ContactVerification.objects.create(**check_data, purpose=_PURPOSE, is_confirmed=False)

    attrs = "?" + "".join((f"{k}={v}" for k, v in check_data.items())) + f"&small_code={cv.small_code}"
    response = api_client.get(posixpath.join(PATH, attrs))
    assert response.data == []


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
def test__verified__fail(api_client, data: dict, get_user_fi):
    check_data = {k: v for k, v in data.items() if v}
    if data.get("phone"):
        check_data["phone"] = parse_phone_number(raw_phone_number=data["phone"])
    cv = ContactVerification.objects.create(**check_data, purpose=_PURPOSE, is_confirmed=True)

    attrs = "?" + "".join((f"{k}={v}" for k, v in check_data.items())) + f"&small_code={cv.small_code}"
    s = posixpath.join(PATH, attrs)
    response = api_client.get(s)
    assert response.data == {"detail": "Active contact verification not found"}
