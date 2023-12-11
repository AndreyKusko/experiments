import functools

import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated, PermissionDenied

from tests.utils import request_response_delete
from accounts.models import USER_IS_BLOCKED, USER_IS_DELETED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from ma_saas.constants.system import Callable
from ma_saas.constants.company import CUR, CUS, ROLES
from clients.policies.interface import Policies
from companies.models.company_user import CompanyUser
from projects.models.contractor_project_territory_worker import ContractorProjectTerritoryWorker

User = get_user_model()

__get_response = functools.partial(
    request_response_delete, path="/api/v1/contractor-project-territory-workers/"
)


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codes={NotAuthenticated.status_code})
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, get_pt_worker_fi):
    instance = get_pt_worker_fi(company=r_cu.company)
    assert __get_response(api_client, instance_id=instance.id, user=r_cu.user)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__related_manager__success(api_client, get_cu_fi, r_cu, get_pt_worker_fi, get_project_territory_fi):
    pt = get_project_territory_fi(company=r_cu.company)
    instance = get_pt_worker_fi(project_territory=pt, company=r_cu.company)
    assert __get_response(api_client, instance_id=instance.id, user=r_cu.user)


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", CUS)
def test__different_company_user__fail(api_client, get_cu_fi, get_pt_worker_fi, role, status):
    r_cu = get_cu_fi(status=status.value, role=role)
    instance = get_pt_worker_fi()
    assert __get_response(api_client, instance_id=instance.id, user=r_cu.user, status_codes=NotFound)


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", CUS)
def test__user_without_pt__fail(api_client, get_cu_fi, get_pt_worker_fi, role, status):
    if status == CUS.ACCEPT.value and role == CUR.OWNER:
        return
    r_cu = get_cu_fi(status=status.value, role=role)
    instance = get_pt_worker_fi(company=r_cu.company)

    assert __get_response(api_client, instance_id=instance.id, user=r_cu.user, status_codes=NotFound)


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
    api_client, monkeypatch, r_cu, get_pt_worker_fi, has_object_policy, is_user, field, err_text
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()
    else:
        setattr(r_cu, field, True)
        r_cu.save()
    instance = get_pt_worker_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=PermissionDenied)
    assert response.data == err_text


def test__model_is_fake_delete_allow_create_new_model(api_client, get_pt_worker_fi):
    instance = get_pt_worker_fi()
    fields = {f: getattr(instance, f) for f in ["project_territory", "company_user"]}
    instance.is_deleted = True
    instance.save()
    assert ContractorProjectTerritoryWorker.objects.filter(**fields, is_deleted=True).count() == 1
    assert get_pt_worker_fi(**fields)
    assert ContractorProjectTerritoryWorker.objects.existing().filter(**fields).count() == 1
