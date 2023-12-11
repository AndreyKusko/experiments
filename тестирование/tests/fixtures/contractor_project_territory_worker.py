import typing as tp
from typing import Callable

import pytest

from projects.models.project import Project
from companies.models.company import Company
from ma_saas.constants.company import CUR, CUS
from companies.models.company_user import CompanyUser
from projects.models.project_territory import ProjectTerritory
from projects.models.contractor_project_territory_worker import ContractorProjectTerritoryWorker


@pytest.fixture
def new_contractor_pt_worker_data(
    get_company_fi,
    get_project_territory_fi: Callable,
    get_territory_fi: Callable,
    get_project_fi,
    get_cu_fi,
    _is_relations_ids: bool = True,
) -> Callable:
    def return_data(
        company: tp.Optional[Company] = None,
        project: tp.Optional[Project] = None,
        territory: tp.Optional[Project] = None,
        project_territory: tp.Optional[ProjectTerritory] = None,
        company_user: tp.Optional[CompanyUser] = None,
        _is_relations_ids=True,
    ) -> tp.Dict[str, tp.Any]:

        if not company:
            if company_user:
                company = company_user.company
            elif project_territory:
                company = project_territory.project.company
            elif project:
                company = project.company
            else:
                company = get_company_fi()
        if not project_territory:
            project_territory = get_project_territory_fi(
                company=company,
                project=project or get_project_fi(company=company),
                territory=territory or get_territory_fi(company=company),
            )

        if not company_user:
            company_user = get_cu_fi(company=company, role=CUR.WORKER, status=CUS.ACCEPT.value)

        relation_data = {"project_territory": project_territory, "company_user": company_user}
        if _is_relations_ids:
            relation_data = {k: v.id for k, v in relation_data.items()}

        return relation_data

    return return_data


@pytest.fixture
def get_pt_worker_fi(
    new_contractor_pt_worker_data,
) -> Callable[..., ContractorProjectTerritoryWorker]:
    def get_or_create_instance(*args, **kwargs) -> ContractorProjectTerritoryWorker:
        data = new_contractor_pt_worker_data(*args, _is_relations_ids=False, **kwargs)
        instance = ContractorProjectTerritoryWorker.objects.create(**data)
        return instance

    return get_or_create_instance


@pytest.fixture
def contractor_pt_worker_fi(get_pt_worker_fi) -> ContractorProjectTerritoryWorker:
    return get_pt_worker_fi()
