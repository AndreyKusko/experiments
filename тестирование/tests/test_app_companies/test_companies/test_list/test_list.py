import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated

from tests.utils import request_response_list
from ma_saas.constants.company import ROLES, NOT_ACCEPT_OR_INVITE_CUS, ACCEPT_OR_INVITE_CUS_VALUES
from clients.policies.interface import Policies

User = get_user_model()


__get_response = functools.partial(request_response_list, path="/api/v1/companies/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


def test__user_without_companies_got_nothing(api_client, monkeypatch, user_fi: User):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    response = __get_response(api_client, user=user_fi)
    assert not response.data


def test__response_data(api_client, monkeypatch, user_fi, get_cu_fi):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    qty = 3
    cus = [get_cu_fi(user=user_fi) for _ in range(qty)]
    cus.reverse()
    response = __get_response(api_client, user=user_fi)

    assert len(response.data) == qty, response.data
    for index, response_instance in enumerate(response.data):

        assert response_instance.pop("id") == cus[index].company.id
        assert response_instance.pop("title") == cus[index].company.title
        assert response_instance.pop("subdomain") == cus[index].company.subdomain
        assert str(response_instance.pop("logo")) == cus[index].company.logo
        assert response_instance.pop("support_email") == cus[index].company.support_email
        assert (
            response_instance.pop("transactions_list_scheme") == cus[index].company.transactions_list_scheme
        )
        assert response_instance.pop("created_at")
        assert response_instance.pop("updated_at")
        assert not response_instance, f"response_instance = {response_instance}"


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", ACCEPT_OR_INVITE_CUS_VALUES)
@pytest.mark.parametrize("qty", (2,))
def test__cu_with_status_accept_or_invite__success(api_client, user_fi: User, get_cu_fi, role, status, qty):
    cus = [get_cu_fi(user=user_fi, role=role, status=status) for _ in range(qty)]
    cus.reverse()
    response = __get_response(api_client=api_client, user=user_fi)
    assert len(response.data) == qty
    for i in range(qty):
        assert response.data[i]["id"] == cus[i].company.id


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", NOT_ACCEPT_OR_INVITE_CUS)
@pytest.mark.parametrize("qty", (2,))
def test__cu_with_not_status_accept_or_not_invite__access(
    api_client, user_fi: User, get_cu_fi, role, status, qty
):
    cus = [get_cu_fi(user=user_fi, role=role, status=status) for _ in range(qty)]
    cus.reverse()
    response = __get_response(api_client, user=user_fi)
    assert len(response.data) == qty
