import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated

from tests.utils import request_response_list, retrieve_response_instance
from ma_saas.constants.company import CPS, CUR, CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from ma_saas.constants.project import PPS
from clients.policies.interface import Policies

User = get_user_model()

__get_response = functools.partial(request_response_list, path="/api/v1/project-scheme-partnership/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("project_scheme_partnership_fi")])
def test__user_without_companies_got_nothing(api_client, monkeypatch, user_fi, instance):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    response = __get_response(api_client, user=user_fi)
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("is_client_company", (True, False))
def test__accepted_owner__without_policy__success(
    api_client,
    mock_policies_false,
    r_cu,
    get_project_scheme_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_company_fi,
    get_project_scheme_partnership_fi,
    is_client_company,
):
    company = get_company_fi()
    if is_client_company:
        cp = get_company_partnership_fi(inviting_company=company, invited_company=r_cu.company)
    else:
        cp = get_company_partnership_fi(inviting_company=r_cu.company, invited_company=company)
    pp = get_project_partnership_fi(company_partnership=cp)

    project_scheme = get_project_scheme_fi(project=pp.project)
    instance = get_project_scheme_partnership_fi(project_scheme=project_scheme, project_partnership=pp)

    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == 1
    assert response.data[0]["id"] == instance.id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
@pytest.mark.parametrize("is_client_company", (True, False))
def test__not_accepted_owner__with_policy__fail(
    api_client,
    monkeypatch,
    get_cu_fi,
    get_project_scheme_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_company_fi,
    get_project_scheme_partnership_fi,
    is_client_company,
    status,
):
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    r_cu = get_cu_fi(role=CUR.OWNER, status=status)
    company = get_company_fi()
    if is_client_company:
        cp = get_company_partnership_fi(inviting_company=company, invited_company=r_cu.company)
        pp = get_project_partnership_fi(company_partnership=cp)
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [pp.id])
    else:
        cp = get_company_partnership_fi(inviting_company=r_cu.company, invited_company=company)
        pp = get_project_partnership_fi(company_partnership=cp)
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    project_scheme = get_project_scheme_fi(project=pp.project)
    _instance = get_project_scheme_partnership_fi(project_scheme=project_scheme, project_partnership=pp)

    response = __get_response(api_client, r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
@pytest.mark.parametrize("is_client_company", (True, False))
def test__not_accepted_owner__without_policy__fail(
    api_client,
    monkeypatch,
    get_cu_fi,
    get_project_scheme_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_company_fi,
    get_project_scheme_partnership_fi,
    is_client_company,
    status,
):
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    r_cu = get_cu_fi(role=CUR.OWNER, status=status)
    company = get_company_fi()
    if is_client_company:
        cp = get_company_partnership_fi(inviting_company=company, invited_company=r_cu.company)
    else:
        cp = get_company_partnership_fi(inviting_company=r_cu.company, invited_company=company)
    pp = get_project_partnership_fi(company_partnership=cp)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])

    project_scheme = get_project_scheme_fi(project=pp.project)
    _instance = get_project_scheme_partnership_fi(project_scheme=project_scheme, project_partnership=pp)

    response = __get_response(api_client, r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
@pytest.mark.parametrize("is_client_company", (True, False))
def test__not_owner__without_policy__fail(
    api_client,
    monkeypatch,
    get_cu_fi,
    get_project_scheme_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_company_fi,
    get_project_scheme_partnership_fi,
    is_client_company,
    role,
):
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])

    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    company = get_company_fi()
    if is_client_company:
        cp = get_company_partnership_fi(inviting_company=company, invited_company=r_cu.company)
    else:
        cp = get_company_partnership_fi(inviting_company=r_cu.company, invited_company=company)
    pp = get_project_partnership_fi(company_partnership=cp)

    project_scheme = get_project_scheme_fi(project=pp.project)
    _instance = get_project_scheme_partnership_fi(project_scheme=project_scheme, project_partnership=pp)

    response = __get_response(api_client, r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
@pytest.mark.parametrize("is_client_company", (True, False))
def test__not_owner__with_policy__success(
    api_client,
    monkeypatch,
    get_cu_fi,
    get_project_scheme_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_company_fi,
    get_project_scheme_partnership_fi,
    is_client_company,
    role,
):
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    company = get_company_fi()
    if is_client_company:
        cp = get_company_partnership_fi(inviting_company=company, invited_company=r_cu.company)
        pp = get_project_partnership_fi(company_partnership=cp)
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [pp.id])
    else:
        cp = get_company_partnership_fi(inviting_company=r_cu.company, invited_company=company)
        pp = get_project_partnership_fi(company_partnership=cp)
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    project_scheme = get_project_scheme_fi(project=pp.project)
    instance = get_project_scheme_partnership_fi(project_scheme=project_scheme, project_partnership=pp)

    response = __get_response(api_client, r_cu.user)
    assert response.data[0]["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("is_client_company", (True, False))
@pytest.mark.parametrize(
    ("invited_company_status", "inviting_company_status"),
    [*[(PPS.ACCEPT, s) for s in PPS if s != PPS.ACCEPT], *[(s, PPS.ACCEPT) for s in PPS if s != PPS.ACCEPT]],
)
def test__not_active_project_partnership__success(
    api_client,
    mock_policies_false,
    r_cu,
    get_project_scheme_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_company_fi,
    get_project_scheme_partnership_fi,
    is_client_company,
    invited_company_status,
    inviting_company_status,
):
    company = get_company_fi()
    if is_client_company:
        cp = get_company_partnership_fi(inviting_company=company, invited_company=r_cu.company)
    else:
        cp = get_company_partnership_fi(inviting_company=r_cu.company, invited_company=company)
    pp = get_project_partnership_fi(company_partnership=cp)
    pp.invited_company_status = invited_company_status
    pp.inviting_company_status = inviting_company_status
    pp.save()

    project_scheme = get_project_scheme_fi(project=pp.project)
    instance = get_project_scheme_partnership_fi(project_scheme=project_scheme, project_partnership=pp)

    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == 1
    assert response.data[0]["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("is_client_company", (True, False))
@pytest.mark.parametrize(
    ("invited_company_status", "inviting_company_status"),
    [*[(CPS.ACCEPT, s) for s in CPS if s != CPS.ACCEPT], *[(s, CPS.ACCEPT) for s in CPS if s != CPS.ACCEPT]],
)
def test__not_active_company_partnership__success(
    api_client,
    mock_policies_false,
    r_cu,
    get_project_scheme_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_company_fi,
    get_project_scheme_partnership_fi,
    is_client_company,
    invited_company_status,
    inviting_company_status,
):
    company = get_company_fi()
    if is_client_company:
        cp = get_company_partnership_fi(inviting_company=company, invited_company=r_cu.company)
    else:
        cp = get_company_partnership_fi(inviting_company=r_cu.company, invited_company=company)
    pp = get_project_partnership_fi(company_partnership=cp)
    cp.invited_company_status = invited_company_status
    cp.inviting_company_status = inviting_company_status
    cp.save()

    project_scheme = get_project_scheme_fi(project=pp.project)
    instance = get_project_scheme_partnership_fi(project_scheme=project_scheme, project_partnership=pp)

    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == 1
    assert response.data[0]["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("qty", (1, 3))
@pytest.mark.parametrize("is_client_company", (True, False))
def test__response_data(
    api_client,
    mock_policies_false,
    r_cu,
    get_project_scheme_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_company_fi,
    get_project_scheme_partnership_fi,
    qty,
    is_client_company,
):
    company = get_company_fi()
    if is_client_company:
        cp = get_company_partnership_fi(inviting_company=company, invited_company=r_cu.company)
    else:
        cp = get_company_partnership_fi(inviting_company=r_cu.company, invited_company=company)
    pp = get_project_partnership_fi(company_partnership=cp)
    instances = []
    for _ in range(qty):
        project_scheme = get_project_scheme_fi(project=pp.project)
        instance = get_project_scheme_partnership_fi(project_scheme=project_scheme, project_partnership=pp)
        instances.append(instance)
    instances.reverse()

    response = __get_response(api_client, user=r_cu.user)
    for index, response_instance in enumerate(response.data):
        instance = instances[index]
        assert response_instance.pop("id") == instance.id
        if response_scheme := retrieve_response_instance(response_instance, "project_scheme", dict):
            instance_scheme = instance.project_scheme
            assert response_scheme.pop("id") == instance_scheme.id
            assert response_scheme.pop("title") == instance_scheme.title
            assert response_scheme.pop("is_labour_exchange") == instance_scheme.is_labour_exchange
            assert not response_scheme
        if response_pp := retrieve_response_instance(response_instance, "project_partnership", dict):
            assert response_pp.pop("id") == pp.id
            if response_project := retrieve_response_instance(response_pp, "project", dict):
                assert response_project.pop("id") == pp.project.id
                assert response_project.pop("title") == pp.project.title
                if response_company := retrieve_response_instance(response_project, "company", dict):
                    assert response_company.pop("id") == pp.project.company.id
                    assert response_company.pop("title") == pp.project.company.title
                    assert not response_company
                assert not response_project
            if response_partner_company := retrieve_response_instance(response_pp, "partner_company", dict):
                assert response_partner_company.pop("id") == pp.partner_company.id
                assert response_partner_company.pop("title") == pp.partner_company.title
                assert not response_partner_company
            assert not response_pp
        assert response_instance.pop("created_at")
        assert response_instance.pop("updated_at")
        assert response_instance.pop("is_processed_reports_acceptance_allowed") is True
        assert not response_instance
