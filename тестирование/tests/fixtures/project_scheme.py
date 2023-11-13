import typing as tp
from typing import Callable

import pytest
from django.utils.crypto import get_random_string

from projects.models.project import Project
from companies.models.company import Company
from projects.models.project_scheme import ProjectScheme
from projects.models.specialisation import Specialisation


@pytest.fixture
def new_project_scheme_data(get_project_fi, get_company_fi, get_specialisation_fi) -> Callable:
    def return_data(
        title: tp.Optional[str] = None,
        color: tp.Optional[str] = None,
        company: tp.Optional[Company] = None,
        project: tp.Optional[Project] = None,
        specialisation: tp.Optional[Specialisation] = None,
        is_labour_exchange: bool = False,
        service_name_for_receipt: str = None,
        _is_relations_ids: bool = True,
    ) -> tp.Dict[str, tp.Any]:
        title = title or get_random_string()
        color = color or get_random_string()

        if not company and not project:
            company = get_company_fi()
        if not project:
            project = get_project_fi(company=company)
        if service_name_for_receipt is None:
            service_name_for_receipt = get_random_string()
        data = {
            "title": title,
            "color": color,
            "service_name_for_receipt": service_name_for_receipt,
            "is_labour_exchange": is_labour_exchange,
        }
        relation_data = {"project": project, "specialisation": specialisation}
        if _is_relations_ids:
            relation_data = {k: v.id for k, v in relation_data.items() if v}

        return {**data, **relation_data}

    return return_data


@pytest.fixture
def get_project_scheme_fi(new_project_scheme_data: Callable) -> Callable[..., ProjectScheme]:
    def get_or_create_instance(*args, **kwargs) -> ProjectScheme:
        data = new_project_scheme_data(*args, _is_relations_ids=False, **kwargs)
        instance = ProjectScheme.objects.create(**data)
        return instance

    return get_or_create_instance


@pytest.fixture
def project_scheme_fi(get_project_scheme_fi) -> ProjectScheme:
    return get_project_scheme_fi()
