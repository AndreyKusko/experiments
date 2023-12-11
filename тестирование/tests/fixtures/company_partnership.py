import typing as tp
from typing import Callable

import pytest

from tests.utils import get_random_email
from companies.models.company import Company
from ma_saas.constants.company import CPS, CUR, CUS, CompanyPartnershipStatus
from companies.models.company_user import CompanyUser
from companies.models.company_partnership import CompanyPartnership


@pytest.fixture
def new_company_partnership_data(get_company_fi, get_cu_fi) -> Callable:
    def return_data(
        inviting_company: tp.Optional[Company] = None,
        inviting_company_user: tp.Optional[CompanyUser] = None,
        invited_company: tp.Optional[Company] = None,
        invited_company_user_email: tp.Optional[str] = "",
        inviting_company_status: tp.Optional[int] = CompanyPartnershipStatus.ACCEPT.value,
        invited_company_status: tp.Optional[int] = CompanyPartnershipStatus.INVITE.value,
    ) -> tp.Dict[str, tp.Any]:

        if not inviting_company:
            if inviting_company_user:
                inviting_company = inviting_company_user.company
            else:
                inviting_company = get_company_fi()

        if not inviting_company_user:
            inviting_company_user = get_cu_fi(
                company=inviting_company, role=CUR.OWNER, status=CUS.INVITE.value
            )
        if not invited_company_user_email and not invited_company:
            invited_company_user_email = get_random_email()

        data = {
            "inviting_company": inviting_company.id,
            "inviting_company_status": inviting_company_status,
            "invited_company_status": invited_company_status,
            "invited_company_user_email": invited_company_user_email,
        }
        if inviting_company_user:
            data["inviting_company_user"] = inviting_company_user.id
        if invited_company:
            data["invited_company"] = invited_company.id
        return data

    return return_data


@pytest.fixture
def get_company_partnership_fi(
    monkeypatch, new_company_partnership_data: Callable
) -> Callable[..., CompanyPartnership]:
    def get_or_create_instance(*args, **kwargs) -> CompanyPartnership:
        data = new_company_partnership_data(*args, **kwargs)
        data["inviting_company"] = Company.objects.get(id=data["inviting_company"])
        if invited_company_id := data.pop("invited_company", None):
            data["invited_company"] = Company.objects.get(id=invited_company_id)
        # if data.get("invited_company_user"):
        #     data["invited_company_user"] = CompanyUser.objects.get(id=data["invited_company_user"])
        if data.get("inviting_company_user"):
            data["inviting_company_user"] = CompanyUser.objects.get(id=data["inviting_company_user"])
        instance = CompanyPartnership.objects.create(**data)
        return instance

    return get_or_create_instance


@pytest.fixture
def company_partnership_fi(get_company_fi) -> Company:
    return get_company_fi()


@pytest.fixture
def get_active_company_partnership_fi(
    monkeypatch, new_company_partnership_data: Callable
) -> Callable[..., CompanyPartnership]:
    def get_or_create_instance(*args, **kwargs) -> CompanyPartnership:
        data = new_company_partnership_data(*args, **kwargs)
        data["inviting_company"] = Company.objects.get(id=data["inviting_company"])
        if invited_company_id := data.pop("invited_company", None):
            data["invited_company"] = Company.objects.get(id=invited_company_id)
        if data.get("inviting_company_user"):
            data["inviting_company_user"] = CompanyUser.objects.get(id=data["inviting_company_user"])
        data["inviting_company_status"] = CPS.ACCEPT.value
        data["invited_company_status"] = CPS.ACCEPT.value
        instance = CompanyPartnership.objects.create(**data)
        return instance

    return get_or_create_instance
