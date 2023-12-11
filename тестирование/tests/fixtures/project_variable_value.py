import typing as tp
from typing import Callable

import pytest
from django.utils.crypto import get_random_string

from tests.utils import get_random_int
from projects.models.project import Project
from companies.models.company import Company
from projects.models.project_variable import ProjectVariable
from projects.models.project_variable_value import ProjectVariableValue, ProjectVariableValueModelName


@pytest.fixture
def new_project_variable_value_data(get_project_fi, get_company_fi, get_project_variable_fi) -> Callable:
    def return_data(
        model_id: tp.Optional[int] = None,
        model_name: tp.Optional[int] = None,
        value: tp.Optional[str] = None,
        project: tp.Optional[Project] = "",
        company: tp.Optional[Company] = "",
        project_variable: tp.Optional[ProjectVariable] = "",
        _is_relations_ids: bool = True,
    ) -> tp.Dict[str, tp.Any]:

        value = value or get_random_string()
        model_id = model_id or get_random_int()
        model_name = model_name or ProjectVariableValueModelName.WORKER_INSTRUCTION

        if not project_variable:
            if not company and not project:
                company = get_company_fi()
            if not project:
                project = get_project_fi(company=company)
            project_variable = get_project_variable_fi(project=project)

        data = {"model_id": model_id, "value": value}

        relation_data = {"project_variable": project_variable}
        if _is_relations_ids:
            relation_data = {k: v.id for k, v in relation_data.items()}

        select_field = {"model_name": model_name}
        if _is_relations_ids:
            select_field = {k: v.value for k, v in select_field.items()}
        return {**data, **relation_data, **select_field}

    return return_data


@pytest.fixture
def get_project_variable_value_fi(
    new_project_variable_value_data: Callable,
) -> Callable[..., ProjectVariableValue]:
    def get_or_create_instance(*args, **kwargs) -> ProjectVariableValue:
        data = new_project_variable_value_data(*args, _is_relations_ids=False, **kwargs)
        instance = ProjectVariableValue.objects.create(**data)
        return instance

    return get_or_create_instance


@pytest.fixture
def project_variable_value_fi(get_project_variable_value_fi) -> ProjectVariableValue:
    return get_project_variable_value_fi()
