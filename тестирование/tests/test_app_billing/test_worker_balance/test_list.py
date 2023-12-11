import typing as tp
import functools
from decimal import Decimal

import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated

from tests.utils import request_response_list
from ma_saas.constants.system import DATETIME_FORMAT
from companies.models.company_user import CompanyUser

User = get_user_model()


__get_response = functools.partial(request_response_list, path="/api/v1/worker-balance/")


def test__anonymous(api_client):
    response = __get_response(api_client, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_worker_fi")])
def test__response_with_worker_report_transaction(
    api_client,
    r_cu,
    get_pt_worker_fi,
    get_worker_report_fi: tp.Callable,
    get_worker_report_transaction_fi: tp.Callable,
    get_user_billing_accounts_fi: tp.Callable,
    get_billing_transaction_fi: tp.Callable,
):
    pt_worker = get_pt_worker_fi(company_user=r_cu)
    worker_report = get_worker_report_fi(project_territory_worker=pt_worker)
    u1, u2 = get_user_billing_accounts_fi(user_id=r_cu.user.id, company_id=r_cu.company.id)
    billing_transaction = get_billing_transaction_fi(user_account=u1)
    worker_report_transaction = get_worker_report_transaction_fi(
        worker_report=worker_report, transaction_id=billing_transaction.id
    )
    response = __get_response(api_client, status_codes=status_code.HTTP_200_OK, user=r_cu.user)
    assert len(response.data["result"]) == 1

    transaction_result = response.data["result"][0]
    assert transaction_result["id"] == billing_transaction.id
    assert transaction_result["amount"] == str(billing_transaction.amount) + "0"
    assert transaction_result["unmarked_amount"] == str(billing_transaction.unmarked_amount) + "0"
    assert transaction_result["status"] == billing_transaction.status
    assert transaction_result["created_at"] == billing_transaction.created_at.strftime(DATETIME_FORMAT)

    worker_report_result = transaction_result["worker_report"]
    assert worker_report_result["id"] == worker_report_transaction.id
    assert worker_report_result["created_at"] == worker_report_transaction.created_at.strftime(
        DATETIME_FORMAT
    )
    assert worker_report_result["transaction_id"] == billing_transaction.id
    assert worker_report_result["company"]["id"] == r_cu.company.id
    assert worker_report_result["company"]["title"] == r_cu.company.title
    assert worker_report_result["project"]["id"] == worker_report.project_territory.project.id
    assert worker_report_result["project"]["title"] == worker_report.project_territory.project.title
    assert worker_report_result["territory"]["id"] == worker_report.project_territory.territory.id
    assert worker_report_result["territory"]["title"] == worker_report.project_territory.territory.title
    assert transaction_result["billing_transfer_user"] == {}

    assert response.data["accrued"] == Decimal(str(u1.balance))
    assert response.data["available"] == Decimal(str(u2.balance))


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_worker_fi")])
def test__response_with_billing_transfer(
    api_client,
    r_cu,
    get_company_billing_accounts_fi: tp.Callable,
    get_billing_transfer_fi: tp.Callable,
    get_billing_transfer_user_fi: tp.Callable,
    get_user_billing_accounts_fi: tp.Callable,
    get_billing_transaction_fi: tp.Callable,
):
    company_u1 = get_company_billing_accounts_fi(company_id=r_cu.company.id)
    company_transaction = get_billing_transaction_fi(user_account=company_u1)
    transfer = get_billing_transfer_fi(company_id=r_cu.company.id, c_outcome_tid=company_transaction.id)
    user_u1, user_u2 = get_user_billing_accounts_fi(user_id=r_cu.user.id, company_id=r_cu.company.id)
    u1_transaction = get_billing_transaction_fi(user_account=user_u1)
    u2_transaction = get_billing_transaction_fi(user_account=user_u1)
    transfer_user = get_billing_transfer_user_fi(
        transfer_id=transfer.id,
        user_id=r_cu.user.id,
        u1_outcome_tid=u1_transaction.id,
        u2_income_tid=u2_transaction.id,
    )
    response = __get_response(api_client, status_codes=status_code.HTTP_200_OK, user=r_cu.user)
    assert len(response.data["result"]) == 2

    result_u2_transaction = response.data["result"][0]
    assert result_u2_transaction["id"] == u2_transaction.id
    assert result_u2_transaction["amount"] == str(u2_transaction.amount) + "0"
    assert result_u2_transaction["unmarked_amount"] == str(u2_transaction.unmarked_amount) + "0"
    assert result_u2_transaction["status"] == u2_transaction.status
    assert result_u2_transaction["created_at"] == u2_transaction.created_at.strftime(DATETIME_FORMAT)
    assert result_u2_transaction["worker_report"] == {}

    assert result_u2_transaction["billing_transfer_user"]["id"] == transfer_user.id
    assert result_u2_transaction["billing_transfer_user"]["transfer_id"] == transfer.id
    assert result_u2_transaction["billing_transfer_user"]["realm_id"] == transfer_user.realm_id
    assert result_u2_transaction["billing_transfer_user"]["user_id"] == r_cu.user.id
    assert result_u2_transaction["billing_transfer_user"]["total_amount"] == transfer_user.total_amount
    assert result_u2_transaction["billing_transfer_user"]["u1_outcome_tid"] == u1_transaction.id
    assert result_u2_transaction["billing_transfer_user"]["u2_income_tid"] == u2_transaction.id
    assert result_u2_transaction["billing_transfer_user"]["created_at"] == transfer_user.created_at.strftime(
        DATETIME_FORMAT
    )
    assert result_u2_transaction["billing_transfer_user"]["company"]["id"] == r_cu.company.id
    assert result_u2_transaction["billing_transfer_user"]["company"]["title"] == r_cu.company.title

    result_u1_transaction = response.data["result"][1]
    assert result_u1_transaction["id"] == u1_transaction.id
    assert result_u1_transaction["amount"] == str(u1_transaction.amount) + "0"
    assert result_u1_transaction["unmarked_amount"] == str(u1_transaction.unmarked_amount) + "0"
    assert result_u1_transaction["status"] == u1_transaction.status
    assert result_u1_transaction["created_at"] == u1_transaction.created_at.strftime(DATETIME_FORMAT)
    assert result_u1_transaction["worker_report"] == {}

    assert result_u1_transaction["billing_transfer_user"]["id"] == transfer_user.id
    assert result_u1_transaction["billing_transfer_user"]["transfer_id"] == transfer.id
    assert result_u1_transaction["billing_transfer_user"]["realm_id"] == transfer_user.realm_id
    assert result_u1_transaction["billing_transfer_user"]["user_id"] == r_cu.user.id
    assert result_u1_transaction["billing_transfer_user"]["total_amount"] == transfer_user.total_amount
    assert result_u1_transaction["billing_transfer_user"]["u1_outcome_tid"] == u1_transaction.id
    assert result_u1_transaction["billing_transfer_user"]["u2_income_tid"] == u2_transaction.id
    assert result_u1_transaction["billing_transfer_user"]["created_at"] == transfer_user.created_at.strftime(
        DATETIME_FORMAT
    )
    assert result_u1_transaction["billing_transfer_user"]["company"]["id"] == r_cu.company.id
    assert result_u1_transaction["billing_transfer_user"]["company"]["title"] == r_cu.company.title

    assert response.data["accrued"] == Decimal(str(user_u1.balance))
    assert response.data["available"] == Decimal(str(user_u2.balance))


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_worker_fi")])
def test__worker__success(
    api_client,
    r_cu,
    get_pt_worker_fi,
    get_worker_report_fi,
    get_user_billing_accounts_fi,
    get_worker_report_transaction_fi,
    get_billing_transaction_fi,
):
    pt_worker = get_pt_worker_fi(company_user=r_cu)
    worker_report = get_worker_report_fi(project_territory_worker=pt_worker)
    u1, u2 = get_user_billing_accounts_fi(user_id=r_cu.user.id, company_id=r_cu.company.id)
    billing_transaction = get_billing_transaction_fi(user_account=u1)
    get_worker_report_transaction_fi(worker_report=worker_report, transaction_id=billing_transaction.id)
    response = __get_response(api_client, status_codes=status_code.HTTP_200_OK, user=r_cu.user)
    assert response.data["result"]
    assert response.data["accrued"]
    assert response.data["available"]
