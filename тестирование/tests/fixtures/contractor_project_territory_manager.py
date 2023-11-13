import typing as tp
from typing import Callable

import pytest

from projects.models.project import Project
from companies.models.company import Company
from ma_saas.constants.company import CUS
from projects.models.territory import Territory
from companies.models.company_user import CompanyUser
from projects.models.project_territory import ProjectTerritory
from projects.models.contractor_project_territory_manager import ContractorProjectTerritoryManager


@pytest.fixture
def new_contractor_pt_manager_data(
    get_company_fi,
    get_project_territory_fi: Callable,
    get_territory_fi: Callable,
    get_project_fi,
    get_cu_manager_fi,
) -> Callable:
    def return_data(
        company: tp.Optional[Company] = None,
        project: tp.Optional[Project] = None,
        territory: tp.Optional[Territory] = None,
        project_territory: tp.Optional[ProjectTerritory] = None,
        company_user: tp.Optional[CompanyUser] = None,
    ) -> tp.Dict[str, tp.Any]:

        if not project_territory or not company_user or not company:
            if project_territory:
                company = project_territory.project.company
            elif company_user:
                company = company_user.company
            elif project:
                company = project.company
            elif territory:
                company = territory.company
            else:
                company = company or get_company_fi()

        project_territory = project_territory or get_project_territory_fi(
            company=company,
            project=project or get_project_fi(company=company),
            territory=territory or get_territory_fi(company=company),
        )
        company_user = company_user or get_cu_manager_fi(company=company, status=CUS.ACCEPT.value)
        return {
            "project_territory": project_territory.id,
            "company_user": company_user.id,
        }

    return return_data


@pytest.fixture
def get_contractor_pt_manager_fi(
    monkeypatch, new_contractor_pt_manager_data: Callable
) -> Callable[..., ContractorProjectTerritoryManager]:
    def get_or_create_instance(*args, **kwargs) -> ContractorProjectTerritoryManager:
        # monkeypatch.setattr(ContractorProjectTerritoryManager, "create_policies", lambda *a, **kw: None)
        # monkeypatch.setattr(ContractorProjectTerritoryManager, "remove_policies", lambda *a, **kw: None)

        data = new_contractor_pt_manager_data(*args, **kwargs)
        data["project_territory"] = ProjectTerritory.objects.get(id=data["project_territory"])
        data["company_user"] = CompanyUser.objects.get(id=data["company_user"])
        instance = ContractorProjectTerritoryManager.objects.create(**data)
        return instance

    return get_or_create_instance


@pytest.fixture
def contractor_pt_manager_fi(get_contractor_pt_manager_fi: Callable) -> ContractorProjectTerritoryManager:
    return get_contractor_pt_manager_fi()
