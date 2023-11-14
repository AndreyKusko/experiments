import typing as tp
from typing import Callable

import pytest
from django.utils.crypto import get_random_string

from projects.models.project import Project
from companies.models.company import Company
from ma_saas.constants.project import ProjectStatus


@pytest.fixture
def new_project_data(get_company_fi) -> Callable:
    def return_data(
        title: tp.Optional[str] = None,
        description: tp.Optional[str] = None,
        company: tp.Optional[Company] = "",
        status: tp.Optional[ProjectStatus] = ProjectStatus.ACTIVE.value,
        _is_relations_ids: bool = True,
    ) -> tp.Dict[str, tp.Any]:
        title = title or get_random_string()
        description = description or get_random_string()
        company = company or get_company_fi()
        data = {
            "title": title,
            "description": description,
            "status": status,
        }

        relation_data = {"company": company}
        if _is_relations_ids:
            relation_data = {k: v.id for k, v in relation_data.items()}

        return {**data, **relation_data}

    return return_data


@pytest.fixture
def get_project_fi(new_project_data: Callable) -> Callable[..., Project]:
    def get_or_create_instance(*args, **kwargs) -> Project:
        data = new_project_data(*args, _is_relations_ids=False, **kwargs)
        instance = Project.objects.create(**data)
        return instance

    return get_or_create_instance


@pytest.fixture
def project_fi(get_project_fi) -> Project:
    return get_project_fi()
