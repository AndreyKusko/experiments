import datetime as dt
from typing import Callable
from decimal import Decimal

import pytest

from ma_saas.utils import system
from billing.models import BillingTransfer, BillingTransaction
from ma_saas.settings import REALM_ID
from ma_saas.constants.constant import TransferStatus


@pytest.fixture
def get_billing_transfer_fi() -> Callable:
    def create_instance(
        company_id: int,
        c_outcome_tid: BillingTransaction,
        max_amount: Decimal = 9988.00,
        total_amount: Decimal = 9876.00,
        total_fee: Decimal = 99.00,
    ) -> BillingTransaction:
        now = system.get_now()
        instance = BillingTransfer.objects.create(
            realm_id=REALM_ID,
            company_id=company_id,
            scheme_id=1,
            status=TransferStatus.DONE.value,
            max_amount=max_amount,
            total_amount=total_amount,
            total_fee=total_fee,
            c_outcome_tid=c_outcome_tid,
            # c_fee_tid=1,
            created_at=now,
            updated_at=now,
        )
        return instance

    return create_instance
