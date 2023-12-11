import json
import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated

from tests.utils import request_response_list
from ma_saas.constants.company import CUR, CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from ma_saas.constants.company import CompanyPartnershipStatus as CPS
from clients.policies.interface import Policies

User = get_user_model()

__get_response = functools.partial(request_response_list, path="/api/v1/company-partnerships/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


def test__user_without_companies_got_nothing(api_client, monkeypatch, user_fi: User):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    response = __get_response(api_client, user=user_fi)
    assert not response.data, f"response.data = {response.data}"


def test__owners__success(monkeypatch, api_client, get_cu_fi, get_company_partnership_fi):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    qty = 3
    r_cu1 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    instances1 = [get_company_partnership_fi(inviting_company_user=r_cu1) for _ in range(qty)]
    instances1.reverse()
    response1 = __get_response(api_client, user=r_cu1.user)

    assert len(response1.data) == qty, response1.data
    for index, instance1 in enumerate(instances1):
        assert response1.data[index]["id"] == instance1.id

    r_cu2 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    instances2 = [get_company_partnership_fi(invited_company=r_cu2.company) for _ in range(qty)]
    instances2.reverse()
    response2 = __get_response(api_client, user=r_cu2.user)

    assert len(response1.data) == qty, response1.data
    for index, instance2 in enumerate(instances2):
        assert response2.data[index]["id"] == instance2.id


def test__response_data(monkeypatch, api_client, get_cu_fi, get_company_partnership_fi, get_company_fi):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    qty = 3
    accept = CPS.ACCEPT.value

    r_cu0 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    instances0 = [
        get_company_partnership_fi(
            inviting_company_user=r_cu0, inviting_company_status=accept, invited_company_status=accept
        )
        for _ in range(qty)
    ]
    instances0.reverse()
    response0 = __get_response(api_client, user=r_cu0.user)
    assert len(response0.data) == qty, response0.data
    for index, instance0 in enumerate(instances0):
        response_instance = response0.data[index]

        assert response_instance["id"] == instance0.id
        assert response_instance["invited_company_user_email"] == instance0.invited_company_user_email

        assert len(response_instance["invited_company"]) == 0

        assert len(response_instance["inviting_company"]) == 4
        assert response_instance["inviting_company"]["id"] == instance0.inviting_company.id
        assert response_instance["inviting_company"]["title"] == instance0.inviting_company.title
        assert response_instance["inviting_company"]["subdomain"] == instance0.inviting_company.subdomain
        assert response_instance["inviting_company"]["logo"] == instance0.inviting_company.logo

        assert len(response_instance["inviting_company_user"]) == 1
        assert response_instance["inviting_company_user"]["id"] == r_cu0.id
        assert response_instance["invited_company_status"] == accept
        assert response_instance["inviting_company_status"] == accept
        assert response_instance["invited_project_partnership_qty_map"]
        assert response_instance["updated_at"]
        assert response_instance["created_at"]

    r_cu1 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    instances1 = [
        get_company_partnership_fi(
            inviting_company_user=r_cu1,
            inviting_company_status=accept,
            invited_company_status=accept,
            invited_company=get_company_fi(),
        )
        for _ in range(qty)
    ]
    instances1.reverse()
    response1 = __get_response(api_client, user=r_cu1.user)
    assert len(response1.data) == qty, response1.data
    for index, instance1 in enumerate(instances1):
        response_instance = response1.data[index]

        assert response_instance["id"] == instance1.id
        assert response_instance["invited_company_user_email"] == instance1.invited_company_user_email

        assert len(response_instance["invited_company"]) == 4
        assert response_instance["invited_company"]["id"] == instance1.invited_company.id
        assert response_instance["invited_company"]["title"] == instance1.invited_company.title
        assert response_instance["invited_company"]["subdomain"] == instance1.invited_company.subdomain
        assert response_instance["invited_company"]["logo"] == instance1.invited_company.logo

        assert len(response_instance["inviting_company"]) == 4
        assert response_instance["inviting_company"]["id"] == r_cu1.company.id
        assert response_instance["inviting_company"]["title"] == r_cu1.company.title
        assert response_instance["inviting_company"]["subdomain"] == r_cu1.company.subdomain
        assert response_instance["inviting_company"]["logo"] == r_cu1.company.logo

        assert len(response_instance["inviting_company_user"]) == 1
        assert response_instance["inviting_company_user"]["id"] == r_cu1.id
        assert response_instance["invited_company_status"] == accept
        assert response_instance["inviting_company_status"] == accept
        assert response_instance["invited_project_partnership_qty_map"]
        assert response_instance["updated_at"]
        assert response_instance["created_at"]

    r_cu2 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)

    instances2 = [
        get_company_partnership_fi(
            invited_company=r_cu2.company, inviting_company_status=accept, invited_company_status=accept
        )
        for _ in range(qty)
    ]
    instances2.reverse()
    response2 = __get_response(api_client, user=r_cu2.user)

    assert len(response1.data) == qty, response1.data
    for index, instance2 in enumerate(instances2):
        response_instance = response2.data[index]
        assert response_instance["id"] == instance2.id
        assert response_instance["invited_company_user_email"] == instance2.invited_company_user_email

        assert len(response_instance["invited_company"]) == 4
        assert response_instance["invited_company"]["id"] == r_cu2.company.id
        assert response_instance["invited_company"]["title"] == r_cu2.company.title
        assert response_instance["invited_company"]["subdomain"] == r_cu2.company.subdomain
        assert response_instance["invited_company"]["logo"] == r_cu2.company.logo

        assert len(response_instance["inviting_company"]) == 4
        assert response_instance["inviting_company"]["id"] == instance2.inviting_company.id
        assert response_instance["inviting_company"]["title"] == instance2.inviting_company.title
        assert response_instance["inviting_company"]["subdomain"] == instance2.inviting_company.subdomain
        assert response_instance["inviting_company"]["logo"] == instance2.inviting_company.logo

        assert len(response_instance["inviting_company_user"]) == 1
        assert response_instance["inviting_company_user"]["id"] == instance2.inviting_company_user.id
        assert response_instance["invited_company_status"] == accept
        assert response_instance["inviting_company_status"] == accept
        assert response_instance["invited_project_partnership_qty_map"]
        assert response_instance["updated_at"]
        assert response_instance["created_at"]


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__fail(monkeypatch, api_client, get_cu_fi, get_company_partnership_fi, status):

    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    qty = 3

    r_cu1 = get_cu_fi(role=CUR.OWNER, status=status.value)
    instances1 = [get_company_partnership_fi(inviting_company_user=r_cu1) for _ in range(qty)]
    instances1.reverse()
    response1 = __get_response(api_client, user=r_cu1.user)
    assert len(response1.data) == 0

    r_cu2 = get_cu_fi(role=CUR.OWNER, status=status)
    instances2 = [get_company_partnership_fi(invited_company=r_cu2.company) for _ in range(qty)]
    instances2.reverse()
    response2 = __get_response(api_client, user=r_cu2.user)
    assert len(response2.data) == 0


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__accepted_not_owner__no_policies__fail(
    monkeypatch, api_client, get_cu_fi, get_company_partnership_fi, role
):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    qty = 3

    r_cu1 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    instances1 = [get_company_partnership_fi(inviting_company_user=r_cu1) for _ in range(qty)]
    instances1.reverse()
    response1 = __get_response(api_client, user=r_cu1.user)
    assert len(response1.data) == 0

    r_cu2 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    instances2 = [get_company_partnership_fi(invited_company=r_cu2.company) for _ in range(qty)]
    instances2.reverse()
    response2 = __get_response(api_client, user=r_cu2.user)
    assert len(response2.data) == 0
