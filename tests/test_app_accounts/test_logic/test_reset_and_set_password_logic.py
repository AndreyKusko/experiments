import functools

import pytest
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from tests.utils import get_random_email, get_random_phone, request_response_create
from ma_saas.constants.constant import ContactVerificationPurpose
from accounts.models.contact_verification import ContactVerification
from clients.notifications.interfaces.sms import SendSMS
from clients.notifications.interfaces.email import SendEmail

User = get_user_model()
__get_response_reset_password = functools.partial(request_response_create, path="/api/v1/reset-password/")
__get_response_set_password = functools.partial(request_response_create, path="/api/v1/set-password/")
_PURPOSE = ContactVerificationPurpose.PASSWORD_SET.value


@pytest.mark.parametrize("data", ({"phone": get_random_phone(7)}, {"email": get_random_email()}))
@pytest.mark.parametrize("is_authorised", (True, False))
@pytest.mark.parametrize("is_user_with_password", (True, False))
def test__success(monkeypatch, api_client, get_user_fi, data, is_authorised, is_user_with_password):
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)

    """запрос кода для смены пароля"""
    user = get_user_fi(**data)
    if not is_user_with_password:
        user.password = ""
        user.save()
    assert not ContactVerification.objects.filter(Q(user=user) | Q(**data), purpose=_PURPOSE).exists()
    __get_response_reset_password(api_client, data=data, user=user if is_authorised else None)
    cv = ContactVerification.objects.filter(user=user, purpose=_PURPOSE).order_by("id").last()
    assert not cv.is_confirmed
    new_password = get_random_string()
    assert not user.check_password(new_password)

    """запрос установки пароля"""
    data = {**data, "password": new_password, "small_code": cv.small_code}
    response = __get_response_set_password(api_client, data=data, user=user if is_authorised else None)
    cv = ContactVerification.objects.filter(user=user, purpose=_PURPOSE).order_by("id").last()
    assert cv.small_code
    assert cv.is_confirmed
    assert response.data == {}
    assert cv.user.check_password(new_password)
