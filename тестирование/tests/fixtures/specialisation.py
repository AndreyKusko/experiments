import typing as tp
from typing import Callable

import pytest
from django.utils.crypto import get_random_string

from projects.models.specialisation import Specialisation


@pytest.fixture
def new_specialisation_data() -> Callable:
    def return_data(title: tp.Optional[str] = None) -> tp.Dict[str, tp.Any]:
        title = title or get_random_string()
        return {"title": title}

    return return_data


@pytest.fixture
def get_specialisation_fi(new_specialisation_data: Callable) -> Callable[..., Specialisation]:
    def get_or_create_instance(*args, **kwargs) -> Specialisation:
        data = new_specialisation_data(*args, **kwargs)
        instance = Specialisation.objects.create(**data)
        return instance

    return get_or_create_instance


@pytest.fixture
def specialisation_fi(get_specialisation_fi) -> Specialisation:
    return get_specialisation_fi()
