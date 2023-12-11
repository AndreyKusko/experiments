import typing as tp
from typing import Callable
from decimal import Decimal
from datetime import datetime

import pytest

from ma_saas.utils import system
from billing.models import BillingAccount
from ma_saas.settings import REALM_ID
from ma_saas.constants.constant import Billing, AccountKind


@pytest.fixture
def get_billing_account_fi() -> Callable:
    def create_instance(
        kind: AccountKind,
        user_id: int = None,
        company_id: int = None,
        scheme_id: int = None,
        balance: float = 123.12,
        balance_version_mark: str = "",
    ) -> BillingAccount:
        now = system.get_now()
        instance = BillingAccount.objects.create(
            balance=balance,
            realm_id=REALM_ID,
            user_id=user_id,
            company_id=company_id,
            scheme_id=scheme_id,
            kind=kind,
            balance_version_mark=balance_version_mark,
            created_at=now,
            updated_at=now,
        )
        return instance

    return create_instance


@pytest.fixture
def get_user_billing_accounts_fi() -> Callable:
    def create_instance(
        user_id: int, company_id: int, balance_version_mark: str = ""
    ) -> tp.Tuple[BillingAccount, BillingAccount]:
        now = system.get_now()
        u1 = BillingAccount.objects.create(
            balance=123.12,
            realm_id=REALM_ID,
            user_id=user_id,
            company_id=company_id,
            kind=AccountKind.U1.value,
            balance_version_mark=balance_version_mark,
            created_at=now,
            updated_at=now,
        )
        u2 = BillingAccount.objects.create(
            balance=987.98,
            scheme_id=1,
            realm_id=REALM_ID,
            user_id=user_id,
            kind=AccountKind.U2.value,
            balance_version_mark=balance_version_mark,
            created_at=now,
            updated_at=now,
        )
        return u1, u2

    return create_instance


@pytest.fixture
def get_company_billing_accounts_fi(get_billing_account_fi) -> Callable:
    def create_instance(
        company_id: int, balance: Decimal = 9876.54, balance_version_mark: str = ""
    ) -> tp.Tuple[BillingAccount, BillingAccount]:
        u1 = get_billing_account_fi(
            balance=balance,
            company_id=company_id,
            kind=AccountKind.COMPANY.value,
            scheme_id=Billing.CREATE_COMPANY_ACCOUNT_SCHEME_ID,
            balance_version_mark=balance_version_mark,
        )
        return u1

    return create_instance
