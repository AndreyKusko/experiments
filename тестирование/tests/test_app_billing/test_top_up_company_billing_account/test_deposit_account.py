import functools

import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from tests.utils import request_response_update
from accounts.models import USER_IS_BLOCKED, NOT_TA_R_U__DELETED, NOT_TA_REQUESTING_USER_REASON
from companies.models.company import COMPANY_IS_DELETED, NOT_TA_COMPANY_REASON
from clients.billing.interfaces.company import CompanyBillingInterface

User = get_user_model()


__get_response = functools.partial(request_response_update, path="/api/v1/top-up-company-billing-account/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("get_company_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, {}, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


def test__by_superuser__success(api_client, monkeypatch, get_company_fi, super_user_fi: User):
    monkeypatch.setattr(CompanyBillingInterface, "deposit_account", lambda *args, **kwargs: None)
    monkeypatch.setattr(CompanyBillingInterface, "create_account", lambda *args, **kwargs: None)
    requesting_user = super_user_fi
    company = get_company_fi()
    assert __get_response(
        api_client,
        data={"deposit_amount": 1.00, "summary": get_random_string()},
        company_id=company.id,
        user=requesting_user,
        status_codes=status_code.HTTP_200_OK,
    )


def test__billing_and_deposit_if_instance_billing_true__success(
    api_client, monkeypatch, get_company_fi, super_user_fi: User
):
    requesting_user = super_user_fi
    company = get_company_fi()
    monkeypatch.setattr(CompanyBillingInterface, "deposit_account", lambda *args, **kwargs: None)
    assert __get_response(
        api_client,
        data={"deposit_amount": 1.00, "summary": get_random_string()},
        company_id=company.id,
        user=requesting_user,
        status_codes=status_code.HTTP_200_OK,
    )


def test__deleted_user__fail(api_client, get_company_fi, super_user_fi: User):
    requesting_user = super_user_fi
    requesting_user.user.is_deleted = True
    requesting_user.save()

    company = get_company_fi()
    response = __get_response(
        api_client,
        data={"deposit_amount": 1.00, "summary": get_random_string()},
        company_id=company.id,
        user=requesting_user,
        status_codes=PermissionDenied.status_code,
    )

    assert response.data == {"detail": NOT_TA_R_U__DELETED}


def test__blocked_user__fail(api_client, get_company_fi, super_user_fi: User):
    requesting_user = super_user_fi
    requesting_user.is_blocked = True
    requesting_user.save()
    company = get_company_fi()
    response = __get_response(
        api_client,
        data={"deposit_amount": 1.00, "summary": get_random_string()},
        company_id=company.id,
        user=requesting_user,
        status_codes=status_code.HTTP_403_FORBIDDEN,
    )
    assert response.data["detail"] == NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_BLOCKED)


def test__deleted_company__fail(api_client, get_company_fi, super_user_fi: User):
    requesting_user = super_user_fi
    company = get_company_fi()
    company.is_deleted = True
    company.save()

    response = __get_response(
        api_client,
        data={"deposit_amount": 1.00, "summary": get_random_string()},
        company_id=company.id,
        user=requesting_user,
        status_codes=status_code.HTTP_403_FORBIDDEN,
    )
    assert response.data["detail"] == NOT_TA_COMPANY_REASON.format(reason=COMPANY_IS_DELETED)
