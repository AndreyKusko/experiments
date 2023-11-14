from typing import Callable

import pytest
from django.utils.crypto import get_random_string

from reports.models.worker_report import WorkerReport


@pytest.fixture
def get_billing_transaction_for_export_transactions_receipts_test(
    get_pt_worker_fi,
    get_worker_report_fi: Callable,
    get_user_billing_accounts_fi: Callable,
    get_worker_report_transaction_fi: Callable,
    get_billing_transfer_fi: Callable,
    get_billing_transfer_item_fi: Callable,
    get_billing_transaction_fi: Callable,
) -> Callable:
    def return_instance(company):
        pt_worker = get_pt_worker_fi(company=company)
        worker_report: WorkerReport = get_worker_report_fi(project_territory_worker=pt_worker)
        u1, u2 = get_user_billing_accounts_fi(user_id=pt_worker.company_user.user.id, company_id=company.id)

        billing_transaction = get_billing_transaction_fi(user_account=u1)
        get_worker_report_transaction_fi(worker_report=worker_report, transaction_id=billing_transaction.id)
        billing_transfer = get_billing_transfer_fi(
            company_id=company.id, c_outcome_tid=billing_transaction.id
        )
        get_billing_transfer_item_fi(
            transfer_id=billing_transfer.id,
            u1_income_tid=billing_transaction.id,
            receipt_status="accepted",
            receipt_id=get_random_string(),
            receipt_url=f"http://{get_random_string()}.qwe/{get_random_string()}",
        )

        return billing_transaction

    return return_instance
