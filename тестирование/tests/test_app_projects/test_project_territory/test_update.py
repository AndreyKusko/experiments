import functools

import pytest
from django.forms import model_to_dict
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_update
from projects.models.project import PROJECT_IS_ARCHIVED
from ma_saas.constants.company import ROLES, NOT_ACCEPT_CUS_VALUES
from ma_saas.constants.project import ProjectStatus
from companies.models.company_user import CompanyUser
from projects.models.project_territory import ProjectTerritory

User = get_user_model()

__get_response = functools.partial(request_response_update, path="/api/v1/project-territory/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("project_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, {}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(
    api_client,
    mock_policy_true,
    r_cu,
    get_project_territory_fi,
    new_project_territory_data,
):
    mock_policy_true(r_cu.company)
    instance = get_project_territory_fi(company=r_cu.company)
    data = new_project_territory_data(company=r_cu.company)
    del data["project"]
    del data["territory"]
    response = __get_response(api_client, data=data, instance_id=instance.id, user=r_cu.user)
    updated_instance_data = model_to_dict(ProjectTerritory.objects.get(id=instance.id))

    assert response.data["territory_title"]
    assert response.data["project_title"]
    assert response.data.pop("territory_title") == instance.territory.title
    assert response.data.pop("project_title") == instance.project.title

    assert all(updated_instance_data[key] == response.data[key] == value for key, value in data.items())


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("is_active", (True, False))
def test__any_active_status__success(
    api_client,
    mock_policy_true,
    r_cu: CompanyUser,
    get_project_territory_fi,
    new_project_territory_data,
    is_active: bool,
):
    mock_policy_true(r_cu.company)
    instance = get_project_territory_fi(company=r_cu.company, is_active=is_active)
    data = new_project_territory_data(company=r_cu.company)
    del data["project"]
    del data["territory"]
    assert __get_response(api_client, instance.id, data, user=r_cu.user)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__project_archived__fail(
    api_client,
    mock_policy_true,
    r_cu,
    get_project_territory_fi,
    new_project_territory_data,
    get_project_fi,
):
    mock_policy_true(r_cu.company)
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.ARCHIVED.value)
    instance = get_project_territory_fi(company=r_cu.company, project=project)
    data = new_project_territory_data(company=r_cu.company)
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PROJECT_IS_ARCHIVED}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("status", (ProjectStatus.SETUP.value, ProjectStatus.ACTIVE.value))
def test__project_active_or_setup__success(
    api_client,
    mock_policy_true,
    r_cu,
    get_project_territory_fi,
    new_project_territory_data,
    get_project_fi,
    status,
):
    mock_policy_true(r_cu.company)
    project = get_project_fi(company=r_cu.company, status=status)
    instance = get_project_territory_fi(company=r_cu.company, project=project)
    data = new_project_territory_data(company=r_cu.company)
    del data["project"]
    del data["territory"]
    assert __get_response(api_client, instance.id, data, r_cu.user)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_territory__fail(
    api_client,
    mock_policy_true,
    r_cu,
    get_project_territory_fi,
    new_project_territory_data,
    get_project_fi,
):
    mock_policy_true(r_cu.company)

    instance = get_project_territory_fi(company=r_cu.company)
    data = new_project_territory_data(company=r_cu.company)
    r_cu.user.is_deleted = True
    instance.territory.save()
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    assert response.data == ["Нельзя менять проект у проекто-территории."]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_project__fail(
    api_client,
    mock_policy_true,
    r_cu: CompanyUser,
    get_project_territory_fi,
    new_project_territory_data,
    get_project_fi,
):
    mock_policy_true(r_cu.company)
    instance = get_project_territory_fi(company=r_cu.company)
    data = new_project_territory_data(company=r_cu.company)
    instance.project.is_deleted = True
    instance.project.save()
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=NotFound)
    # assert response.data == {
    #     "detail": NOT_TA_PT_REASON.format(reason=NOT_TA_PROJECT_REASON.format(reason=PROJECT_IS_DELETED))
    # }


# @pytest.mark.parametrize("role", NOT_OWNER_ROLES)
# def test__not_owner__fail(api_client, get_cu_fi, get_project_territory_fi, role):
#     r_cu = get_cu_fi(role=role)
#     instance = get_project_territory_fi(company=r_cu.company)
#     response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=PermissionDenied)
#     assert response.data == {"detail": COMPANY_OWNER_ONLY_ALLOWED}


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", NOT_ACCEPT_CUS_VALUES)
def test__not_accepted_user__fail(
    api_client, mock_policy_true, get_cu_fi, get_project_territory_fi, status, role
):
    r_cu = get_cu_fi(status=status, role=role)
    mock_policy_true(r_cu.company)
    instance = get_project_territory_fi(company=r_cu.company)
    # assert __get_response(api_client, instance.id, {}, r_cu.user, status_codes=NotFound)
    assert __get_response(api_client, instance.id, {}, r_cu.user, status_codes=PermissionDenied)


# @pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
# def test__restricted_field__not_updating(
#     api_client,mock_policy_true,
#     r_cu: CompanyUser,
#     get_project_territory_fi,
#     get_territory_fi,
#     get_project_fi,
# ):
#     mock_policy_true(r_cu.company)
#     instance = get_project_territory_fi(company=r_cu.company)
#     data = {"territory": get_territory_fi().id, "project": get_project_fi().id}
#     response = __get_response(api_client, instance.id, data, user=r_cu.user)
#     updated_instance = ProjectTerritory.objects.get(id=instance.id)
#     assert response.data["territory"] == instance.territory.id == updated_instance.territory.id
#     assert response.data["project"] == instance.project.id == updated_instance.project.id
