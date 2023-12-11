from typing import Callable

import pytest
from django.utils.crypto import get_random_string

from ma_saas.utils import system
from billing.models import BillingAccount, BillingTransaction


@pytest.fixture
def get_billing_transaction_fi() -> Callable:
    def create_instance(
        user_account: BillingAccount, amount: float = 1.00, unmarked_amount: float = 1.00
    ) -> BillingTransaction:
        now = system.get_now()
        instance = BillingTransaction.objects.create(
            user_account_id=user_account.id,
            title=get_random_string(),
            system_account=1,
            amount=amount,
            unmarked_amount=unmarked_amount,
            status=3,
            created_at=now,
            updated_at=now,
        )
        return instance

    return create_instance
