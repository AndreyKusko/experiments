import datetime as dt
from typing import Callable
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from billing.models import BillingTransfer, BillingTransaction, BillingTransferUser
from ma_saas.settings import REALM_ID
from ma_saas.utils import system

User = get_user_model()


@pytest.fixture
def get_billing_transfer_user_fi() -> Callable:
    def create_instance(
        transfer_id: int,
        user_id: int,
        u1_outcome_tid: int,
        u2_income_tid: int,
        total_amount: Decimal = 9876.00,
    ) -> BillingTransaction:
        instance = BillingTransferUser.objects.create(
            transfer_id=transfer_id,
            realm_id=REALM_ID,
            user_id=user_id,
            total_amount=total_amount,
            u1_outcome_tid=u1_outcome_tid,
            u2_income_tid=u2_income_tid,
            created_at=system.get_now(),
        )
        return instance

    return create_instance
