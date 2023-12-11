import typing as tp
from typing import Callable

import pytest
from django.utils.crypto import get_random_string

from projects.models.project import Project
from companies.models.company import Company
from projects.models.project_variable import ProjectVariable, ProjectVariableKind


@pytest.fixture
def new_project_variable_data(get_project_fi, get_company_fi) -> Callable:
    def return_data(
        title: tp.Optional[str] = None,
        key: tp.Optional[str] = None,
        kind: tp.Optional[int] = None,
        project: tp.Optional[Project] = "",
        company: tp.Optional[Company] = "",
        _is_relations_ids: bool = True,
    ) -> tp.Dict[str, tp.Any]:

        title = title or get_random_string()
        key = key or get_random_string()
        kind = kind or ProjectVariableKind.NUMBER

        if not project:
            company = company or get_company_fi()
            project = get_project_fi(company=company)

        data = {"title": title, "key": key, "kind": kind}

        relation_data = {"project": project}
        if _is_relations_ids:
            relation_data = {k: v.id for k, v in relation_data.items()}

        return {**data, **relation_data}

    return return_data


@pytest.fixture
def get_project_variable_fi(new_project_variable_data: Callable) -> Callable[..., ProjectVariable]:
    def get_or_create_instance(*args, **kwargs) -> ProjectVariable:
        data = new_project_variable_data(*args, _is_relations_ids=False, **kwargs)
        instance = ProjectVariable.objects.create(**data)
        return instance

    return get_or_create_instance


@pytest.fixture
def project_variable_fi(get_project_variable_fi) -> ProjectVariable:
    return get_project_variable_fi()
