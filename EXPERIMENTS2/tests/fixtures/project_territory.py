import typing as tp
from random import randrange
from typing import Callable

import pytest

from projects.models.project import Project
from companies.models.company import Company
from projects.models.territory import Territory
from projects.models.project_territory import ProjectTerritory


@pytest.fixture
def new_project_territory_data(get_company_fi, get_territory_fi: Callable, get_project_fi) -> Callable:
    def return_data(
        territory: tp.Optional[Territory] = None,
        project: tp.Optional[Project] = None,
        company: tp.Optional[Company] = None,
        is_active: tp.Optional[bool] = True,
        reward: tp.Optional[int] = None,
    ) -> tp.Dict[str, tp.Any]:
        if not company:
            if territory:
                company = territory.company
            elif project:
                company = project.company
            else:
                company = company or get_company_fi()
        territory = territory or get_territory_fi(company=company)
        project = project or get_project_fi(company=company)
        return {
            "territory": territory.id,
            "project": project.id,
            "is_active": is_active,
            "reward": reward or randrange(100),
        }

    return return_data


@pytest.fixture
def get_project_territory_fi(new_project_territory_data: Callable) -> Callable[..., ProjectTerritory]:
    def get_or_create_instance(*args, **kwargs) -> ProjectTerritory:
        data = new_project_territory_data(*args, **kwargs)
        data["territory"] = Territory.objects.get(id=data["territory"])
        data["project"] = Project.objects.get(id=data["project"])
        instance = ProjectTerritory.objects.create(**data)
        return instance

    return get_or_create_instance


@pytest.fixture
def project_territory_fi(get_project_territory_fi) -> ProjectTerritory:
    return get_project_territory_fi()
