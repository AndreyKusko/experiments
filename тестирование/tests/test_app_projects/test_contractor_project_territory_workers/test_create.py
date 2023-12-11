import functools

import pytest
from django.forms import model_to_dict
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_create
from accounts.models import USER_IS_BLOCKED, USER_IS_DELETED, NOT_TA_USER_REASON
from ma_saas.constants.system import Callable
from ma_saas.constants.company import CUR, ROLES, NOT_ACCEPT_CUS, NOT_WORKER_ROLES, NOT_ACCEPT_CUS_VALUES
from companies.models.company_user import (
    CU_IS_DELETED,
    NOT_TA_RCU_REASON,
    TARGET_ROLE_WRONG,
    CUS_MUST_BE_ACCEPT,
    NOT_TA_TARGET_CU_REASON,
    CompanyUser,
)
from companies.permissions.company_user import REQUESTING_USER_NOT_BELONG_TO_COMPANY
from projects.models.contractor_project_territory_worker import (
    UNIQ_CONSTRAINT_ERR,
    ContractorProjectTerritoryWorker,
)

User = get_user_model()

__get_response = functools.partial(
    request_response_create, path="/api/v1/contractor-project-territory-workers/"
)


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, {}, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(api_client, r_cu: CompanyUser, new_contractor_pt_worker_data):
    data = new_contractor_pt_worker_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user)
    new_instance = model_to_dict(ContractorProjectTerritoryWorker.objects.get(**data))
    assert len(response.data["company_user"]) == 11
    assert response.data["company_user"]["id"] == data.pop("company_user")
    assert all(new_instance[key] == response.data[key] == value for key, value in data.items())


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, new_contractor_pt_worker_data):
    data = new_contractor_pt_worker_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user)
    new_instance = ContractorProjectTerritoryWorker.objects.get(**data)
    assert new_instance.id == response.data["id"]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__related__manager__success(
    api_client, get_cu_worker_fi_fi, r_cu, new_contractor_pt_worker_data, get_project_territory_fi
):
    pt = get_project_territory_fi(company=r_cu.company)
    target_cu = get_cu_worker_fi_fi(company=r_cu.company)
    data = new_contractor_pt_worker_data(project_territory=pt, company_user=target_cu)
    response = __get_response(api_client, data=data, user=r_cu.user)
    new_instance = ContractorProjectTerritoryWorker.objects.get(**data)
    assert new_instance.id == response.data["id"]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("target_status", NOT_ACCEPT_CUS_VALUES)
def test__contractor_not_accepted_worker__fail(
    api_client,
    r_cu,
    get_cu_fi,
    new_contractor_pt_worker_data: Callable,
    target_status,
):
    company = r_cu.company
    target_cu = get_cu_fi(status=target_status, role=CUR.WORKER, company=company)
    data = new_contractor_pt_worker_data(company_user=target_cu, company=company)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data["company_user"][0] == NOT_TA_TARGET_CU_REASON.format(reason=CUS_MUST_BE_ACCEPT)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("target_status", NOT_ACCEPT_CUS_VALUES)
def test__contractor_different_company__fail(
    api_client,
    r_cu,
    get_company_fi,
    get_cu_fi,
    new_contractor_pt_worker_data,
    target_status,
):
    company = get_company_fi()
    target_cu = get_cu_fi(status=target_status, role=CUR.WORKER, company=company)
    data = new_contractor_pt_worker_data(company_user=target_cu, company=company)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == REQUESTING_USER_NOT_BELONG_TO_COMPANY


@pytest.mark.parametrize("requesting_role", ROLES)
@pytest.mark.parametrize("target_status", NOT_ACCEPT_CUS)
def test__appoint_by_client_cu__fail(
    api_client, get_cu_fi, new_contractor_pt_worker_data, target_status, requesting_role
):
    r_cu = get_cu_fi(role=requesting_role)
    target_cu = get_cu_fi(status=target_status.value, role=CUR.WORKER)
    data = new_contractor_pt_worker_data(company_user=target_cu)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_COMPANY}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("target_role", NOT_WORKER_ROLES)
def test__contractor_not_worker_cu__fail(
    api_client,
    r_cu,
    get_cu_fi,
    get_company_fi,
    new_contractor_pt_worker_data,
    target_role,
):
    company = r_cu.company
    target_cu = get_cu_fi(role=target_role, company=company)
    data = new_contractor_pt_worker_data(company_user=target_cu, company=company)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == [TARGET_ROLE_WRONG.format(CUR.WORKER)]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__duplicates__fail(
    api_client,
    r_cu: CompanyUser,
    new_contractor_pt_worker_data,
    get_pt_worker_fi,
):
    duplicate_instance = get_pt_worker_fi(company=r_cu.company)
    data = new_contractor_pt_worker_data(
        company_user=duplicate_instance.company_user, project_territory=duplicate_instance.project_territory
    )
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data[0] == UNIQ_CONSTRAINT_ERR.format(
        company_user=duplicate_instance.company_user.id,
        project_territory=duplicate_instance.project_territory.id,
    )


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__blocked_requesting_user__fail(api_client, r_cu: CompanyUser, new_contractor_pt_worker_data):
    data = new_contractor_pt_worker_data(company=r_cu.company)
    r_cu.user.is_blocked = True
    r_cu.user.save()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": NOT_TA_RCU_REASON.format(reason=NOT_TA_USER_REASON.format(reason=USER_IS_BLOCKED))
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_requesting_user__fail(api_client, r_cu: CompanyUser, new_contractor_pt_worker_data):
    data = new_contractor_pt_worker_data(company=r_cu.company)
    r_cu.user.is_deleted = True
    r_cu.user.save()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.datadata == {
        "detail": NOT_TA_RCU_REASON.format(reason=NOT_TA_USER_REASON.format(reason=USER_IS_DELETED))
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_r_cu__fail(api_client, r_cu: CompanyUser, new_contractor_pt_worker_data):
    data = new_contractor_pt_worker_data(company=r_cu.company)
    r_cu.is_deleted = True
    r_cu.save()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == REQUESTING_USER_NOT_BELONG_TO_COMPANY


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__blocked_target_user__fail(
    api_client,
    r_cu: CompanyUser,
    new_contractor_pt_worker_data,
    get_cu_worker_fi,
):
    target_cu = get_cu_worker_fi(company=r_cu.company)
    data = new_contractor_pt_worker_data(company=r_cu.company, company_user=target_cu)
    target_cu.user.is_blocked = True
    target_cu.user.save()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data["company_user"][0] == NOT_TA_TARGET_CU_REASON.format(
        reason=NOT_TA_USER_REASON.format(reason=USER_IS_BLOCKED)
    )


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_target_user__fail(
    api_client,
    r_cu: CompanyUser,
    new_contractor_pt_worker_data,
    get_cu_worker_fi,
):
    target_cu = get_cu_worker_fi(company=r_cu.company)
    data = new_contractor_pt_worker_data(company=target_cu.company, company_user=target_cu)
    r_cu.user.is_deleted = True
    target_cu.user.save()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data["company_user"][0] == NOT_TA_TARGET_CU_REASON.format(
        reason=NOT_TA_USER_REASON.format(reason=USER_IS_DELETED)
    )


def test__deleted_target_cu__fail(
    api_client,
    cu_owner_fi,
    new_contractor_pt_worker_data,
    get_cu_worker_fi,
):
    r_cu = cu_owner_fi
    target_cu = get_cu_worker_fi(company=r_cu.company)
    data = new_contractor_pt_worker_data(company=r_cu.company, company_user=target_cu)
    target_cu.is_deleted = True
    target_cu.save()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data["company_user"][0] == NOT_TA_TARGET_CU_REASON.format(reason=CU_IS_DELETED)
