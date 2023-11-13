import functools
from copy import deepcopy

import pytest
from django.forms import model_to_dict
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated, PermissionDenied

from tests.utils import request_response_update
from accounts.models.users import (
    USER_IS_BLOCKED,
    USER_IS_DELETED,
    USER_EMAIL_NOT_VERIFIED,
    USER_PHONE_NOT_VERIFIED,
    NOT_TA_REQUESTING_USER_REASON,
)
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from ma_saas.constants.system import Callable
from ma_saas.constants.company import CUR, ROLES, NOT_ACCEPT_CUS, NOT_OWNER_ROLES, NOT_ACCEPT_CUS_VALUES
from projects.models.territory import Territory
from clients.policies.interface import Policies
from companies.models.company_user import COMPANY_OWNER_ONLY_ALLOWED, CompanyUser
from projects.serializers.territory import TerritorySerializer

User = get_user_model()


__get_response = functools.partial(request_response_update, path="/api/v1/territories/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("project_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, {}, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_company_owner__fail(api_client, get_cu_fi, get_territory_fi: Callable, role):
    company_user = get_cu_fi(role=role)
    project = get_territory_fi(company=company_user.company)
    response = __get_response(
        api_client,
        data={},
        instance_id=project.id,
        user=company_user.user,
        status_codes=status_code.HTTP_403_FORBIDDEN,
    )
    assert response.data["detail"] == COMPANY_OWNER_ONLY_ALLOWED


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_user__fail(api_client, get_cu_fi, get_territory_fi: Callable, status, role):
    company_user = get_cu_fi(status=status.value, role=role)
    instance = get_territory_fi(company=company_user.company)
    response = __get_response(
        api_client, data={}, instance_id=instance.id, user=company_user.user, status_codes=NotFound
    )
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS_VALUES)
def test__not_accepted_owner__fail(
    api_client,
    get_cu_fi,
    get_territory_fi: Callable,
    new_territory_data: Callable,
    status,
):
    company_user = get_cu_fi(status=status, role=CUR.OWNER)
    instance = get_territory_fi(company=company_user.company)
    data = new_territory_data(company=instance.company)
    del data["inviting_company"]
    response = __get_response(api_client, instance.id, data, user=company_user.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__fail(api_client, get_cu_fi, get_territory_fi, new_territory_data, role):
    company_user = get_cu_fi(role=role)
    instance = get_territory_fi(company=company_user.company)
    data = new_territory_data(company=instance.company)
    del data["inviting_company"]
    response = __get_response(api_client, instance.id, data, company_user.user, status_codes=PermissionDenied)
    assert response.data["detail"] == COMPANY_OWNER_ONLY_ALLOWED


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(
    api_client, mock_policies_false, r_cu, get_territory_fi, new_territory_data
):
    instance = get_territory_fi(company=r_cu.company)
    data = new_territory_data(company=instance.company)
    del data["inviting_company"]
    response = __get_response(
        api_client,
        instance.id,
        data,
        user=r_cu.user,
    )
    assert all(response.data[key] == value for key, value in data.items())
    new_territory = model_to_dict(Territory.objects.get(id=instance.id))
    assert all(new_territory[key] == value for key, value in data.items())


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__restricted_field_do_not_updating(
    api_client,
    r_cu,
    get_territory_fi: Callable,
    get_company_fi,
    new_project_data: Callable,
):
    instance = get_territory_fi(company=r_cu.company)
    instance_dict = TerritorySerializer(instance=instance).data

    new_data = deepcopy(instance_dict)
    new_data["inviting_company"] = get_company_fi().id

    response = __get_response(api_client, instance.id, new_data, r_cu.user)
    assert all(value == instance_dict[key] for key, value in response.data.items())


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
    api_client,
    monkeypatch,
    r_cu,
    get_territory_fi,
    new_territory_data,
    has_object_policy,
    is_user,
    field,
    err_text,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()
    else:
        setattr(r_cu, field, True)
        r_cu.save()
    instance = get_territory_fi(company=r_cu.company)
    data = new_territory_data(company=instance.company)

    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == err_text


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__not_email_verified__fail(api_client, r_cu, get_territory_fi: Callable):
    instance = get_territory_fi(company=r_cu.company)
    r_cu.user.is_verified_email = False
    r_cu.user.save()
    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=PermissionDenied)
    assert response.data["detail"] == NOT_TA_REQUESTING_USER_REASON.format(reason=USER_EMAIL_NOT_VERIFIED)


def test__not_phone_verified__fail(api_client, get_cu_worker_fi, get_territory_fi: Callable):
    r_cu = get_cu_worker_fi()
    instance = get_territory_fi(company=r_cu.company)
    r_cu.user.is_verified_phone = False
    r_cu.user.save()
    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=PermissionDenied)
    assert response.data["detail"] == NOT_TA_REQUESTING_USER_REASON.format(reason=USER_PHONE_NOT_VERIFIED)
