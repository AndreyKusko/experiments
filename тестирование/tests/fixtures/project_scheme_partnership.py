import typing as tp
from typing import Callable

import pytest

from projects.models.project_scheme import ProjectScheme
from projects.models.project_partnership import ProjectPartnership
from companies.models.company_partnership import CompanyPartnership
from projects.models.project_scheme_partnership import ProjectSchemePartnership


@pytest.fixture
def new_project_scheme_partnership_data(get_project_partnership_fi, get_project_scheme_fi) -> Callable:
    def return_data(
        company_partnership: tp.Optional[CompanyPartnership] = None,
        project_partnership: tp.Optional[ProjectPartnership] = None,
        project_scheme: tp.Optional[ProjectScheme] = None,
        is_processed_reports_acceptance_allowed: bool = True,
        _is_relations_ids: bool = True,
    ) -> tp.Dict[str, tp.Any]:
        if not project_partnership:
            if project_scheme:
                project_partnership = get_project_partnership_fi(project=project_scheme.project)
            elif company_partnership:
                project_partnership = get_project_partnership_fi(company_partnership=company_partnership)
            else:
                project_partnership = get_project_partnership_fi()

        if not project_scheme:
            if project_partnership:
                project_scheme = get_project_scheme_fi(project=project_partnership.project)
            elif company_partnership:
                project_scheme = get_project_scheme_fi(company=company_partnership.inviting_company)
            else:
                project_scheme = get_project_scheme_fi()

        relation_data = {"project_scheme": project_scheme, "project_partnership": project_partnership}
        if _is_relations_ids:
            relation_data = {k: v.id for k, v in relation_data.items() if v}

        data = {"is_processed_reports_acceptance_allowed": is_processed_reports_acceptance_allowed}
        return {**relation_data, **data}

    return return_data


@pytest.fixture
def get_project_scheme_partnership_fi(
    new_project_scheme_partnership_data: Callable,
) -> Callable[..., ProjectSchemePartnership]:
    def get_or_create_instance(*args, **kwargs) -> ProjectSchemePartnership:
        data = new_project_scheme_partnership_data(*args, _is_relations_ids=False, **kwargs)
        instance = ProjectSchemePartnership.objects.create(**data)
        return instance

    return get_or_create_instance


@pytest.fixture
def project_scheme_partnership_fi(
    get_project_scheme_partnership_fi, get_company_partnership_fi, get_project_partnership_fi, get_company_fi
) -> ProjectSchemePartnership:
    company_partnership = get_company_partnership_fi(
        invited_company=get_company_fi(), inviting_company=get_company_fi()
    )
    project_partnership = get_project_partnership_fi(company_partnership=company_partnership)
    return get_project_scheme_partnership_fi(project_partnership=project_partnership)
