import json
import typing as tp
from typing import Callable

import pytest

from projects.models.project import Project
from companies.models.company import Company
from projects.models.project_scheme import ProjectScheme
from reports.models.worker_instruction import WorkerInstruction


@pytest.fixture
def new_worker_instruction_data(get_project_fi, get_company_fi, get_project_scheme_fi) -> Callable:
    def return_data(
        title: tp.Optional[str] = None,
        company: tp.Optional[Company] = None,
        project: tp.Optional[Project] = None,
        project_scheme: tp.Optional[ProjectScheme] = None,
        instructions_data: tp.Optional[tp.List[str]] = None,
        _is_relations_ids: bool = True,
    ) -> tp.Dict[str, tp.Any]:

        if project_scheme:
            relation_data = {"project_scheme": project_scheme}
        else:
            if project:
                pass
            elif company:
                project = get_project_fi(company=company)
            else:
                project = get_project_fi()
            relation_data = {"project": project}

        if _is_relations_ids:
            relation_data = {k: v.id for k, v in relation_data.items()}

        data = {"data": instructions_data or []}
        if _is_relations_ids:
            data["data"] = json.dumps(data["data"])

        result_data = {**data, **relation_data}

        if title is not None:
            result_data[title] = title
        return result_data

    return return_data


@pytest.fixture
def get_worker_instruction_fi(new_worker_instruction_data: Callable) -> Callable[..., WorkerInstruction]:
    def get_or_create_instance(*args, **kwargs) -> WorkerInstruction:
        data = new_worker_instruction_data(*args, _is_relations_ids=False, **kwargs)
        instance = WorkerInstruction.objects.create(**data)
        return instance

    return get_or_create_instance


@pytest.fixture
def worker_instruction_fi(get_worker_instruction_fi) -> WorkerInstruction:
    return get_worker_instruction_fi()
