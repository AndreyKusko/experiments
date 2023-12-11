import typing as tp
from decimal import Decimal
from http.client import responses

import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from tests.utils import get_authorization_token
from ma_saas.constants.system import API_V1
from ma_saas.constants.company import CUR, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from companies.models.company_user import NOT_TA_RCU_MUST_BE_ACCEPT, COMPANY_OWNER_ONLY_ALLOWED

User = get_user_model()


def __get_response(
    api_client, company_id: int, status_codes: int, user: tp.Optional[User] = None
) -> Response:
    """Return response."""
    if user:
        api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user))
    response = api_client.get(f"/{API_V1}/company-balance/{company_id}/")
    assert response.status_code == status_codes, f"response.data = {response.data}"
    assert response.status_text == responses[status_codes]
    return response


def test__anonymous(api_client, get_company_fi):
    response = __get_response(api_client, company_id=get_company_fi().id, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(
    api_client,
    mock_policies_false,
    r_cu,
    get_company_billing_accounts_fi: tp.Callable,
    get_user_billing_accounts_fi: tp.Callable,
    get_billing_transaction_fi: tp.Callable,
    get_billing_transfer_fi: tp.Callable,
    get_billing_transfer_user_fi: tp.Callable,
    get_cu_worker_fi,
):
    contractor_worker_cu = get_cu_worker_fi(company=r_cu.company)
    company_u1 = get_company_billing_accounts_fi(company_id=contractor_worker_cu.company.id)
    company_transaction = get_billing_transaction_fi(user_account=company_u1)
    transfer = get_billing_transfer_fi(company_id=r_cu.company.id, c_outcome_tid=company_transaction.id)
    user_u1, user_u2 = get_user_billing_accounts_fi(
        user_id=contractor_worker_cu.user.id, company_id=r_cu.company.id
    )
    u1_transaction = get_billing_transaction_fi(user_account=user_u1)
    u2_transaction = get_billing_transaction_fi(user_account=user_u1)
    transfer_user = get_billing_transfer_user_fi(
        transfer_id=transfer.id,
        user_id=contractor_worker_cu.user.id,
        u1_outcome_tid=u1_transaction.id,
        u2_income_tid=u2_transaction.id,
    )
    response = __get_response(
        api_client,
        company_id=r_cu.company.id,
        status_codes=status_code.HTTP_200_OK,
        user=r_cu.user,
    )
    assert response.data["balance"] == Decimal(str(company_u1.balance))
    assert response.data["result"][0]["id"] == transfer_user.id
    assert response.data["result"][0]["transfer_id"] == transfer.id
    assert response.data["result"][0]["user_id"] == contractor_worker_cu.user.id
    assert response.data["result"][0]["total_amount"] == transfer_user.total_amount
    assert response.data["result"][0]["u1_outcome_tid"] == u1_transaction.id
    assert response.data["result"][0]["u2_income_tid"] == u2_transaction.id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__contractor_not_accepted_owner__fail(
    api_client,
    get_cu_fi,
    get_company_billing_accounts_fi: tp.Callable,
    get_user_billing_accounts_fi: tp.Callable,
    get_billing_transaction_fi: tp.Callable,
    get_billing_transfer_fi: tp.Callable,
    get_billing_transfer_user_fi: tp.Callable,
    get_cu_worker_fi,
    status,
):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    contractor_worker_cu = get_cu_worker_fi(company=r_cu.company)
    company_u1 = get_company_billing_accounts_fi(company_id=contractor_worker_cu.company.id)
    company_transaction = get_billing_transaction_fi(user_account=company_u1)
    transfer = get_billing_transfer_fi(company_id=r_cu.company.id, c_outcome_tid=company_transaction.id)
    user_u1, user_u2 = get_user_billing_accounts_fi(
        user_id=contractor_worker_cu.user.id, company_id=r_cu.company.id
    )
    u1_transaction = get_billing_transaction_fi(user_account=user_u1)
    u2_transaction = get_billing_transaction_fi(user_account=user_u1)
    get_billing_transfer_user_fi(
        transfer_id=transfer.id,
        user_id=contractor_worker_cu.user.id,
        u1_outcome_tid=u1_transaction.id,
        u2_income_tid=u2_transaction.id,
    )
    response = __get_response(
        api_client,
        company_id=r_cu.company.id,
        user=r_cu.user,
        status_codes=PermissionDenied,
    )
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_contractor_owner__fail(
    api_client,
    get_cu_fi,
    get_company_billing_accounts_fi: tp.Callable,
    get_user_billing_accounts_fi: tp.Callable,
    get_billing_transaction_fi: tp.Callable,
    get_billing_transfer_fi: tp.Callable,
    get_billing_transfer_user_fi: tp.Callable,
    get_cu_worker_fi,
    role,
):
    r_cu = get_cu_fi(role=role)
    contractor_worker_cu = get_cu_worker_fi(company=r_cu.company)
    company_u1 = get_company_billing_accounts_fi(company_id=contractor_worker_cu.company.id)
    company_transaction = get_billing_transaction_fi(user_account=company_u1)
    transfer = get_billing_transfer_fi(company_id=r_cu.company.id, c_outcome_tid=company_transaction.id)
    user_u1, user_u2 = get_user_billing_accounts_fi(
        user_id=contractor_worker_cu.user.id, company_id=r_cu.company.id
    )
    u1_transaction = get_billing_transaction_fi(user_account=user_u1)
    u2_transaction = get_billing_transaction_fi(user_account=user_u1)
    get_billing_transfer_user_fi(
        transfer_id=transfer.id,
        user_id=contractor_worker_cu.user.id,
        u1_outcome_tid=u1_transaction.id,
        u2_income_tid=u2_transaction.id,
    )
    response = __get_response(
        api_client,
        company_id=r_cu.company.id,
        user=r_cu.user,
        status_codes=PermissionDenied,
    )
    assert response.data["detail"] == COMPANY_OWNER_ONLY_ALLOWED
