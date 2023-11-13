import functools

from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework.exceptions import ValidationError

from tests.utils import get_random_email, get_random_phone, request_response_create
from ma_saas.constants.company import CompanyPartnershipStatus
from ma_saas.constants.constant import CONTACT_VERIFICATION_PURPOSE, ContactVerificationPurpose
from projects.models.project_partnership import ProjectPartnership
from accounts.models.contact_verification import ContactVerification
from companies.models.company_partnership import CompanyPartnership
from accounts.serializers.sign_up_new_user_via_invite import SECRETE_LINK_CONFIRMED
from companies.serializers.register_new_company_and_owner_via_secret_code import SUBDOMAIN_OCCUPIED

User = get_user_model()

__get_response = functools.partial(
    request_response_create, path="/api/v1/sign-up-new-company-owner-via-invite/"
)
PURPOSE = ContactVerificationPurpose.INVITE_PARTNER_TO_SIGN_UP.value


def test__without_project_partnership__success(
    api_client, monkeypatch, get_company_partnership_invite_via_email_fi
):
    email, phone = get_random_email(), get_random_phone(7)
    cp, cv = get_company_partnership_invite_via_email_fi(invited_company_user_email=email)

    assert not cp.invited_company
    assert cp.invited_company_user_email
    assert cp.inviting_company_status == CompanyPartnershipStatus.ACCEPT.value
    assert cp.invited_company_status == CompanyPartnershipStatus.INVITE.value

    assert not cv.is_confirmed
    assert not cv.small_code
    assert cv.large_code

    assert not User.objects.filter(email=email).exists()
    assert not User.objects.filter(phone=phone).exists()

    cv_email = ContactVerification.objects.create(email=email, purpose=CONTACT_VERIFICATION_PURPOSE)
    assert not cv_email.is_confirmed
    assert not cv_email.large_code
    assert cv_email.small_code
    cv_phone = ContactVerification.objects.create(phone=phone, purpose=CONTACT_VERIFICATION_PURPOSE)
    assert not cv_phone.is_confirmed
    assert not cv_phone.large_code
    assert cv_phone.small_code

    data = {
        "company_title": get_random_string(),
        "company_subdomain": f"t-{get_random_string(length=4)}",
        "email": email,
        "email_verification_code": cv_email.small_code,
        "phone": phone,
        "phone_verification_code": cv_phone.small_code,
        "secret_invite_code": cv.large_code,
        "first_name": get_random_string(),
        "last_name": get_random_string(),
        "middle_name": get_random_string(),
        "password": get_random_string(),
    }
    response = __get_response(api_client, data=data)
    assert response.data == {"id": cp.id}

    updated_cv = ContactVerification.objects.get(id=cv.id)
    assert updated_cv.is_confirmed

    updated_cp = CompanyPartnership.objects.get(id=cp.id)
    assert updated_cp.invited_company
    assert updated_cp.invited_company

    created_user = User.objects.get(email=email, phone=phone)
    assert created_user.is_verified_phone
    assert created_user.is_verified_email


def test__with_project_partnership__success(
    api_client,
    monkeypatch,
    get_company_partnership_invite_via_email_fi,
    get_project_partnership_fi,
    get_project_fi,
):
    email, phone = get_random_email(), get_random_phone(7)
    cp, cv = get_company_partnership_invite_via_email_fi(invited_company_user_email=email)

    assert not cp.invited_company
    assert cp.invited_company_user_email
    assert cp.inviting_company_status == CompanyPartnershipStatus.ACCEPT.value
    assert cp.invited_company_status == CompanyPartnershipStatus.INVITE.value

    assert not cv.is_confirmed
    assert not cv.small_code
    assert cv.large_code

    assert not User.objects.filter(email=email).exists()
    assert not User.objects.filter(phone=phone).exists()

    project = get_project_fi(company=cp.inviting_company)
    pp = get_project_partnership_fi(company_partnership=cp, project=project)
    assert not pp.partner_company

    cv_email = ContactVerification.objects.create(email=email, purpose=CONTACT_VERIFICATION_PURPOSE)
    assert not cv_email.is_confirmed
    assert not cv_email.large_code
    assert cv_email.small_code
    cv_phone = ContactVerification.objects.create(phone=phone, purpose=CONTACT_VERIFICATION_PURPOSE)
    assert not cv_phone.is_confirmed
    assert not cv_phone.large_code
    assert cv_phone.small_code

    data = {
        "company_title": get_random_string(),
        "company_subdomain": f"t-{get_random_string(length=4)}",
        "email": email,
        "email_verification_code": cv_email.small_code,
        "phone": phone,
        "phone_verification_code": cv_phone.small_code,
        "secret_invite_code": cv.large_code,
        "first_name": get_random_string(),
        "last_name": get_random_string(),
        "middle_name": get_random_string(),
        "password": get_random_string(),
    }
    response = __get_response(api_client, data=data)
    assert response.data == {"id": cp.id}

    updated_cv = ContactVerification.objects.get(id=cv.id)
    assert updated_cv.is_confirmed

    updated_cp = CompanyPartnership.objects.get(id=cp.id)
    assert updated_cp.invited_company
    assert updated_cp.invited_company

    created_user = User.objects.get(email=email, phone=phone)
    assert created_user.is_verified_phone
    assert created_user.is_verified_email

    updated_pp = ProjectPartnership.objects.get(id=pp.id)
    assert updated_pp.partner_company == updated_cp.invited_company


def test__with_project_scheme_partnership__success(
    api_client,
    monkeypatch,
    get_company_partnership_invite_via_email_fi,
    get_project_partnership_fi,
    get_project_fi,
    get_project_scheme_partnership_fi,
):
    email, phone = get_random_email(), get_random_phone(7)
    cp, cv = get_company_partnership_invite_via_email_fi(invited_company_user_email=email)

    assert not cp.invited_company
    assert cp.invited_company_user_email
    assert cp.inviting_company_status == CompanyPartnershipStatus.ACCEPT.value
    assert cp.invited_company_status == CompanyPartnershipStatus.INVITE.value

    assert not cv.is_confirmed
    assert not cv.small_code
    assert cv.large_code

    assert not User.objects.filter(email=email).exists()
    assert not User.objects.filter(phone=phone).exists()

    project = get_project_fi(company=cp.inviting_company)
    pp = get_project_partnership_fi(company_partnership=cp, project=project)
    assert not pp.partner_company

    get_project_scheme_partnership_fi(project_partnership=pp)

    cv_email = ContactVerification.objects.create(email=email, purpose=CONTACT_VERIFICATION_PURPOSE)
    assert not cv_email.is_confirmed
    assert not cv_email.large_code
    assert cv_email.small_code
    cv_phone = ContactVerification.objects.create(phone=phone, purpose=CONTACT_VERIFICATION_PURPOSE)
    assert not cv_phone.is_confirmed
    assert not cv_phone.large_code
    assert cv_phone.small_code

    data = {
        "company_title": get_random_string(),
        "company_subdomain": f"t-{get_random_string(length=4)}",
        "email": email,
        "email_verification_code": cv_email.small_code,
        "phone": phone,
        "phone_verification_code": cv_phone.small_code,
        "secret_invite_code": cv.large_code,
        "first_name": get_random_string(),
        "last_name": get_random_string(),
        "middle_name": get_random_string(),
        "password": get_random_string(),
    }
    response = __get_response(api_client, data=data)
    assert response.data == {"id": cp.id}

    updated_cv = ContactVerification.objects.get(id=cv.id)
    assert updated_cv.is_confirmed

    updated_cp = CompanyPartnership.objects.get(id=cp.id)
    assert updated_cp.invited_company
    assert updated_cp.invited_company

    created_user = User.objects.get(email=email, phone=phone)
    assert created_user.is_verified_phone
    assert created_user.is_verified_email

    updated_pp = ProjectPartnership.objects.get(id=pp.id)
    assert updated_pp.partner_company == updated_cp.invited_company


def test__confirmed__fail(api_client, monkeypatch, get_company_partnership_invite_via_email_fi):
    email, phone = get_random_email(), get_random_phone(7)
    cp, cv = get_company_partnership_invite_via_email_fi(invited_company_user_email=email)
    cv.is_confirmed = True
    cv.save()

    cv_email = ContactVerification.objects.create(email=email, purpose=CONTACT_VERIFICATION_PURPOSE)

    cv_phone = ContactVerification.objects.create(phone=phone, purpose=CONTACT_VERIFICATION_PURPOSE)

    data = {
        "company_title": get_random_string(),
        "company_subdomain": f"t-{get_random_string(length=4)}",
        "email": email,
        "email_verification_code": cv_email.small_code,
        "phone": phone,
        "phone_verification_code": cv_phone.small_code,
        "secret_invite_code": cv.large_code,
        "first_name": get_random_string(),
        "last_name": get_random_string(),
        "middle_name": get_random_string(),
        "password": get_random_string(),
    }
    response = __get_response(api_client, data=data, status_codes=ValidationError)
    assert response.data == {"secret_invite_code": [SECRETE_LINK_CONFIRMED]}


def test__existing_subdomain__fail(
    api_client, monkeypatch, get_company_partnership_invite_via_email_fi, get_company_fi
):
    email, phone = get_random_email(), get_random_phone(7)
    cp, cv = get_company_partnership_invite_via_email_fi(invited_company_user_email=email)

    cv_email = ContactVerification.objects.create(email=email, purpose=CONTACT_VERIFICATION_PURPOSE)
    cv_phone = ContactVerification.objects.create(phone=phone, purpose=CONTACT_VERIFICATION_PURPOSE)
    company_subdomain = f"t-{get_random_string(length=4)}"
    company = get_company_fi(subdomain=company_subdomain)

    data = {
        "company_title": get_random_string(),
        "company_subdomain": company.subdomain,
        "email": email,
        "email_verification_code": cv_email.small_code,
        "phone": phone,
        "phone_verification_code": cv_phone.small_code,
        "secret_invite_code": cv.large_code,
        "first_name": get_random_string(),
        "last_name": get_random_string(),
        "middle_name": get_random_string(),
        "password": get_random_string(),
    }
    response = __get_response(api_client, data=data, status_codes=ValidationError)
    assert response.data == {"company_subdomain": [SUBDOMAIN_OCCUPIED]}
