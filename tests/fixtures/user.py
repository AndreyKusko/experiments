import json
import typing as tp
from typing import Callable

import pytest
from django.contrib.auth import get_user_model

from tests.utils import get_random_email, get_random_phone
from clients.authserv.manager import AuthservManager
from accounts.serializers.utils import parse_phone_number

User = get_user_model()

TEST_EMAIL_POSTFIX = "@test.ru"
LONG_TEST_PASSWORD = "123qweasd"
SHORT_TEST_PASSWORD = "1234"


@pytest.fixture
def new_user_data() -> Callable:
    def return_data(
        email: tp.Optional[str] = "",
        phone: tp.Optional[str] = "",
        password: str = LONG_TEST_PASSWORD,
        is_password: bool = True,
        is_blocked: bool = False,
        avatar: tp.Optional[str] = None,
        first_name: str = "test_first_name",  # имя
        last_name: str = "test_last_name",  # фамилия
        middle_name: str = "test_middle_name",  # отчество
        city: str = "Москва",
        lat: float = 55.7522,  # широта
        lon: float = 37.6156,  # долгота
        gender: int = 0,  # пол
        birthdate: str = "1992-02-01",  # др
        is_test: bool = False,
    ) -> tp.Dict[str, tp.Any]:
        if not email:
            phone = phone or get_random_phone()
        if not phone:
            email = email or get_random_email()
        passwords = {}
        if is_password:
            passwords = {"password": password}
        avatar = json.dumps(avatar or {})
        return {
            "phone": phone,
            "email": email,
            "is_blocked": is_blocked,
            **passwords,
            "avatar": avatar,
            "first_name": first_name,
            "last_name": last_name,
            "middle_name": middle_name,
            "city": city,
            "lat": lat,
            "lon": lon,
            "gender": gender,
            "birthdate": birthdate,
            "is_test": is_test,
        }

    return return_data


@pytest.fixture
def get_user_fi(monkeypatch, new_user_data: Callable) -> Callable[..., User]:
    def get_or_create_instance(
        is_superuser: bool = False,
        is_verified_phone: tp.Optional[bool] = None,
        is_verified_email: tp.Optional[bool] = None,
        *args,
        **kwargs,
    ) -> User:
        # monkeypatch.setattr(AuthservManager, "update_user", lambda *a, **kw: None)
        monkeypatch.setattr(AuthservManager, "create_user", lambda *a, **kw: None)

        data = new_user_data(*args, **kwargs)
        password = data.pop("password")

        if user := User.objects.filter(is_superuser=is_superuser, **data).exists():
            return user
        if phone := data.get("phone"):
            data["phone"] = parse_phone_number(phone)
        else:
            data.pop("phone", None)
        is_v_phone = is_verified_phone if isinstance(is_verified_phone, bool) else not not data.get("phone")
        is_v_email = is_verified_email if isinstance(is_verified_email, bool) else not not data.get("email")
        user = User(
            is_superuser=is_superuser, is_verified_phone=is_v_phone, is_verified_email=is_v_email, **data
        )
        user.set_password(password)
        user.save()

        return user

    return get_or_create_instance


@pytest.fixture
def user_fi(get_user_fi) -> User:
    return get_user_fi()


@pytest.fixture
def super_user_fi(get_user_fi) -> User:
    return get_user_fi(is_superuser=True)
