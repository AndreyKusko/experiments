import functools

import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated, PermissionDenied

from tests.utils import request_response_delete
from accounts.models import USER_IS_BLOCKED, USER_IS_DELETED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.constants.system import Callable
from ma_saas.constants.company import (
    CUR,
    CUS,
    ROLES,
    NOT_ACCEPT_CUS,
    NOT_OWNER_ROLES,
    NOT_ACCEPT_CUS_VALUES,
    NOT_OWNER_AND_NOT_WORKER_ROLES,
)
from companies.models.company_user import COMPANY_OWNER_ONLY_ALLOWED, CompanyUser
from projects.models.project_territory import ProjectTerritory

User = get_user_model()


__get_response = functools.partial(request_response_delete, path="/api/v1/project-territory/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("project_territory_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codes={NotAuthenticated.status_code})
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, get_project_territory_fi):
    instance = get_project_territory_fi(company=r_cu.company)
    assert __get_response(api_client, instance.id, user=r_cu.user)


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__fail(api_client, get_cu_fi, get_project_territory_fi, status):
    r_cu = get_cu_fi(status=status, role=CUR.OWNER)
    instance = get_project_territory_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_AND_NOT_WORKER_ROLES)
@pytest.mark.parametrize("status", NOT_ACCEPT_CUS_VALUES)
def test__not_owner_and_not_accepted__fail(api_client, get_cu_fi, get_project_territory_fi, role, status):
    r_cu = get_cu_fi(status=status, role=role)
    instance = get_project_territory_fi(company=r_cu.company)

    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == str(NotFound.default_detail)


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__fail(
    api_client,
    get_cu_fi,
    get_project_territory_fi: Callable,
    role,
):
    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)
    instance = get_project_territory_fi(company=r_cu.company)

    response = __get_response(api_client, instance.id, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": COMPANY_OWNER_ONLY_ALLOWED}


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", CUS)
def test__different_company_user__fail(
    api_client,
    get_cu_fi,
    get_project_territory_fi: Callable,
    role,
    status,
):
    r_cu = get_cu_fi(status=status.value, role=role)
    instance = get_project_territory_fi()
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("field", "err_text"),
    (
        ("is_blocked", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_BLOCKED)),
        ("is_deleted", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_DELETED)),
    ),
)
@pytest.mark.parametrize("has_object_policy", [True, False])
def test__not_ta__cu__fail(
    api_client, monkeypatch, r_cu, get_project_territory_fi, has_object_policy, field, err_text
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    setattr(r_cu.user, field, True)
    r_cu.user.save()

    instance = get_project_territory_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=PermissionDenied)
    assert response.data == err_text


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_cu__success(api_client, r_cu, get_project_territory_fi: Callable):
    instance = get_project_territory_fi(company=r_cu.company)
    r_cu.is_deleted = True
    r_cu.save()
    response = __get_response(
        api_client,
        instance_id=instance.id,
        user=r_cu.user,
        status_codes={status_code.HTTP_404_NOT_FOUND},
    )
    assert response.data["detail"] == NotFound.default_detail


def test__model_is_fake_delete_allow_create_new_model(api_client, get_project_territory_fi: Callable):
    instance = get_project_territory_fi()
    fields = {f: getattr(instance, f) for f in ["project", "territory"]}
    instance.is_deleted = True
    instance.save()
    assert ProjectTerritory.objects.filter(**fields, is_deleted=True).count() == 1
    assert get_project_territory_fi(**fields)
    assert ProjectTerritory.objects.existing().filter(**fields).count() == 1
