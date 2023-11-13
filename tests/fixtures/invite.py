import typing as tp

import pytest
from django.utils.crypto import get_random_string

from companies.models.company import Company
from ma_saas.constants.system import Callable
from ma_saas.constants.company import CUR

"""Функция инвайта сделана на основании моделей: CompanyUser, User так что используй в фикстуры для них."""


@pytest.fixture
def new_invite_data(get_company_fi) -> Callable:
    def return_data(
        phone: tp.Optional[str] = None,
        email: tp.Optional[str] = None,
        company: tp.Optional[Company] = None,
        role: tp.Optional[int] = None,
    ) -> tp.Dict[str, tp.Union[str, int]]:
        company = company or get_company_fi()
        return {
            "phone": phone or "+7" + get_random_string(length=10, allowed_chars="0123456789"),
            "email": email or get_random_string(length=4) + "@test.ru",
            "company": company.id,
            "role": role or CUR.WORKER.value,
        }

    return return_data
