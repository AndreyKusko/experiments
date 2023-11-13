import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated

from tests.utils import request_response_list
from ma_saas.constants.company import CUR, CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES, CPS_ING_AND_ED_COMPANY_STATUS
from ma_saas.constants.project import PPS, PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES
from clients.policies.interface import Policies

User = get_user_model()

qty = 3

__get_response = functools.partial(request_response_list, path="/api/v1/project-partnerships/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


def test__user_without_companies_got_nothing(api_client, monkeypatch, user_fi: User):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    response = __get_response(api_client, user=user_fi)
    assert not response.data, f"response.data = {response.data}"


def test__owners__success(
    monkeypatch,
    api_client,
    user_fi,
    get_cu_fi,
    get_company_partnership_fi,
    get_project_fi,
    get_project_partnership_fi,
):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    r_cu1 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    cp1 = get_company_partnership_fi(inviting_company_user=r_cu1, **CPS_ING_AND_ED_COMPANY_STATUS)
    instances1 = []
    for _ in range(qty):
        p = dict(project=get_project_fi(company=r_cu1.company))
        pp = get_project_partnership_fi(
            inviting_company_user=r_cu1,
            **p,
            company_partnership=cp1,
            **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES,
        )
        instances1.append(pp)
    instances1.reverse()
    response1 = __get_response(api_client, user=r_cu1.user)
    assert len(response1.data) == qty, response1.data
    for index, instance1 in enumerate(instances1):
        assert response1.data[index]["id"] == instance1.id

    r_cu2 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    cp2 = get_company_partnership_fi(invited_company=r_cu2.company, **CPS_ING_AND_ED_COMPANY_STATUS)
    instances2 = []
    for _ in range(qty):
        p = dict(project=get_project_fi(company=r_cu1.company))
        pp = get_project_partnership_fi(
            inviting_company_user=r_cu2,
            **p,
            company_partnership=cp2,
            **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES,
        )
        instances2.append(pp)
    instances2.reverse()
    response2 = __get_response(api_client, user=r_cu2.user)
    assert len(response1.data) == qty, response2.data
    for index, instance2 in enumerate(instances2):
        assert response2.data[index]["id"] == instance2.id


def test__response_data(
    monkeypatch,
    api_client,
    get_project_fi,
    get_cu_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    r_cu1 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    cp1 = get_company_partnership_fi(inviting_company_user=r_cu1, **CPS_ING_AND_ED_COMPANY_STATUS)
    instances1 = []
    for _ in range(qty):
        p = dict(project=get_project_fi(company=r_cu1.company))
        pp = get_project_partnership_fi(
            inviting_company_user=r_cu1,
            **p,
            company_partnership=cp1,
            **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES,
        )
        instances1.append(pp)
    instances1.reverse()
    response = __get_response(api_client, user=r_cu1.user)

    response_instance = response.data

    assert len(response_instance) == qty, response_instance
    for index, instance1 in enumerate(instances1):
        assert response_instance[index]["id"] == instance1.id

    assert len(response_instance) == qty, response_instance
    for index, instance1 in enumerate(instances1):
        assert response_instance[index]["id"] == instance1.id
        assert response_instance[index]["project"]["id"] == instance1.project.id
        assert response_instance[index]["project"]["title"] == instance1.project.title

        assert response_instance[index]["project"]["company"]["id"] == instance1.project.company.id
        assert response_instance[index]["project"]["company"]["title"] == instance1.project.company.title
        assert (
            response_instance[index]["project"]["company"]["subdomain"] == instance1.project.company.subdomain
        )
        assert response_instance[index]["project"]["company"]["logo"] == instance1.project.company.logo

        assert response_instance[index]["inviting_company_user"]["id"] == instance1.inviting_company_user.id

        assert response_instance[index]["created_at"]
        assert response_instance[index]["created_at"]


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accept_owners__fail(
    monkeypatch,
    api_client,
    user_fi,
    get_cu_fi,
    get_company_partnership_fi,
    get_project_fi,
    get_project_partnership_fi,
    status,
):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    r_cu1 = get_cu_fi(role=CUR.OWNER, status=status.value)
    cp1 = get_company_partnership_fi(inviting_company_user=r_cu1, **CPS_ING_AND_ED_COMPANY_STATUS)
    instances1 = []
    for _ in range(qty):
        p = dict(project=get_project_fi(company=r_cu1.company))
        pp = get_project_partnership_fi(
            inviting_company_user=r_cu1,
            **p,
            company_partnership=cp1,
            **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES,
        )
        instances1.append(pp)
    instances1.reverse()
    response1 = __get_response(api_client, user=r_cu1.user)
    assert not response1.data

    r_cu2 = get_cu_fi(role=CUR.OWNER, status=status)
    cp2 = get_company_partnership_fi(invited_company=r_cu2.company, **CPS_ING_AND_ED_COMPANY_STATUS)
    instances2 = []
    for _ in range(qty):
        p = dict(project=get_project_fi(company=r_cu1.company))
        pp = get_project_partnership_fi(
            inviting_company_user=r_cu2,
            **p,
            company_partnership=cp2,
            **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES,
        )
        instances2.append(pp)
    instances2.reverse()
    response2 = __get_response(api_client, user=r_cu2.user)
    assert not response2.data


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__without_policy__fail(
    monkeypatch,
    api_client,
    user_fi,
    get_cu_fi,
    get_company_partnership_fi,
    get_project_fi,
    get_project_partnership_fi,
    role,
):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    r_cu1 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    cp1 = get_company_partnership_fi(inviting_company_user=r_cu1, **CPS_ING_AND_ED_COMPANY_STATUS)
    instances1 = []
    for _ in range(qty):
        p = dict(project=get_project_fi(company=r_cu1.company))
        pp = get_project_partnership_fi(
            inviting_company_user=r_cu1,
            **p,
            company_partnership=cp1,
            **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES,
        )
        instances1.append(pp)
    instances1.reverse()
    response1 = __get_response(api_client, user=r_cu1.user)
    assert not response1.data

    r_cu2 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    cp2 = get_company_partnership_fi(invited_company=r_cu2.company, **CPS_ING_AND_ED_COMPANY_STATUS)
    instances2 = []
    for _ in range(qty):
        p = dict(project=get_project_fi(company=r_cu1.company))
        pp = get_project_partnership_fi(
            inviting_company_user=r_cu2,
            **p,
            company_partnership=cp2,
            **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES,
        )
        instances2.append(pp)
    instances2.reverse()
    response2 = __get_response(api_client, user=r_cu2.user)
    assert not response2.data


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__with_policy__success(
    monkeypatch,
    api_client,
    user_fi,
    get_cu_fi,
    get_company_partnership_fi,
    get_project_fi,
    get_project_partnership_fi,
    role,
):
    r_cu1 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    cp1 = get_company_partnership_fi(inviting_company_user=r_cu1, **CPS_ING_AND_ED_COMPANY_STATUS)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu1.company.id])
    instances1 = []
    for _ in range(qty):
        p = dict(project=get_project_fi(company=r_cu1.company))
        pp = get_project_partnership_fi(
            inviting_company_user=r_cu1,
            **p,
            company_partnership=cp1,
            **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES,
        )
        instances1.append(pp)
    instances1.reverse()
    response1 = __get_response(api_client, user=r_cu1.user)
    assert len(response1.data) == qty, response1.data
    for index, instance1 in enumerate(instances1):
        assert response1.data[index]["id"] == instance1.id

    r_cu2 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    cp2 = get_company_partnership_fi(invited_company=r_cu2.company, **CPS_ING_AND_ED_COMPANY_STATUS)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu2.company.id])
    instances2 = []
    for _ in range(qty):
        p = dict(project=get_project_fi(company=r_cu1.company))
        pp = get_project_partnership_fi(
            inviting_company_user=r_cu2,
            **p,
            company_partnership=cp2,
            **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES,
        )
        instances2.append(pp)
    instances2.reverse()
    response2 = __get_response(api_client, user=r_cu2.user)
    assert len(response2.data) == qty, response2.data
    for index, instance2 in enumerate(instances2):
        assert response2.data[index]["id"] == instance2.id


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

    response1 = __get_response(api_client, user=r_cu.user)
    assert response1.data[0]["id"] == instance1.id


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

    response = __get_response(api_client, r_cu.user)
    assert response.data == []


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

    response = __get_response(api_client, r_cu.user)
    assert response.data == []


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
    old_inviting_status, new_inviting_status = PPS.ACCEPT.value, PPS.CANCEL.value
    r_cu = get_cu_fi(role=CUR.PROJECT_MANAGER, status=CUS.ACCEPT.value)
    inviting_company, invited_company = r_cu.company, get_company_fi()
    project = get_project_fi(company=inviting_company)
    cp = get_company_partnership_fi(
        inviting_company=inviting_company, invited_company=invited_company, **CPS_ING_AND_ED_COMPANY_STATUS
    )
    q_data1 = {"project": project, "company_partnership": cp}
    instance = get_project_partnership_fi(
        **q_data1, inviting_company_status=old_inviting_status, invited_company_status=PPS.ACCEPT.value
    )
    assert instance.inviting_company_status == old_inviting_status
    assert old_inviting_status != new_inviting_status

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

    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == 1
    assert response.data[0]["id"] == instance.id
