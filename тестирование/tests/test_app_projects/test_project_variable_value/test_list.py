import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from tests.utils import request_response_list
from accounts.models import USER_IS_BLOCKED, USER_IS_DELETED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from ma_saas.constants.company import CUR, CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from clients.policies.interface import Policies
from companies.models.company_user import CompanyUser

User = get_user_model()

__get_response = functools.partial(request_response_list, path="/api/v1/project-variable-values/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


def test__user_without_companies__fail(api_client, mock_policies_false, user_fi: User):

    response = __get_response(api_client, user_fi)
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("qty", (1, 3))
def test__accepted_owner__success(api_client, mock_policies_false, get_project_variable_value_fi, r_cu, qty):
    [get_project_variable_value_fi(company=r_cu.company) for _ in range(qty)]
    response = __get_response(api_client, r_cu.user)
    assert len(response.data) == qty


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("qty", (1, 3))
def test__response_data(api_client, mock_policies_false, get_project_variable_value_fi, r_cu, qty):

    instances = [get_project_variable_value_fi(company=r_cu.company) for _ in range(qty)]
    response = __get_response(api_client, r_cu.user)
    for index, response_instance in enumerate(response.data):
        assert response_instance.pop("id")
        assert response_instance.pop("project_variable") == {
            "id": instances[index].project_variable.id,
            "key": instances[index].project_variable.key,
            "kind": instances[index].project_variable.kind,
        }
        assert response_instance.pop("model_id") == instances[index].model_id
        assert response_instance.pop("model_name") == instances[index].model_name
        assert response_instance.pop("value") == instances[index].value
        assert not response_instance


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
@pytest.mark.parametrize("qty", (3,))
def test__not_accepted_owner__fail(
    api_client, monkeypatch, get_project_variable_value_fi, get_cu_fi, status, qty
):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    instances = [get_project_variable_value_fi(company=r_cu.company) for _ in range(qty)]
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [i.id for i in instances])
    response = __get_response(api_client, r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
@pytest.mark.parametrize("qty", (3,))
def test__not_owner__without_policies__fail(
    api_client, mock_policies_false, get_project_variable_value_fi, get_cu_fi, role, qty
):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    [get_project_variable_value_fi(company=r_cu.company) for _ in range(qty)]
    response = __get_response(api_client, r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
@pytest.mark.parametrize("qty", (3,))
def test__not_owner__with_policies__success(
    api_client, monkeypatch, get_project_variable_value_fi, get_cu_fi, role, qty
):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    [get_project_variable_value_fi(company=r_cu.company) for _ in range(qty)]

    response = __get_response(api_client, r_cu.user)
    assert len(response.data) == qty


@pytest.mark.xfail
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
    api_client, monkeypatch, r_cu, get_project_variable_value_fi, has_object_policy, is_user, field, err_text
):
    get_project_variable_value_fi(company=r_cu.company)

    __get_target_policies_return = [r_cu.company.id] if has_object_policy else []
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: __get_target_policies_return)
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()

        response = __get_response(api_client, r_cu.user, status_codes=PermissionDenied)
        assert response.data == {"detail": err_text}

    else:
        setattr(r_cu, field, True)
        r_cu.save()

        response = __get_response(api_client, r_cu.user)
        assert response.data == []
