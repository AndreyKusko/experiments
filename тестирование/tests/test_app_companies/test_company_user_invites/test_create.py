import typing as tp
import functools

import pytest
from django.forms import model_to_dict
from django.contrib.auth import get_user_model
from django.core.validators import EmailValidator
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import get_random_email, get_random_phone, request_response_create
from accounts.models.users import USER_EMAIL_NOT_VERIFIED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from ma_saas.constants.company import (
    CUR,
    CUS,
    ROLES,
    NOT_ACCEPT_CUS,
    NOT_WORKER_ROLES,
    ROLES_WITH_EMAIL,
    ROLES_WITH_PHONE,
)
from accounts.serializers.utils import parse_phone_number
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_MUST_BE_ACCEPT, CompanyUser
from accounts.serializers.validators import EMAIL_OR_PHONE_REQUIRE
from clients.notifications.interfaces.sms import SendSMS
from clients.notifications.interfaces.email import SendEmail
from companies.serializers.company_user_invite import (
    ERROR_INVITE_ROLE_EMAIL_ONLY,
    ERROR_INVITE_ROLE_PHONE_ONLY,
)
from companies.serializers.utils.company_user_invite import (
    ERROR_INVITE_USER_IS_BLOCKED,
    COMPANY_USER_ALREADY_EXISTS_WITH_ROLE,
    ERROR_INVITE_COMPANY_USER_ALREADY_EXISTS,
)

User = get_user_model()

__get_response = functools.partial(request_response_create, path="/api/v1/company-user-invites/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, {}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("role", NOT_WORKER_ROLES)
def test__owner__invite_via_email__success(api_client, monkeypatch, mock_policies_false, r_cu, role):
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    email = get_random_email()
    data = {"email": email, "company": r_cu.company.id, "role": role}
    assert not User.objects.filter(email=email).exists()
    response = __get_response(api_client, data, user=r_cu.user)
    created_users = User.objects.filter(email=email)
    assert created_users.count() == 1
    created_user = created_users.first()
    assert not created_user.is_verified_phone
    assert not created_user.is_verified_email
    created_company_users = CompanyUser.objects.filter(user=created_user)
    assert created_company_users.count() == 1
    created_cu = created_company_users.first()
    created_cu_dict = model_to_dict(created_cu)
    assert all(created_cu_dict[key] == value for key, value in response.data.items())


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("role", [CUR.OWNER])
def test__owner_invite_via_phone__fail(api_client, monkeypatch, mock_policies_false, r_cu, role):
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)
    phone = get_random_phone(7)
    check_phone = parse_phone_number(raw_phone_number=phone)
    assert not User.objects.filter(phone=check_phone).exists()
    data = {"phone": phone, "company": r_cu.company.id, "role": role}
    response = __get_response(api_client, data, r_cu.user, status_codes=ValidationError)
    assert response.data == {"non_field_errors": [ERROR_INVITE_ROLE_EMAIL_ONLY]}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("role", [CUR.WORKER])
def test__invite_worker_via_email__fail(api_client, monkeypatch, r_cu, role):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    email = get_random_email()
    data = {"email": email, "company": r_cu.company.id, "role": role}
    assert not User.objects.filter(email=email).exists()
    response = __get_response(api_client, data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == {"non_field_errors": [ERROR_INVITE_ROLE_PHONE_ONLY]}
    assert not User.objects.filter(email=email).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("role", NOT_WORKER_ROLES)
def test__invite_not_worker_via_phone__fail(api_client, monkeypatch, r_cu, role):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    phone = get_random_phone()
    check_phone = parse_phone_number(raw_phone_number=phone)
    assert not User.objects.filter(phone=check_phone).exists()
    data = {"phone": phone, "company": r_cu.company.id, "role": role}
    response = __get_response(api_client, data, r_cu.user, status_codes=ValidationError)
    assert response.data == {"non_field_errors": [ERROR_INVITE_ROLE_EMAIL_ONLY]}
    assert not User.objects.filter(phone=check_phone).exists()


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__manager_without_policy__fail(api_client, mock_policies_false, r_cu, role):
    email = get_random_email()
    assert not User.objects.filter(email=email).exists()
    data = {"email": email, "company": r_cu.company.id, "role": role}
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert not User.objects.filter(email=email).exists()
    assert response.data == {"detail": PermissionDenied.default_detail}


@pytest.mark.parametrize("role", ROLES_WITH_EMAIL)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__manager__via_email__with_policy__success(api_client, monkeypatch, r_cu, role):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    email = get_random_email()
    assert not User.objects.filter(email=email).exists()
    data = {"email": email, "company": r_cu.company.id, "role": role}
    response = __get_response(api_client, data=data, user=r_cu.user)
    assert response.data["id"]
    assert response.data["company"] == r_cu.company.id
    assert response.data["role"] == role
    assert response.data["status"] == CUS.INVITE.value
    assert User.objects.filter(email=email).exists()


@pytest.mark.parametrize("role", ROLES_WITH_PHONE)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__manager__via_phone__with_policy__success(api_client, monkeypatch, r_cu, role):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)
    phone = get_random_phone(7)
    check_phone = parse_phone_number(raw_phone_number=phone)
    assert not User.objects.filter(phone=check_phone).exists()
    data = {"phone": phone, "company": r_cu.company.id, "role": role}
    response = __get_response(api_client, data, r_cu.user)
    assert response.data["company"] == r_cu.company.id
    assert response.data["role"] == role
    assert response.data["status"] == CUS.INVITE.value
    created_users = User.objects.filter(phone=check_phone)
    assert created_users.count() == 1
    created_user = created_users.first()
    assert response.data["user"] == created_user.id
    assert not created_user.is_verified_phone
    assert not created_user.is_verified_email
    created_company_users = CompanyUser.objects.filter(user=created_user)
    assert created_company_users.count() == 1
    assert response.data["id"] == created_company_users.first().id


@pytest.mark.parametrize(
    ("email", "err_msg"),
    (
        ("1@1.1", EmailValidator.message),
        ("qwe", EmailValidator.message),
        ("123", EmailValidator.message),
        ("@qwe.qwe", EmailValidator.message),
        ("qwe@123", EmailValidator.message),
        ("qwe@.qwe", EmailValidator.message),
    ),
)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__contractor_invalid_email__fail(api_client, r_cu, email: str, err_msg: str):
    data = {"email": email, "company": r_cu.company.id, "role": CUR.PROJECT_MANAGER}
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == {"email": [err_msg]}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("contact", "role"),
    (
        ({"phone": get_random_phone(prefix="7")}, CUR.WORKER),
        ({"email": get_random_email()}, CUR.PROJECT_MANAGER),
        ({"email": get_random_email()}, CUR.OWNER),
    ),
)
def test__existing_accepted_company_user__fail(
    api_client, r_cu, get_user_fi, get_cu_fi, contact: tp.Dict[str, str], role
):
    company = r_cu.company
    existing_user = get_user_fi(**contact)
    get_cu_fi(company=company, user=existing_user, role=role, status=CUS.ACCEPT.value)
    data = {**contact, "company": company.id, "role": role}
    response = __get_response(api_client, data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == [ERROR_INVITE_COMPANY_USER_ALREADY_EXISTS]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
@pytest.mark.parametrize(
    ("contact", "role"),
    (
        ({"phone": get_random_phone(prefix="7")}, CUR.WORKER),
        ({"email": get_random_email()}, CUR.PROJECT_MANAGER),
        ({"email": get_random_email()}, CUR.OWNER),
    ),
)
def test__existing__not_accepted_company_user__success(
    monkeypatch, api_client, r_cu, get_user_fi, get_cu_fi, contact: tp.Dict[str, str], role, status
):
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    company = r_cu.company
    existing_user = get_user_fi(**contact)
    get_cu_fi(company=company, user=existing_user, role=role, status=status.value)
    data = {**contact, "company": company.id, "role": role}
    assert __get_response(api_client, data=data, user=r_cu.user)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("contact", "role", "existing_role"),
    (
        ({"email": get_random_email()}, CUR.PROJECT_MANAGER, CUR.OWNER),
        ({"email": get_random_email()}, CUR.OWNER, CUR.PROJECT_MANAGER),
    ),
)
def test__contractor__existing_cu_with_another_role__fail(
    monkeypatch,
    api_client,
    r_cu,
    get_user_fi,
    get_cu_fi,
    contact: tp.Dict[str, str],
    role,
    existing_role,
):
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    company = r_cu.company
    existing_user = get_user_fi(**contact)
    get_cu_fi(company=company, user=existing_user, role=existing_role, status=CUS.INVITE.value)
    data = {**contact, "company": company.id, "role": role}
    response = __get_response(api_client, data, r_cu.user, status_codes=ValidationError)
    assert response.data == [COMPANY_USER_ALREADY_EXISTS_WITH_ROLE.format(role=existing_role)]


@pytest.mark.parametrize(
    ("contact", "role"),
    (
        ({"phone": get_random_phone(prefix="7")}, CUR.WORKER),
        ({"email": get_random_email()}, CUR.PROJECT_MANAGER),
    ),
)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__contractor__blocked_user__fail(api_client, r_cu, get_user_fi, contact: tp.Dict[str, str], role):
    _existing_user = get_user_fi(**contact, is_blocked=True)
    data = {**contact, "company": r_cu.company.id, "role": role}
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == [ERROR_INVITE_USER_IS_BLOCKED]


def test__contractor__not_verified_requesting_user__fail(api_client, get_cu_owner_fi, get_user_fi):
    email = get_random_email()
    user = get_user_fi(email=email, is_verified_email=False)
    r_cu = get_cu_owner_fi(user=user)
    phone = get_random_phone()
    data = {"phone": phone, "company": r_cu.company.id, "role": CUR.WORKER}
    response = __get_response(api_client, data, user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_REQUESTING_USER_REASON.format(reason=USER_EMAIL_NOT_VERIFIED)}


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__contractor__not_accepted_company_user__fail(api_client, monkeypatch, get_cu_owner_fi, status):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu = get_cu_owner_fi(status=status.value)
    data = {"phone": get_random_phone(), "company": r_cu.company.id, "role": CUR.WORKER}
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__contractor__deleted_company_user__fail(api_client, monkeypatch, r_cu):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    r_cu.is_deleted = True
    r_cu.save()
    phone = get_random_phone()
    data = {"phone": phone, "company": r_cu.company.id, "role": CUR.WORKER}
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__another_company__fail(api_client, r_cu, get_company_fi):
    phone = get_random_phone()
    data = {"phone": phone, "company": get_company_fi().id, "role": CUR.WORKER}
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__contractor__not_single_contact__fail(api_client, r_cu):
    data = {"company": r_cu.company.id, "role": CUR.WORKER}
    response = __get_response(api_client, data, r_cu.user, status_codes=ValidationError)
    assert response.data == {"non_field_errors": [EMAIL_OR_PHONE_REQUIRE]}
