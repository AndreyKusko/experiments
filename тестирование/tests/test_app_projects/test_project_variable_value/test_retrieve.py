import functools
from typing import Callable

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated, PermissionDenied

from tests.utils import request_response_get
from accounts.models import USER_IS_BLOCKED, USER_IS_DELETED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from ma_saas.constants.company import CUR, NOT_ACCEPT_CUS
from clients.policies.interface import Policies
from companies.models.company_user import CompanyUser

User = get_user_model()

__get_response = functools.partial(request_response_get, path="/api/v1/project-variable-values/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("processed_report_form_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(api_client, monkeypatch, r_cu, get_project_variable_value_fi):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_project_variable_value_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user)
    response_instance = response.data

    created_instance_id = response_instance.pop("id")
    assert created_instance_id

    response_project_variable = response_instance.pop("project_variable")
    assert response_project_variable == {
        "id": instance.project_variable.id,
        "key": instance.project_variable.key,
        "kind": instance.project_variable.kind,
    }

    assert response_instance.pop("model_id") == instance.model_id
    assert response_instance.pop("model_name") == instance.model_name
    assert response_instance.pop("value") == instance.value
    assert not response_instance


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_worker_fi")])
def test__related_pt_worker__without_policy__without_reservation__fail(
    api_client, mock_policies_false, r_cu, get_pt_worker_fi, get_project_variable_value_fi
):
    ptw = get_pt_worker_fi(company_user=r_cu)

    instance = get_project_variable_value_fi(project=ptw.project_territory.project)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_worker_fi")])
def test__related_pt_worker__without_policy__with_reservation__success(
    api_client,
    mock_policies_false,
    r_cu,
    get_pt_worker_fi,
    get_reservation_fi,
    get_project_variable_value_fi,
):

    ptw = get_pt_worker_fi(company_user=r_cu)
    get_reservation_fi(project_territory_worker=ptw)
    instance = get_project_variable_value_fi(project=ptw.project_territory.project)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__manager_without_permission__fail(
    api_client,
    monkeypatch,
    mock_policies_false,
    r_cu,
    get_project_variable_value_fi,
):
    instance = get_project_variable_value_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_contractor_owner__fail(
    api_client, mock_policies_false, get_cu_fi, get_project_variable_value_fi, status
):
    r_cu = get_cu_fi(status=status.value, role=CUR.OWNER)
    instance = get_project_variable_value_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_cu__fail(api_client, monkeypatch, mock_policies_false, r_cu, get_project_variable_value_fi):

    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    instance = get_project_variable_value_fi(company=r_cu.company)
    r_cu.is_deleted = True
    r_cu.save()
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


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
    api_client, monkeypatch, r_cu, get_project_fi, has_object_policy, is_user, field, err_text
):
    __get_target_policies_return = [r_cu.company.id] if has_object_policy else []
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: __get_target_policies_return)

    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    instance = get_project_fi(company=r_cu.company)

    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()
        response = __get_response(api_client, instance.id, r_cu.user, status_codes=PermissionDenied)
        assert response.data == {"detail": err_text}
    else:
        setattr(r_cu, field, True)
        r_cu.save()
        response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
        assert response.data == {"detail": NotFound.default_detail}
