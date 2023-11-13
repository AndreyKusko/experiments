import typing as tp
from typing import Callable

import pytest

from projects.models.project import Project
from ma_saas.constants.project import PPS, ProjectPartnershipStatus
from companies.models.company_user import CompanyUser
from projects.models.project_partnership import ProjectPartnership
from companies.models.company_partnership import CompanyPartnership


@pytest.fixture
def new_project_partnership_data(get_project_fi, get_company_partnership_fi, get_cu_fi) -> Callable:
    def return_data(
        project: tp.Optional[Project] = None,
        company_partnership: tp.Optional[CompanyPartnership] = None,
        invited_company_status: tp.Optional[int] = ProjectPartnershipStatus.ACCEPT.value,
        inviting_company_status: tp.Optional[int] = ProjectPartnershipStatus.ACCEPT.value,
        inviting_company_user: tp.Optional[CompanyUser] = None,
    ) -> tp.Dict[str, tp.Any]:
        if not company_partnership:
            if project:
                company_partnership = get_company_partnership_fi(inviting_company=project.company)
            elif inviting_company_user:
                company_partnership = get_company_partnership_fi(
                    inviting_company=inviting_company_user.company
                )
            else:
                company_partnership = get_company_partnership_fi()

        if not project:
            if company_partnership:
                project = get_project_fi(company=company_partnership.inviting_company)
            elif inviting_company_user:
                project = get_project_fi(company=inviting_company_user.company)
            else:
                project = get_project_fi()
        if not inviting_company_user:
            if company_partnership:
                inviting_company_user = get_cu_fi(company=company_partnership.inviting_company)

        data = {
            "project": project.id,
            "company_partnership": company_partnership.id,
            "invited_company_status": invited_company_status,
            "inviting_company_status": inviting_company_status,
            "inviting_company_user": inviting_company_user.id,
        }
        return data

    return return_data


@pytest.fixture
def get_project_partnership_fi(new_project_partnership_data: Callable) -> Callable[..., ProjectPartnership]:
    def get_or_create_instance(*args, **kwargs) -> ProjectPartnership:
        data = new_project_partnership_data(*args, **kwargs)
        data["project"] = Project.objects.get(id=data["project"])
        data["company_partnership"] = CompanyPartnership.objects.get(id=data["company_partnership"])
        data["inviting_company_user"] = CompanyUser.objects.get(id=data["inviting_company_user"])
        instance = ProjectPartnership.objects.create(**data)
        return instance

    return get_or_create_instance


@pytest.fixture
def project_partnership_fi(get_project_partnership_fi) -> ProjectPartnership:
    return get_project_partnership_fi()


@pytest.fixture
def get_active_project_partnership_fi(
    new_project_partnership_data: Callable,
) -> Callable[..., ProjectPartnership]:
    def get_or_create_instance(*args, **kwargs) -> ProjectPartnership:
        data = new_project_partnership_data(*args, **kwargs)
        data["project"] = Project.objects.get(id=data["project"])
        data["company_partnership"] = CompanyPartnership.objects.get(id=data["company_partnership"])
        data["inviting_company_user"] = CompanyUser.objects.get(id=data["inviting_company_user"])
        data["inviting_company_status"] = PPS.ACCEPT.value
        data["invited_company_status"] = PPS.ACCEPT.value
        instance = ProjectPartnership.objects.create(**data)
        return instance

    return get_or_create_instance
