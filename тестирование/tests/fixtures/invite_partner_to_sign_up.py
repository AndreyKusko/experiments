from typing import Callable

import pytest
from django.contrib.contenttypes.models import ContentType

from tests.utils import get_random_email
from companies.models.company import Company
from ma_saas.constants.company import CPS, CUS
from ma_saas.constants.constant import ContactVerificationPurpose
from accounts.models.contact_verification import ContactVerification
from companies.models.company_partnership import CompanyPartnership

PURPOSE = ContactVerificationPurpose.INVITE_PARTNER_TO_SIGN_UP.value


@pytest.fixture
def get_company_partnership_invite_via_email_fi(
    monkeypatch, get_cu_owner_fi, new_company_data: Callable
) -> Callable[..., Company]:
    def create_instance(
        invited_company_user_email=get_random_email(),
        inviting_company_user=get_cu_owner_fi(status=CUS.ACCEPT.value),
    ):
        invited_company_status, inviting_company_status = CPS.INVITE.value, CPS.ACCEPT.value

        company_partnership = CompanyPartnership.objects.create(
            invited_company_user_email=invited_company_user_email,
            inviting_company=inviting_company_user.company,
            inviting_company_user=inviting_company_user,
            invited_company_status=invited_company_status,
            inviting_company_status=inviting_company_status,
        )

        json_data = {
            "instances": [
                {
                    "id": company_partnership.id,
                    "content_type": ContentType.objects.get_for_model(company_partnership).id,
                }
            ]
        }
        contact_verification = ContactVerification.objects.create(
            json_data=json_data, purpose=PURPOSE, email=invited_company_user_email
        )

        return company_partnership, contact_verification

    return create_instance


@pytest.fixture
def company_fi(get_company_fi) -> Company:
    return get_company_fi()
