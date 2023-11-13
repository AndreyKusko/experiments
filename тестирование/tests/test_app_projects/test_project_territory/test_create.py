import functools
from copy import deepcopy

import pytest
from django.forms import model_to_dict
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_create
from accounts.models import USER_IS_BLOCKED, USER_IS_DELETED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from projects.models.project import PROJECT_IS_ARCHIVED, Project
from ma_saas.constants.system import Callable
from ma_saas.constants.company import NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from ma_saas.constants.project import ProjectStatus
from projects.models.territory import Territory
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_MUST_BE_ACCEPT, CompanyUser
from projects.models.project_territory import UNIQ_CONSTRAINT_ERR, ProjectTerritory

User = get_user_model()

__get_response = functools.partial(request_response_create, path="/api/v1/project-territory/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, {}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, new_project_territory_data):
    data = new_project_territory_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user)
    assert all(response.data[key] == value for key, value in data.items())
    new_instance = ProjectTerritory.objects.get(id=response.data["id"])
    new_instance_dict = model_to_dict(new_instance)
    assert all(new_instance_dict[key] == value for key, value in data.items())
    assert response.data["territory_title"]
    assert response.data["project_title"]
    territory = Territory.objects.get(id=data["territory"])
    assert response.data["territory_title"] == territory.title == new_instance.territory.title
    project = Project.objects.get(id=data["territory"])
    assert response.data["project_title"] == project.title == new_instance.project.title


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_ta_company_owner__fail(api_client, get_cu_owner_fi, new_project_territory_data, status):
    r_cu = get_cu_owner_fi(status=status.value)
    data = new_project_territory_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__without_policy__fail(
    api_client,
    monkeypatch,
    get_cu_fi,
    new_project_territory_data: Callable,
    role,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    r_cu = get_cu_fi(role=role)
    data = new_project_territory_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    # assert response.data == {"detail": COMPANY_OWNER_ONLY_ALLOWED}
    assert response.data == {"detail": PermissionDenied.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("is_user", "field", "err_text"),
    (
        (True, "is_blocked", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_BLOCKED)),
        (True, "is_deleted", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_DELETED)),
        (False, "is_deleted", REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY),
    ),
)
@pytest.mark.parametrize("has_object_policy", [True, False])
def test__not_ta__cu__fail(
    api_client, monkeypatch, r_cu, new_project_territory_data, has_object_policy, is_user, field, err_text
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()
    else:
        setattr(r_cu, field, True)
        r_cu.save()
    data = new_project_territory_data(company=r_cu.company)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": err_text}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("status", (ProjectStatus.SETUP.value, ProjectStatus.ACTIVE.value))
def test__project_status_setup_or_active__success(
    api_client,
    monkeypatch,
    r_cu,
    get_project_fi,
    new_project_territory_data,
    status,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    project = get_project_fi(company=r_cu.company, status=status)
    data = new_project_territory_data(company=r_cu.company, project=project)
    assert __get_response(api_client, data=data, user=r_cu.user)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__duplicates__fail(
    api_client, r_cu: CompanyUser, get_project_fi, new_project_territory_data: Callable
):
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.ARCHIVED.value)
    data = new_project_territory_data(company=r_cu.company, project=project)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PROJECT_IS_ARCHIVED}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__duplicates__fail(
    api_client,
    monkeypatch,
    r_cu: CompanyUser,
    get_project_territory_fi: Callable,
    new_project_territory_data: Callable,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])

    data = new_project_territory_data(company=r_cu.company)
    duplicate_data = deepcopy(data)
    duplicate_data["territory"] = Territory.objects.get(id=data["territory"])
    duplicate_data["project"] = Project.objects.get(id=data["project"])
    duplicated_instance = get_project_territory_fi(**duplicate_data)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == [
        UNIQ_CONSTRAINT_ERR.format(
            project=duplicated_instance.project.id, territory=duplicated_instance.territory.id
        )
    ]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, monkeypatch, r_cu, new_project_territory_data):

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    data = new_project_territory_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user)
    assert all(response.data[key] == value for key, value in data.items())
    new_instance = model_to_dict(ProjectTerritory.objects.get(id=response.data["id"]))
    assert all(new_instance[key] == value for key, value in data.items())
