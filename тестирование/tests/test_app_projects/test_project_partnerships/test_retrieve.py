import json
import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated

from tests.utils import request_response_get, retrieve_response_instance
from ma_saas.constants.company import (
    CUR,
    CUS,
    ROLES,
    NOT_ACCEPT_CUS,
    NOT_OWNER_ROLES,
    CPS_ING_AND_ED_COMPANY_STATUS,
)
from ma_saas.constants.company import CompanyPartnershipStatus as CPS
from ma_saas.constants.project import PPS, PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES
from clients.policies.interface import Policies
from projects.models.project_partnership import ProjectPartnership

User = get_user_model()

__get_response = functools.partial(request_response_get, path="/api/v1/project-partnerships/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("company_partnership_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize(
    "cps_data",
    [
        {"inviting_company_status": CPS.ACCEPT, "invited_company_status": CPS.INVITE},
        {"inviting_company_status": CPS.ACCEPT, "invited_company_status": CPS.ACCEPT},
        {"inviting_company_status": CPS.ACCEPT, "invited_company_status": CPS.CANCEL},
        {"inviting_company_status": CPS.CANCEL, "invited_company_status": CPS.INVITE},
        {"inviting_company_status": CPS.CANCEL, "invited_company_status": CPS.ACCEPT},
        {"inviting_company_status": CPS.CANCEL, "invited_company_status": CPS.CANCEL},
    ],
)
@pytest.mark.parametrize(
    "pps_data",
    [
        {"inviting_company_status": PPS.ACCEPT, "invited_company_status": PPS.INVITE},
        {"inviting_company_status": PPS.ACCEPT, "invited_company_status": PPS.ACCEPT},
        {"inviting_company_status": PPS.ACCEPT, "invited_company_status": PPS.CANCEL},
        {"inviting_company_status": PPS.CANCEL, "invited_company_status": PPS.INVITE},
        {"inviting_company_status": PPS.CANCEL, "invited_company_status": PPS.ACCEPT},
        {"inviting_company_status": PPS.CANCEL, "invited_company_status": PPS.CANCEL},
    ],
)
def test__accepted_owners__success(
    api_client,
    mock_policies_false,
    get_cu_fi,
    get_project_fi,
    cps_data,  # company partnership status data
    pps_data,  # project partnership status data
    get_company_partnership_fi,
    get_project_partnership_fi,
):

    r_cu1 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    project1 = get_project_fi(company=r_cu1.company)
    cp1 = get_company_partnership_fi(inviting_company_user=r_cu1, **cps_data)
    q_data1 = {"project": project1, "company_partnership": cp1}

    instance1 = get_project_partnership_fi(**q_data1, **{v: s.value for v, s in pps_data.items()})
    response1 = __get_response(api_client, instance_id=instance1.id, user=r_cu1.user)
    assert response1.data["id"] == instance1.id

    r_cu2 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    project2 = get_project_fi(company=r_cu1.company)
    cp2 = get_company_partnership_fi(invited_company=r_cu2.company, **cps_data)
    q_data2 = {"project": project2, "company_partnership": cp2}
    instance2 = get_project_partnership_fi(**q_data2, **pps_data)
    response2 = __get_response(api_client, instance_id=instance2.id, user=r_cu2.user)
    assert response2.data["id"] == instance2.id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__without_policies__fail(
    api_client,
    mock_policies_false,
    status,
    get_cu_fi,
    get_company_partnership_fi,
    get_project_fi,
    get_project_partnership_fi,
):
    r_cu1 = get_cu_fi(role=CUR.OWNER, status=status.value)
    project1 = get_project_fi(company=r_cu1.company)
    cp1 = get_company_partnership_fi(inviting_company_user=r_cu1, **CPS_ING_AND_ED_COMPANY_STATUS)
    q_data1 = {"project": project1, "company_partnership": cp1}
    instance1 = get_project_partnership_fi(**q_data1, **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES)
    response1 = __get_response(api_client, instance_id=instance1.id, user=r_cu1.user, status_codes=NotFound)
    assert response1.data == {"detail": NotFound.default_detail}

    r_cu2 = get_cu_fi(role=CUR.OWNER, status=status)
    project2 = get_project_fi(company=r_cu1.company)
    cp2 = get_company_partnership_fi(invited_company=r_cu2.company, **CPS_ING_AND_ED_COMPANY_STATUS)
    q_data2 = {"project": project2, "company_partnership": cp2}
    instance2 = get_project_partnership_fi(**q_data2, **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES)
    response2 = __get_response(api_client, instance_id=instance2.id, user=r_cu2.user, status_codes=NotFound)
    assert response2.data == {"detail": NotFound.default_detail}


def test__response_data(
    api_client,
    mock_policies_false,
    get_cu_fi,
    get_company_partnership_fi,
    get_project_fi,
    get_project_partnership_fi,
):

    r_cu1 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    project1 = get_project_fi(company=r_cu1.company)
    cp1 = get_company_partnership_fi(inviting_company_user=r_cu1, **CPS_ING_AND_ED_COMPANY_STATUS)
    q_data1 = {"project": project1, "company_partnership": cp1}
    instance1 = get_project_partnership_fi(**q_data1, **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES)
    response1 = __get_response(api_client, instance_id=instance1.id, user=r_cu1.user)
    response_instance1 = response1.data
    assert response_instance1.pop("id") == instance1.id

    if response_project := retrieve_response_instance(response_instance1, "project", dict):
        assert response_project.pop("id") == instance1.project.id
        assert response_project.pop("title") == instance1.project.title

        if response_project_company := retrieve_response_instance(response_project, "company", dict):
            assert response_project_company.pop("id") == instance1.project.company.id
            assert response_project_company.pop("title") == instance1.project.company.title
            assert response_project_company.pop("subdomain") == instance1.project.company.subdomain
            assert response_project_company.pop("logo") == instance1.project.company.logo
        assert not response_project_company

    assert not response_project

    if response_instance_1_inviting_company_user := retrieve_response_instance(
        response_instance1, "inviting_company_user", dict
    ):
        assert response_instance_1_inviting_company_user.pop("id") == instance1.inviting_company_user.id
    assert not response_instance_1_inviting_company_user

    assert response_instance1.pop("invited_company_status") == instance1.invited_company_status
    assert response_instance1.pop("inviting_company_status") == instance1.inviting_company_status
    assert response_instance1.pop("company_partnership") == {"id": instance1.company_partnership.id}
    assert response_instance1.pop("created_at")
    assert response_instance1.pop("updated_at")
    assert response_instance1.pop("partner_company") is None
    assert not response_instance1

    r_cu2 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    project2 = get_project_fi(company=r_cu1.company)
    cp2 = get_company_partnership_fi(invited_company=r_cu2.company, **CPS_ING_AND_ED_COMPANY_STATUS)
    q_data2 = {"project": project2, "company_partnership": cp2}
    instance2 = get_project_partnership_fi(**q_data2, **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES)
    response2 = __get_response(api_client, instance_id=instance2.id, user=r_cu2.user)
    response_instance2 = response2.data
    assert response_instance2.pop("id") == instance2.id
    if response_instance_2_project := retrieve_response_instance(response_instance2, "project", dict):
        assert response_instance_2_project.pop("id") == instance2.project.id
        assert response_instance_2_project.pop("title") == instance2.project.title
        if response_instance_2_project_company := retrieve_response_instance(
            response_instance_2_project, "company", dict
        ):
            assert response_instance_2_project_company.pop("id") == instance2.project.company.id
            assert response_instance_2_project_company.pop("title") == instance2.project.company.title
            assert response_instance_2_project_company.pop("subdomain") == instance2.project.company.subdomain
            assert response_instance_2_project_company.pop("logo") == instance2.project.company.logo
        assert not response_instance_2_project_company
    assert not response_instance_2_project
    if response_inviting_cu := retrieve_response_instance(response_instance2, "inviting_company_user", dict):
        assert response_inviting_cu.pop("id") == instance2.inviting_company_user.id
    assert not response_inviting_cu
    assert response_instance2.pop("created_at")
    assert response_instance2.pop("updated_at")

    if response_partner_company := retrieve_response_instance(response_instance2, "partner_company", dict):
        assert response_partner_company.pop("id") == instance2.company_partnership.inviting_company.id
        assert response_partner_company.pop("title") == instance2.company_partnership.inviting_company.title
    assert not response_partner_company

    assert response_instance2.pop("invited_company_status") == instance2.invited_company_status
    assert response_instance2.pop("inviting_company_status") == instance2.inviting_company_status
    if response_instance_2_company_partnership := retrieve_response_instance(
        response_instance2, "company_partnership", dict
    ):
        assert response_instance_2_company_partnership.pop("id") == instance2.company_partnership.id
    assert not response_instance_2_company_partnership
    assert not response_instance2


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__with_policies__success(
    api_client,
    monkeypatch,
    role,
    get_cu_fi,
    get_company_partnership_fi,
    get_project_fi,
    get_project_partnership_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    r_cu1 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu1.company.id])
    project1 = get_project_fi(company=r_cu1.company)
    cp1 = get_company_partnership_fi(inviting_company_user=r_cu1, **CPS_ING_AND_ED_COMPANY_STATUS)
    q_data1 = {"project": project1, "company_partnership": cp1}
    instance1 = get_project_partnership_fi(**q_data1, **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES)
    response1 = __get_response(api_client, instance_id=instance1.id, user=r_cu1.user)
    assert response1.data["id"] == instance1.id

    r_cu2 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu2.company.id])
    project2 = get_project_fi(company=r_cu1.company)
    cp2 = get_company_partnership_fi(invited_company=r_cu2.company, **CPS_ING_AND_ED_COMPANY_STATUS)
    q_data2 = {"project": project2, "company_partnership": cp2}
    instance2 = get_project_partnership_fi(**q_data2, **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES)
    response2 = __get_response(api_client, instance_id=instance2.id, user=r_cu2.user)
    assert response2.data["id"] == instance2.id


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__without_policies__fail(
    api_client,
    mock_policies_false,
    role,
    get_cu_fi,
    get_company_partnership_fi,
    get_project_fi,
    get_project_partnership_fi,
):

    r_cu1 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    project1 = get_project_fi(company=r_cu1.company)
    cp1 = get_company_partnership_fi(inviting_company=r_cu1.company, **CPS_ING_AND_ED_COMPANY_STATUS)
    q_data1 = {"project": project1, "company_partnership": cp1}
    instance1 = get_project_partnership_fi(**q_data1, **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES)
    response1 = __get_response(api_client, instance_id=instance1.id, user=r_cu1.user, status_codes=NotFound)
    assert response1.data["detail"] == NotFound.default_detail

    r_cu2 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    project2 = get_project_fi(company=r_cu1.company)
    cp2 = get_company_partnership_fi(invited_company=r_cu2.company, **CPS_ING_AND_ED_COMPANY_STATUS)
    q_data2 = {"project": project2, "company_partnership": cp2}
    instance2 = get_project_partnership_fi(**q_data2, **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES)
    response2 = __get_response(api_client, instance_id=instance2.id, user=r_cu2.user, status_codes=NotFound)
    assert response2.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__related_to_company__with_policy__success(
    api_client,
    monkeypatch,
    role,
    get_cu_fi,
    get_company_partnership_fi,
    get_project_fi,
    get_project_partnership_fi,
    get_company_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu1 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    cp1 = get_company_partnership_fi(inviting_company=r_cu1.company, **CPS_ING_AND_ED_COMPANY_STATUS)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [cp1.inviting_company.id])
    instance1 = get_project_partnership_fi(
        company_partnership=cp1, **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES
    )
    response1 = __get_response(api_client, instance_id=instance1.id, user=r_cu1.user)
    assert response1.data["id"] == instance1.id

    r_cu2 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    cp2 = get_company_partnership_fi(invited_company=r_cu2.company, **CPS_ING_AND_ED_COMPANY_STATUS)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [cp2.invited_company.id])
    instance2 = get_project_partnership_fi(
        company_partnership=cp2, **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES
    )
    response2 = __get_response(api_client, instance_id=instance2.id, user=r_cu2.user)
    assert response2.data["id"] == instance2.id


@pytest.mark.parametrize("role", ROLES)
def test__not_owner_not_related_to_company__with_policy__fail(
    api_client,
    monkeypatch,
    role,
    get_cu_fi,
    get_company_partnership_fi,
    get_company_fi,
    get_project_partnership_fi,
):
    r_cu1 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    cp1 = get_company_partnership_fi(inviting_company=get_company_fi(), **CPS_ING_AND_ED_COMPANY_STATUS)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance1 = get_project_partnership_fi(
        company_partnership=cp1, **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES
    )
    response1 = __get_response(api_client, instance_id=instance1.id, user=r_cu1.user, status_codes=NotFound)
    assert response1.data["detail"] == NotFound.default_detail

    r_cu2 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    cp2 = get_company_partnership_fi(invited_company=get_company_fi(), **CPS_ING_AND_ED_COMPANY_STATUS)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance2 = get_project_partnership_fi(
        company_partnership=cp2, **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES
    )
    response2 = __get_response(api_client, instance_id=instance2.id, user=r_cu2.user, status_codes=NotFound)
    assert response2.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("permission", ["pp_perm", "invited_company_perm", "company_partnership_perm"])
def test__invited_company_user__invited_company_perm__success(
    api_client,
    monkeypatch,
    get_cu_fi,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_company_fi,
    permission,
):
    r_cu = get_cu_fi(role=CUR.PROJECT_MANAGER, status=CUS.ACCEPT.value)
    project = get_project_fi()
    cp = get_company_partnership_fi(
        inviting_company=project.company, invited_company=r_cu.company, **CPS_ING_AND_ED_COMPANY_STATUS
    )
    q_data1 = {"project": project, "company_partnership": cp}
    instance1 = get_project_partnership_fi(
        **q_data1, inviting_company_status=PPS.ACCEPT.value, invited_company_status=PPS.ACCEPT.value
    )
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    if permission == "pp_perm":
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [instance1.id])
    elif permission == "invited_company_perm":
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    elif permission == "company_partnership_perm":
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [cp.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    response1 = __get_response(api_client, instance_id=instance1.id, user=r_cu.user)
    assert response1.data["id"] == instance1.id


@pytest.mark.parametrize("permission", ["project_perm", "inviting_company_perm"])
def test__invited_company_user__inviting_company_perm__fail(
    api_client,
    monkeypatch,
    get_cu_fi,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_company_fi,
    permission,
):
    r_cu = get_cu_fi(role=CUR.PROJECT_MANAGER, status=CUS.ACCEPT.value)
    project = get_project_fi()
    inviting_company = project.company
    cp1 = get_company_partnership_fi(
        inviting_company=inviting_company, invited_company=r_cu.company, **CPS_ING_AND_ED_COMPANY_STATUS
    )
    q_data1 = {"project": project, "company_partnership": cp1}
    instance = get_project_partnership_fi(
        **q_data1, inviting_company_status=PPS.ACCEPT.value, invited_company_status=PPS.ACCEPT.value
    )

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    if permission == "project_perm":
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [project.id])
    elif permission == "inviting_company_perm":
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [inviting_company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("permission", ["invited_company_perm"])
def test__inviting_company_user__invited_company_perm__fail(
    api_client,
    monkeypatch,
    get_cu_fi,
    get_company_fi,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    permission,
):
    r_cu = get_cu_fi(role=CUR.PROJECT_MANAGER, status=CUS.ACCEPT.value)
    project = get_project_fi(company=r_cu.company)
    invited_company = get_company_fi()
    cp = get_company_partnership_fi(
        inviting_company=r_cu.company, invited_company=invited_company, **CPS_ING_AND_ED_COMPANY_STATUS
    )
    q_data1 = {"project": project, "company_partnership": cp}
    instance = get_project_partnership_fi(
        **q_data1, inviting_company_status=PPS.ACCEPT.value, invited_company_status=PPS.ACCEPT.value
    )

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    if permission == "invited_company_perm":
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [invited_company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize(
    "permission", ["project_perm", "pp_perm", "inviting_company_perm", "company_partnership_perm"]
)
def test__inviting_company_user__inviting_company_perm__success(
    api_client,
    monkeypatch,
    get_cu_fi,
    get_company_fi,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    permission,
):
    r_cu = get_cu_fi(role=CUR.PROJECT_MANAGER, status=CUS.ACCEPT.value)
    project = get_project_fi(company=r_cu.company)
    inviting_company, invited_company = r_cu.company, get_company_fi()
    cp = get_company_partnership_fi(
        inviting_company=inviting_company, invited_company=invited_company, **CPS_ING_AND_ED_COMPANY_STATUS
    )
    q_data1 = {"project": project, "company_partnership": cp}
    instance = get_project_partnership_fi(
        **q_data1, inviting_company_status=PPS.ACCEPT.value, invited_company_status=PPS.ACCEPT.value
    )

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    if permission == "project_perm":
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [project.id])
    elif permission == "pp_perm":
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [instance.id])
    elif permission == "inviting_company_perm":
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [inviting_company.id])
    elif permission == "company_partnership_perm":
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [cp.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    response = __get_response(api_client, instance.id, r_cu.user)
    assert response.data["id"] == instance.id
