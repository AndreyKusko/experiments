import json
import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated

from tests.utils import request_response_get
from ma_saas.constants.company import (
    CUR,
    CUS,
    ROLES,
    NOT_ACCEPT_CUS,
    NOT_OWNER_ROLES,
    CPS_ING_AND_ED_COMPANY_STATUS,
)
from ma_saas.constants.company import CompanyPartnershipStatus as CPS
from clients.policies.interface import Policies

User = get_user_model()


__get_response = functools.partial(request_response_get, path="/api/v1/company-partnerships/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("company_partnership_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__without_policies__fail(
    api_client, monkeypatch, status, get_cu_fi, get_company_partnership_fi
):
    r_cu1 = get_cu_fi(role=CUR.OWNER, status=status.value)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance1 = get_company_partnership_fi(inviting_company_user=r_cu1, **CPS_ING_AND_ED_COMPANY_STATUS)
    response1 = __get_response(api_client, instance1.id, user=r_cu1.user, status_codes=NotFound)
    assert response1.data["detail"] == NotFound.default_detail

    r_cu2 = get_cu_fi(role=CUR.OWNER, status=status)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance2 = get_company_partnership_fi(invited_company=r_cu2.company, **CPS_ING_AND_ED_COMPANY_STATUS)
    response2 = __get_response(api_client, instance2.id, user=r_cu2.user, status_codes=NotFound)
    assert response2.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize(
    "cps_data",
    [
        {"inviting_company_status": CPS.ACCEPT.value, "invited_company_status": CPS.INVITE.value},
        {"inviting_company_status": CPS.ACCEPT.value, "invited_company_status": CPS.ACCEPT.value},
        {"inviting_company_status": CPS.ACCEPT.value, "invited_company_status": CPS.CANCEL.value},
        {"inviting_company_status": CPS.CANCEL.value, "invited_company_status": CPS.INVITE.value},
        {"inviting_company_status": CPS.CANCEL.value, "invited_company_status": CPS.ACCEPT.value},
        {"inviting_company_status": CPS.CANCEL.value, "invited_company_status": CPS.CANCEL.value},
    ],
)
def test__accepted_owners__success(
    api_client, mock_policies_false, get_cu_fi, cps_data, get_company_partnership_fi
):

    r_cu1 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)

    instance1 = get_company_partnership_fi(inviting_company_user=r_cu1, **cps_data)
    response1 = __get_response(api_client, instance1.id, user=r_cu1.user)
    assert response1.data["id"] == instance1.id
    assert response1.data["inviting_company_status"] == cps_data["inviting_company_status"]
    assert response1.data["invited_company_status"] == cps_data["invited_company_status"]

    r_cu2 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)

    instance2 = get_company_partnership_fi(invited_company=r_cu2.company, **cps_data)
    response2 = __get_response(api_client, instance2.id, user=r_cu2.user)
    assert response2.data["id"] == instance2.id
    assert response2.data["inviting_company_status"] == cps_data["inviting_company_status"]
    assert response2.data["invited_company_status"] == cps_data["invited_company_status"]


def test__response_data(
    api_client, mock_policies_false, get_cu_fi, get_company_partnership_fi, get_company_fi
):
    r_cu0 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    instance0 = get_company_partnership_fi(inviting_company_user=r_cu0, **CPS_ING_AND_ED_COMPANY_STATUS)
    response0 = __get_response(api_client, instance0.id, user=r_cu0.user)
    assert len(response0.data) == 10
    assert response0.data["id"] == instance0.id
    assert response0.data["invited_company_user_email"] == instance0.invited_company_user_email

    assert len(response0.data["invited_company"]) == 0

    assert len(response0.data["inviting_company"]) == 4
    assert response0.data["inviting_company"]["id"] == r_cu0.company.id
    assert response0.data["inviting_company"]["title"] == r_cu0.company.title
    assert response0.data["inviting_company"]["subdomain"] == r_cu0.company.subdomain
    assert response0.data["inviting_company"]["logo"] == r_cu0.company.logo

    assert len(response0.data["inviting_company_user"]) == 1
    assert response0.data["inviting_company_user"]["id"] == r_cu0.id
    assert response0.data["invited_company_status"] == CPS.ACCEPT.value
    assert response0.data["inviting_company_status"] == CPS.ACCEPT.value
    assert response0.data["invited_project_partnership_qty_map"]
    assert response0.data["updated_at"]
    assert response0.data["created_at"]

    r_cu1 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    instance1 = get_company_partnership_fi(
        inviting_company_user=r_cu1, **CPS_ING_AND_ED_COMPANY_STATUS, invited_company=get_company_fi()
    )
    response1 = __get_response(api_client, instance1.id, user=r_cu1.user)
    assert len(response1.data) == 10
    assert response1.data["id"] == instance1.id
    assert response1.data["invited_company_user_email"] == instance1.invited_company_user_email

    assert len(response1.data["invited_company"]) == 4
    assert response1.data["invited_company"]["id"] == instance1.invited_company.id
    assert response1.data["invited_company"]["title"] == instance1.invited_company.title
    assert response1.data["invited_company"]["subdomain"] == instance1.invited_company.subdomain
    assert response1.data["invited_company"]["logo"] == instance1.invited_company.logo

    assert len(response1.data["inviting_company"]) == 4
    assert response1.data["inviting_company"]["id"] == r_cu1.company.id
    assert response1.data["inviting_company"]["title"] == r_cu1.company.title
    assert response1.data["inviting_company"]["subdomain"] == r_cu1.company.subdomain
    assert response1.data["inviting_company"]["logo"] == r_cu1.company.logo

    assert len(response1.data["inviting_company_user"]) == 1
    assert response1.data["inviting_company_user"]["id"] == r_cu1.id
    assert response1.data["invited_company_status"] == CPS.ACCEPT.value
    assert response1.data["inviting_company_status"] == CPS.ACCEPT.value
    assert response1.data["invited_project_partnership_qty_map"]
    assert response1.data["updated_at"]
    assert response1.data["created_at"]

    r_cu2 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    instance2 = get_company_partnership_fi(invited_company=r_cu2.company, **CPS_ING_AND_ED_COMPANY_STATUS)
    response2 = __get_response(api_client, instance2.id, user=r_cu2.user)
    assert len(response2.data) == 10
    assert response2.data["id"] == instance2.id
    assert response2.data["invited_company_user_email"] == instance2.invited_company_user_email

    assert len(response2.data["invited_company"]) == 4
    assert response2.data["invited_company"]["id"] == r_cu2.company.id
    assert response2.data["invited_company"]["title"] == r_cu2.company.title
    assert response2.data["invited_company"]["subdomain"] == r_cu2.company.subdomain
    assert response2.data["invited_company"]["logo"] == r_cu2.company.logo

    assert len(response2.data["inviting_company"]) == 4
    assert response2.data["inviting_company"]["id"] == instance2.inviting_company.id
    assert response2.data["inviting_company"]["title"] == instance2.inviting_company.title
    assert response2.data["inviting_company"]["subdomain"] == instance2.inviting_company.subdomain
    assert response2.data["inviting_company"]["logo"] == instance2.inviting_company.logo

    assert len(response2.data["inviting_company_user"]) == 1
    assert response2.data["inviting_company_user"]["id"] == instance2.inviting_company_user.id
    assert response2.data["invited_company_status"] == CPS.ACCEPT.value
    assert response2.data["inviting_company_status"] == CPS.ACCEPT.value
    assert response2.data["invited_project_partnership_qty_map"]
    assert response2.data["updated_at"]
    assert response2.data["created_at"]


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__with_policies__success(
    api_client, monkeypatch, role, get_cu_fi, get_company_partnership_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu_policy_inviting = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu_policy_inviting.company.id])
    instance1 = get_company_partnership_fi(inviting_company_user=r_cu_policy_inviting)
    response1 = __get_response(api_client, instance1.id, user=r_cu_policy_inviting.user)
    assert response1.data["id"] == instance1.id

    r_cu_policy_invited = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    company = r_cu_policy_invited.company
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [company.id])
    instance2 = get_company_partnership_fi(invited_company=company)
    response2 = __get_response(api_client, instance2.id, user=r_cu_policy_invited.user)
    assert response2.data["id"] == instance2.id


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__without_policies__fail(
    api_client, mock_policies_false, role, get_cu_fi, get_company_partnership_fi
):
    r_cu1 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    instance = get_company_partnership_fi(inviting_company_user=r_cu1)
    response = __get_response(api_client, instance.id, user=r_cu1.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail

    r_cu2 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    instance2 = get_company_partnership_fi(invited_company=r_cu2.company)
    response2 = __get_response(api_client, instance2.id, user=r_cu2.user, status_codes=NotFound)
    assert response2.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__related_to_company__with_policy__success(
    api_client, monkeypatch, role, get_cu_fi, get_company_partnership_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu1 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu1.company.id])
    instance1 = get_company_partnership_fi(inviting_company_user=r_cu1)
    response1 = __get_response(api_client, instance1.id, user=r_cu1.user)
    assert response1.data
    assert response1.data["id"] == instance1.id

    r_cu2 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu2.company.id])
    instance2 = get_company_partnership_fi(invited_company=r_cu2.company)
    response2 = __get_response(api_client, instance2.id, user=r_cu2.user)
    assert response2.data
    assert response2.data["id"] == instance2.id


@pytest.mark.parametrize("role", ROLES)
def test__not_owner_not_related_to_company__with_policy__fail(
    api_client, monkeypatch, role, get_cu_fi, get_company_partnership_fi
):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    instance = get_company_partnership_fi()
    response = __get_response(api_client, instance.id, user=r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail
