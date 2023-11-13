import functools

import pytest
from django.contrib.auth import get_user_model

from tests.utils import get_random_phone, request_response_list, request_response_create
from tests.fixtures.user import SHORT_TEST_PASSWORD
from accounts.models.token import Token
from ma_saas.constants.constant import CONTACT_VERIFICATION_PURPOSE
from accounts.models.contact_verification import ContactVerification
from clients.notifications.interfaces.sms import SendSMS
from clients.notifications.interfaces.email import SendEmail

User = get_user_model()

__get_response_sign_up = functools.partial(request_response_create, path="/api/v1/sign-up/")
__get_response_contact_verification_code_send = functools.partial(
    request_response_create, path="/api/v1/contact-verification-code-send/"
)
__get_response_contact_verification_is_exist = functools.partial(
    request_response_list, path="/api/v1/contact-verification-is-exist/"
)
__get_response_contact_users = functools.partial(request_response_list, path="/api/v1/users/")
__get_response_tokens = functools.partial(request_response_create, path="/api/v1/tokens/")

_PURPOSE = CONTACT_VERIFICATION_PURPOSE


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)},))
def test__success(monkeypatch, api_client, get_user_fi, data, new_user_data):
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)
    monkeypatch.setattr(SendSMS, "send_sms_via_service_with_template", lambda *args, **kwargs: None)

    """начало регистрации заполняем данные"""
    phone, password = get_random_phone(7), SHORT_TEST_PASSWORD
    assert not User.objects.filter(phone=phone).exists()
    data = new_user_data(phone=phone, password=password)
    data.pop("email")

    """запрашиваем отправку кода верификации"""
    assert not ContactVerification.objects.filter(phone=phone, purpose=_PURPOSE).exists()
    response_phone_cv = __get_response_contact_verification_code_send(api_client, data={"phone": phone})
    assert response_phone_cv.data == {"phone": phone, "email": None, "is_password": False}

    """запрашиваем проверку кода верификации"""
    phone_cv = ContactVerification.objects.filter(phone=phone, purpose=_PURPOSE).order_by("id").last()
    query_kwargs = {"phone": phone, "small_code": phone_cv.small_code}
    response = __get_response_contact_verification_is_exist(api_client, query_kwargs=query_kwargs)
    assert response.data == []
    assert phone_cv.small_code and not phone_cv.is_confirmed

    """отправляем данные и получаем в ответ код для авторизаци"""
    assert not Token.objects.filter(user__phone=phone).exists()
    data["phone_verification_code"] = phone_cv.small_code
    assert not User.objects.filter(phone=phone).exists()
    response = __get_response_sign_up(api_client, data=data)
    assert User.objects.filter(phone=phone).exists()
    created_token = Token.objects.get(user__phone=phone)
    assert response.data == {"key": created_token.key}
    phone_cv = ContactVerification.objects.filter(phone=phone, purpose=_PURPOSE).order_by("id").last()
    assert phone_cv.is_confirmed
    created_user = User.objects.filter(phone=phone).order_by("id").last()

    """проверием авторизацию по присланному в ответ коду"""
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['key']}")
    response = __get_response_contact_users(api_client)
    assert response.data[0]["id"] == created_user.id

    """проверить выдачу кода при авторизации через телефон"""
    response = __get_response_tokens(api_client, data={"phone": phone, "password": password})
    assert response.data == {"key": created_token.key}

    """проверием авторизацию по присланному в ответ коду"""
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['key']}")
    response = __get_response_contact_users(api_client)
    assert response.data[0]["id"] == created_user.id
