import functools

import pytest
from django.http import HttpResponseBadRequest
from django.contrib.auth import get_user_model
from django.core.validators import EmailValidator
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import get_random_email, request_response_create
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from companies.models.company import Company
from ma_saas.constants.company import CUR, CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES, CompanyPartnershipStatus
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_MUST_BE_ACCEPT, CompanyUser
from companies.models.company_partnership import CompanyPartnership
from clients.notifications.interfaces.email import SendEmail
from companies.serializers.company_partnership import USER_ALREADY_EXISTS

User = get_user_model()

__get_response = functools.partial(request_response_create, path="/api/v1/company-partnerships/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, {}, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


def test__creating_via_email__result_data(api_client, monkeypatch, cu_owner_fi, get_cu_fi):
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    email = dict(invited_company_user_email=get_random_email())
    assert not CompanyPartnership.objects.filter(**email, inviting_company=r_cu.company).exists()
    assert not User.objects.filter(email=email).exists()
    data = {**email, "inviting_company": r_cu.company.id}
    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instances = CompanyPartnership.objects.filter(**email, inviting_company=r_cu.company)
    assert created_instances.count() == 1
    created_instance: CompanyPartnership = created_instances.first()
    invited_status = CompanyPartnershipStatus.INVITE.value
    inviting_status = CompanyPartnershipStatus.ACCEPT.value
    assert created_instance.invited_company_status == invited_status
    assert created_instance.inviting_company_status == inviting_status
    assert not User.objects.filter(email=email).exists()
    assert len(response.data) == 9
    assert response.data["id"] == created_instance.id
    assert response.data["inviting_company_user"] == r_cu.id
    assert (
        response.data["invited_company_user_email"]
        == created_instance.invited_company_user_email
        == email["invited_company_user_email"]
    )
    assert not response.data["invited_company"]
    assert response.data["inviting_company"] == r_cu.company.id
    assert response.data["invited_company_status"] == invited_status
    assert response.data["inviting_company_status"] == inviting_status
    assert response.data["updated_at"]
    assert response.data["created_at"]


@pytest.mark.parametrize("invited_company", [pytest.lazy_fixture("company_fi")])
def test__creating_via_company__result_data(api_client, monkeypatch, cu_owner_fi, get_cu_fi, invited_company):
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    assert not CompanyPartnership.objects.filter(invited_company=invited_company).exists()
    data = {"invited_company": invited_company.id, "inviting_company": r_cu.company.id}
    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instances = CompanyPartnership.objects.filter(
        invited_company=invited_company, inviting_company=r_cu.company
    )

    assert created_instances.count() == 1
    created_instance: CompanyPartnership = created_instances.first()

    invited_status = CompanyPartnershipStatus.INVITE.value
    inviting_status = CompanyPartnershipStatus.ACCEPT.value
    assert created_instance.invited_company_status == invited_status
    assert created_instance.inviting_company_status == inviting_status
    assert created_instance.inviting_company == r_cu.company
    assert created_instance.invited_company == invited_company
    assert len(response.data) == 9
    assert response.data["id"] == created_instance.id
    assert response.data["inviting_company_user"] == r_cu.id
    assert not response.data["invited_company_user_email"]
    assert response.data["invited_company"] == invited_company.id
    assert response.data["inviting_company"] == r_cu.company.id
    assert response.data["invited_company_status"] == invited_status
    assert response.data["inviting_company_status"] == inviting_status
    assert response.data["updated_at"]
    assert response.data["created_at"]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__creating_with_existing__user_fail(api_client, monkeypatch, r_cu, get_user_fi, get_cu_fi):
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    email = get_random_email()
    email_data = dict(invited_company_user_email=email)
    get_cu_fi(user=get_user_fi(email=email))
    assert not CompanyPartnership.objects.filter(**email_data, inviting_company=r_cu.company).exists()
    assert not User.objects.filter(email=email_data).exists()
    data = {**email_data, "inviting_company": r_cu.company.id}
    assert CompanyUser.objects.existing().filter(user__email=email).exists()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == {"invited_company_user_email": [USER_ALREADY_EXISTS]}
    assert not CompanyPartnership.objects.filter(**email_data).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, monkeypatch, cu_owner_fi, r_cu):
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)

    email = dict(invited_company_user_email=get_random_email())
    assert not CompanyPartnership.objects.filter(**email, inviting_company=r_cu.company).exists()
    data = {**email, "inviting_company": r_cu.company.id}
    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instance = CompanyPartnership.objects.filter(**email, inviting_company=r_cu.company).first()
    assert response.data
    assert response.data["id"] == created_instance.id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted__company_owner__fail(api_client, mock_policies_false, cu_owner_fi, get_cu_fi, status):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    email = dict(invited_company_user_email=get_random_email())
    assert not CompanyPartnership.objects.filter(**email, inviting_company=r_cu.company).exists()
    data = {**email, "inviting_company": r_cu.company.id}
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert not CompanyPartnership.objects.filter(**email, inviting_company=r_cu.company).exists()
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__without_policy__fail(api_client, mock_policies_false, get_cu_fi, role):

    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    email = dict(invited_company_user_email=get_random_email())
    assert not CompanyPartnership.objects.filter(**email, inviting_company=r_cu.company).exists()
    data = {**email, "inviting_company": r_cu.company.id}
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert not CompanyPartnership.objects.filter(**email, inviting_company=r_cu.company).exists()
    assert response.data["detail"] == PermissionDenied.default_detail


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__with_policy__success(api_client, monkeypatch, cu_owner_fi, get_cu_fi, role):
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    email = dict(invited_company_user_email=get_random_email())
    assert not CompanyPartnership.objects.filter(**email, inviting_company=r_cu.company).exists()
    data = {**email, "inviting_company": r_cu.company.id}
    response = __get_response(api_client, data=data, user=r_cu.user)
    assert CompanyPartnership.objects.filter(**email, inviting_company=r_cu.company).exists()
    assert response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("another_company", [pytest.lazy_fixture("company_fi")])
def test__another_company_owner__fail(api_client, monkeypatch, r_cu: CompanyUser, another_company):
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    email = get_random_email()
    data = {"invited_company_user_email": email, "inviting_company": another_company.id}
    assert not CompanyPartnership.objects.filter(**data).exists()
    assert not User.objects.filter(email=email).exists()

    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data["detail"] == REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__related_to_company__without_policies__fail(
    api_client, monkeypatch, mock_policies_false, get_cu_fi, role
):
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    email = get_random_email()
    data = {"invited_company_user_email": email, "inviting_company": r_cu.company.id}
    assert not CompanyPartnership.objects.filter(
        invited_company_user_email=email, inviting_company=r_cu.company
    ).exists()
    assert not User.objects.filter(email=email).exists()

    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data["detail"] == PermissionDenied.default_detail


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__related_to_company__with_policies__success(api_client, monkeypatch, get_cu_fi, role):
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    email = get_random_email()
    data = {"invited_company_user_email": email, "inviting_company": r_cu.company.id}
    assert not CompanyPartnership.objects.filter(
        invited_company_user_email=email, inviting_company=r_cu.company
    ).exists()
    assert not User.objects.filter(email=email).exists()

    response = __get_response(api_client, data=data, user=r_cu.user)
    assert response.data
    assert len(response.data) == 9


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__duplicates_via_email__return_same_result(api_client, monkeypatch, r_cu: CompanyUser):
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    email = get_random_email()
    data = {"invited_company_user_email": email, "inviting_company": r_cu.company.id}
    assert not CompanyPartnership.objects.filter(**data).exists()
    assert not User.objects.filter(email=email).exists()

    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instances = CompanyPartnership.objects.filter(**data)
    assert created_instances.count() == 1
    created_instance = created_instances.first()
    assert response.data["id"] == created_instance.id

    response_duplicate = __get_response(api_client, data=data, user=r_cu.user)
    created_instances_duplicate = CompanyPartnership.objects.filter(**data)
    assert created_instances_duplicate.count() == 1
    created_instance_duplicate = created_instances_duplicate.first()
    assert response_duplicate.data["id"] == created_instance_duplicate.id == created_instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("invited_company", [pytest.lazy_fixture("company_fi")])
def test__duplicates_via_company__return_same_result(
    api_client, monkeypatch, r_cu: CompanyUser, invited_company
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    data = {"invited_company": invited_company.id, "inviting_company": r_cu.company.id}
    assert not CompanyPartnership.objects.filter(
        invited_company=invited_company, inviting_company=r_cu.company
    ).exists()

    response = __get_response(api_client, data=data, user=r_cu.user)

    created_instances = CompanyPartnership.objects.filter(**data)
    assert created_instances.count() == 1
    created_instance: CompanyPartnership = created_instances.first()
    assert response.data["id"] == created_instance.id

    response_duplicate = __get_response(api_client, data=data, user=r_cu.user)
    created_instances_duplicate = CompanyPartnership.objects.filter(**data)
    assert created_instances_duplicate.count() == 1
    created_instance_duplicate = created_instances_duplicate.first()
    assert response_duplicate.data["id"] == created_instance_duplicate.id == created_instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("invited_company", [pytest.lazy_fixture("company_fi")])
def test__duplicates_via_company__return_same_result(
    api_client, monkeypatch, r_cu: CompanyUser, invited_company
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    data = {"invited_company": invited_company.id, "inviting_company": r_cu.company.id}
    assert not CompanyPartnership.objects.filter(**data).exists()

    response = __get_response(api_client, data=data, user=r_cu.user)

    created_instances = CompanyPartnership.objects.filter(**data)
    assert created_instances.count() == 1
    created_instance: CompanyPartnership = created_instances.first()
    assert response.data["id"] == created_instance.id

    response_duplicate = __get_response(api_client, data=data, user=r_cu.user)
    created_instances_duplicate = CompanyPartnership.objects.filter(**data)
    assert created_instances_duplicate.count() == 1
    created_instance_duplicate = created_instances_duplicate.first()
    assert response_duplicate.data["id"] == created_instance_duplicate.id == created_instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__not_existing_company__fail(api_client, monkeypatch, r_cu: CompanyUser):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    latest_company = Company.objects.order_by("id").last() or 0
    not_existing_company_id = latest_company.id + 1000
    data = {"invited_company": not_existing_company_id, "inviting_company": r_cu.company.id}
    assert not CompanyPartnership.objects.filter(**data).exists()
    response = __get_response(
        api_client, data=data, user=r_cu.user, status_codes=HttpResponseBadRequest.status_code
    )
    assert "object does not exist" in response.data["invited_company"][0]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("invited_company_user_email", ["t", 123, "123", None, "t.tt", "t@mail", ""])
def test__invalid_email__fail(api_client, monkeypatch, r_cu: CompanyUser, invited_company_user_email):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    data = {
        "invited_company_user_email": invited_company_user_email,
        "inviting_company": r_cu.company.id,
    }
    assert not CompanyPartnership.objects.filter(**data).exists()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data["invited_company_user_email"] == EmailValidator.message


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("invited_company_user_email", ["t", 123, "123", "t.tt", "t@mail"])
def test__invalid_email__fail(api_client, monkeypatch, r_cu: CompanyUser, invited_company_user_email):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    data = {
        "invited_company_user_email": invited_company_user_email,
        "inviting_company": r_cu.company.id,
    }
    assert not CompanyPartnership.objects.filter(**data).exists()
    response = __get_response(
        api_client, data=data, user=r_cu.user, status_codes=HttpResponseBadRequest.status_code
    )
    assert response.data["invited_company_user_email"][0] == EmailValidator.message


FIELD__EMAIL__OR__INVITED_COMPANY__REQUIRED = "Обязательно нужно заполнить поля: email, invited_company."
ALLOWED__TO_USE_ONLY__EMAIL__OR__INVITED_COMPANY = (
    "Можно использовать только одно из полей: email, invited_company."
)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("is_company_and_email", "err_txt"),
    [
        (True, ALLOWED__TO_USE_ONLY__EMAIL__OR__INVITED_COMPANY),
        (False, FIELD__EMAIL__OR__INVITED_COMPANY__REQUIRED),
    ],
)
def test__company_and_email__fails(
    api_client, monkeypatch, r_cu: CompanyUser, is_company_and_email, err_txt, company_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    inviting_company = {"inviting_company": r_cu.company.id}
    if is_company_and_email:
        data = {
            "invited_company_user_email": get_random_email(),
            **inviting_company,
            "invited_company": company_fi.id,
        }
    else:
        data = {**inviting_company}
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data["non_field_errors"][0] == err_txt


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("invited_status", "inviting_status"),
    [(CompanyPartnershipStatus.ACCEPT.value, CompanyPartnershipStatus.ACCEPT.value)],
)
def test__existing_active_invite__via_email__success(
    api_client,
    monkeypatch,
    r_cu: CompanyUser,
    get_company_partnership_fi,
    invited_status,
    inviting_status,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    monkeypatch.setattr(SendEmail, "company_partnership_sign_up_invite", lambda *a, **kw: None)

    email = {"invited_company_user_email": get_random_email()}
    cp = get_company_partnership_fi(
        **email,
        inviting_company=r_cu.company,
        inviting_company_status=inviting_status,
        invited_company_status=invited_status,
    )
    existing_instances = CompanyPartnership.objects.filter(**email, inviting_company=r_cu.company)
    assert existing_instances.count() == 1
    existing_instance = existing_instances.first()
    assert existing_instance.inviting_company_status == inviting_status
    assert existing_instance.invited_company_status == invited_status

    data = {**email, "inviting_company": r_cu.company.id}
    response = __get_response(api_client, data=data, user=r_cu.user)
    assert response.data["id"] == cp.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("invited_status", "inviting_status"),
    [(CompanyPartnershipStatus.ACCEPT.value, CompanyPartnershipStatus.ACCEPT.value)],
)
@pytest.mark.parametrize("invited_company", [pytest.lazy_fixture("company_fi")])
def test__existing_active_invite__via_company__success(
    api_client,
    monkeypatch,
    r_cu: CompanyUser,
    get_company_partnership_fi,
    invited_status,
    inviting_status,
    invited_company,
):
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance_data = dict(invited_company=invited_company, inviting_company=r_cu.company)
    cp = get_company_partnership_fi(
        **instance_data, inviting_company_status=inviting_status, invited_company_status=invited_status
    )
    existing_instances = CompanyPartnership.objects.filter(**instance_data)
    assert existing_instances.count() == 1
    existing_instance = existing_instances.first()
    assert existing_instance.inviting_company_status == inviting_status
    assert existing_instance.invited_company_status == invited_status

    data = {k: v.id for k, v in instance_data.items()}
    response = __get_response(api_client, data=data, user=r_cu.user)
    assert response.data["id"] == cp.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("invited_status", "inviting_status"),
    [
        (CompanyPartnershipStatus.INVITE.value, CompanyPartnershipStatus.CANCEL.value),
        (CompanyPartnershipStatus.ACCEPT.value, CompanyPartnershipStatus.CANCEL.value),
        (CompanyPartnershipStatus.CANCEL.value, CompanyPartnershipStatus.ACCEPT.value),
        (CompanyPartnershipStatus.CANCEL.value, CompanyPartnershipStatus.CANCEL.value),
    ],
)
def test__with_canceled_invite__via_email__success(
    api_client,
    monkeypatch,
    r_cu: CompanyUser,
    get_company_partnership_fi,
    invited_status,
    inviting_status,
):
    monkeypatch.setattr(SendEmail, "send_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    email = get_random_email()
    data = {"invited_company_user_email": email, "inviting_company": r_cu.company.id}
    get_company_partnership_fi(
        invited_company_user_email=email,
        inviting_company=r_cu.company,
        inviting_company_status=inviting_status,
        invited_company_status=invited_status,
    )
    existing_instances = CompanyPartnership.objects.filter(**data).order_by("id")
    assert existing_instances.count() == 1
    existing_instance = existing_instances.last()
    assert existing_instance.inviting_company_status == inviting_status
    assert existing_instance.invited_company_status == invited_status

    response = __get_response(api_client, data=data, user=r_cu.user)
    assert response.data["id"] != existing_instance.id

    existing_instances_after = CompanyPartnership.objects.filter(**data)
    assert existing_instances_after.count() == 2

    created_instance = CompanyPartnership.objects.filter().latest("id")
    assert response.data["id"] == created_instance.id
    assert response.data["inviting_company_status"] == CompanyPartnershipStatus.ACCEPT.value
    assert response.data["invited_company_status"] == CompanyPartnershipStatus.INVITE.value


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("invited_status", "inviting_status"),
    [
        (CompanyPartnershipStatus.INVITE.value, CompanyPartnershipStatus.CANCEL.value),
        (CompanyPartnershipStatus.ACCEPT.value, CompanyPartnershipStatus.CANCEL.value),
        (CompanyPartnershipStatus.CANCEL.value, CompanyPartnershipStatus.ACCEPT.value),
        (CompanyPartnershipStatus.CANCEL.value, CompanyPartnershipStatus.CANCEL.value),
    ],
)
@pytest.mark.parametrize("invited_company", [pytest.lazy_fixture("company_fi")])
def test__with_canceled_invite__via_company__success(
    api_client,
    monkeypatch,
    r_cu: CompanyUser,
    get_company_partnership_fi,
    invited_status,
    inviting_status,
    invited_company,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    instance_data = {"invited_company": invited_company, "inviting_company": r_cu.company}
    get_company_partnership_fi(
        **instance_data, inviting_company_status=inviting_status, invited_company_status=invited_status
    )

    existing_instances = CompanyPartnership.objects.filter(**instance_data)
    assert existing_instances.count() == 1
    existing_instance = existing_instances.first()
    assert existing_instance.inviting_company_status == inviting_status
    assert existing_instance.invited_company_status == invited_status

    data = {k: v.id for k, v in instance_data.items()}
    response = __get_response(api_client, data=data, user=r_cu.user)
    assert response.data["id"] != existing_instance.id

    existing_instances_after = CompanyPartnership.objects.filter(**data)
    assert existing_instances_after.count() == 2

    created_instance = CompanyPartnership.objects.filter().latest("id")
    assert response.data["id"] == created_instance.id
    assert response.data["inviting_company_status"] == CompanyPartnershipStatus.ACCEPT.value
    assert response.data["invited_company_status"] == CompanyPartnershipStatus.INVITE.value
