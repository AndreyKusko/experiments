from http.client import responses

from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from tests.utils import get_random_email, get_authorization_token
from ma_saas.constants.company import CUR, CUS
from companies.models.company_user import COMPANY_USER_UNIQ_CONSTRAINT_ERR
from clients.notifications.interfaces.email import SendEmail

User = get_user_model()


def test__method__fail(api_client, get_cu_fi):

    r_cu = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)

    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.post(f"/api/v1/company-users/", data={})
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED
    assert response.status_text == responses[status_code.HTTP_405_METHOD_NOT_ALLOWED]
    assert response.data["detail"] == 'Method "POST" not allowed.'


def test__duplicates__fail(api_client, monkeypatch, get_company_fi, get_cu_fi, get_user_fi):
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    role = CUR.OWNER
    email = get_random_email()
    company = get_company_fi()
    target_user = get_user_fi(email=email)
    instance = get_cu_fi(user=target_user, company=company, role=role)

    err = None
    try:
        get_cu_fi(user=instance.user, company=instance.company, role=role)
    except Exception as e:
        err = e
    expected_err = ValidationError(
        COMPANY_USER_UNIQ_CONSTRAINT_ERR.format(company=company.id, user=target_user.id)
    )
    assert err.detail == expected_err.detail
