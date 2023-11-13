import json
import typing as tp
from typing import Callable

import pytest
from django.utils.crypto import get_random_string

from companies.models.company import Company
from clients.dnsmadeeasy.views import RequestDmsEasy
from clients.billing.interfaces.company import CompanyBillingInterface


@pytest.fixture
def new_company_data() -> Callable:
    def return_data(
        title: tp.Optional[str] = None,
        is_deleted: tp.Optional[bool] = False,
        logo: tp.Optional[dict] = None,
        support_email: tp.Optional[str] = None,
        subdomain: tp.Optional[str] = None,
    ) -> tp.Dict[str, tp.Any]:
        title = title or get_random_string()
        subdomain = subdomain or get_random_string(length=5)
        data = {"title": title, "is_deleted": is_deleted, "logo": json.dumps(logo or {})}
        if subdomain:
            data["subdomain"] = subdomain
        if support_email:
            data["support_email"] = support_email
        return data

    return return_data


@pytest.fixture
def get_company_fi(monkeypatch, new_company_data: Callable) -> Callable[..., Company]:
    def create_instance(*args, **kwargs) -> Company:
        monkeypatch.setattr(RequestDmsEasy, "create_subdomain", lambda *a, **kw: None)
        monkeypatch.setattr(CompanyBillingInterface, "create_account", lambda *args, **kwargs: None)

        data = new_company_data(*args, **kwargs)
        instance = Company.objects.create(**data)
        return instance

    return create_instance


@pytest.fixture
def company_fi(get_company_fi) -> Company:
    return get_company_fi()
