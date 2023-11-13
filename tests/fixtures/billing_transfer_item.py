import datetime as dt
from typing import Callable
from decimal import Decimal

import pytest

from ma_saas.utils import system
from billing.models import BillingTransferItem


@pytest.fixture
def get_billing_transfer_item_fi() -> Callable:
    def create_instance(
        transfer_id: int,
        u1_income_tid: int,
        receipt_status: str,
        receipt_id: str,
        receipt_url: str,
        amount: Decimal = 9876.00,
    ) -> BillingTransferItem:
        now = system.get_now()
        instance = BillingTransferItem.objects.create(
            transfer_id=transfer_id,
            u1_income_tid=u1_income_tid,
            amount=amount,
            receipt_status=receipt_status,
            receipt_id=receipt_id,
            receipt_url=receipt_url,
            created_at=now,
            updated_at=now,
        )
        return instance

    return create_instance
