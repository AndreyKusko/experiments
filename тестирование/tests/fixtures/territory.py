import typing as tp
from typing import Callable

import pytest
from django.utils.crypto import get_random_string

from companies.models.company import Company
from projects.models.territory import Territory


@pytest.fixture
def new_territory_data(get_company_fi) -> Callable:
    def return_data(
        title: tp.Optional[str] = None, company: tp.Optional[Company] = None
    ) -> tp.Dict[str, tp.Any]:
        title = title or get_random_string()
        company = company or get_company_fi()
        return {"title": title, "company": company.id}

    return return_data


@pytest.fixture
def get_territory_fi(new_territory_data: Callable) -> Callable[..., Territory]:
    def get_or_create_instance(*args, **kwargs) -> Territory:
        data = new_territory_data(*args, **kwargs)
        data["company"] = Company.objects.get(id=data["company"])
        instance = Territory.objects.create(**data)
        return instance

    return get_or_create_instance


@pytest.fixture
def territory_fi(get_territory_fi) -> Territory:
    return get_territory_fi()
