import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from tests.utils import request_response_create, retrieve_response_instance
from ma_saas.constants.company import CUR, CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES, CPS_ING_AND_ED_COMPANY_STATUS
from ma_saas.constants.company import CompanyPartnershipStatus as CPS
from ma_saas.constants.project import ProjectPartnershipStatus as PPS
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_MUST_BE_ACCEPT
from projects.models.project_partnership import ProjectPartnership

User = get_user_model()


__get_response = functools.partial(request_response_create, path="/api/v1/project-partnerships/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, {}, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


def test__accepted_owner__success(
    api_client, mock_policies_false, get_cu_fi, get_company_partnership_fi, get_project_fi
):
    # протестировать приглашающим юзером
    r_cu1 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    cp1 = get_company_partnership_fi(inviting_company_user=r_cu1, **CPS_ING_AND_ED_COMPANY_STATUS)
    q_data = {"project": get_project_fi(company=r_cu1.company), "company_partnership": cp1}
    assert not ProjectPartnership.objects.filter(**q_data).exists()
    data1 = {k: v.id for k, v in q_data.items()}
    response1 = __get_response(api_client, data=data1, user=r_cu1.user)
    created_instance1 = ProjectPartnership.objects.filter(**q_data).first()
    assert response1.data
    assert response1.data["id"] == created_instance1.id
    # протестировать приглашенвым юзером
    r_cu2 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    company2 = r_cu2.company
    cp2 = get_company_partnership_fi(invited_company=company2, **CPS_ING_AND_ED_COMPANY_STATUS)
    q_data = {"project": get_project_fi(company=company2), "company_partnership": cp2}
    assert not ProjectPartnership.objects.filter(**q_data).exists()
    data1 = {k: v.id for k, v in q_data.items()}
    response2 = __get_response(api_client, data=data1, user=r_cu2.user)
    created_instance2 = ProjectPartnership.objects.filter(**q_data).first()
    assert response2.data
    assert response2.data["id"] == created_instance2.id


def test__result_data(
    api_client,
    monkeypatch,
    cu_owner_fi,
    get_cu_fi,
    get_company_partnership_fi,
    get_project_fi,
    get_company_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    project = get_project_fi(company=r_cu.company)
    cp = get_company_partnership_fi(
        inviting_company_user=r_cu, invited_company=get_company_fi(), **CPS_ING_AND_ED_COMPANY_STATUS
    )
    q_data = {"project": project, "company_partnership": cp}
    assert not ProjectPartnership.objects.filter(**q_data).exists()

    data = {k: v.id for k, v in q_data.items()}
    response = __get_response(api_client, data=data, user=r_cu.user)

    created_instances = ProjectPartnership.objects.filter(**q_data)
    assert created_instances.count() == 1
    created_instance: ProjectPartnership = created_instances.first()
    assert created_instance.invited_company_status == PPS.INVITE.value
    assert created_instance.inviting_company_status == PPS.ACCEPT.value

    response_instance = response.data
    assert response_instance.pop("id") == created_instance.id

    if response_project := retrieve_response_instance(response_instance, "project", dict):
        assert response_project.pop("id") == project.id
        assert response_project.pop("title") == project.title
        if response_project_company := retrieve_response_instance(response_project, "company", dict):
            assert response_project_company.pop("id") == project.company.id
            assert response_project_company.pop("title") == project.company.title
            assert response_project_company.pop("subdomain") == project.company.subdomain
            assert response_project_company.pop("logo") == project.company.logo
        assert not response_project_company
    assert not response_project

    if response_company_partnership := retrieve_response_instance(
        response_instance, "company_partnership", dict
    ):
        assert response_company_partnership.pop("id") == cp.id
    assert not response_company_partnership

    assert response_instance.pop("invited_company_status") == PPS.INVITE.value
    assert response_instance.pop("inviting_company_status") == PPS.ACCEPT.value
    assert response_instance.pop("updated_at")
    assert response_instance.pop("created_at")

    if response_partner_company := retrieve_response_instance(response_instance, "partner_company", dict):
        assert response_partner_company.pop("id") == cp.invited_company.id
        assert response_partner_company.pop("title") == cp.invited_company.title
        assert response_partner_company.pop("subdomain") == cp.invited_company.subdomain
        assert response_partner_company.pop("logo") == cp.invited_company.logo
    assert not response_partner_company

    if inviting_company_user := retrieve_response_instance(response_instance, "inviting_company_user", dict):
        assert inviting_company_user.pop("id") == r_cu.id
    assert not inviting_company_user

    assert not response_instance


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted__company_owner__fail(
    api_client,
    mock_policies_false,
    cu_owner_fi,
    get_cu_owner_fi,
    get_company_partnership_fi,
    get_project_fi,
    get_company_fi,
    status,
):

    r_cu = get_cu_owner_fi(status=status)
    project = get_project_fi(company=r_cu.company)
    cp = get_company_partnership_fi(
        inviting_company_user=r_cu, invited_company=get_company_fi(), **CPS_ING_AND_ED_COMPANY_STATUS
    )
    q_data = {"project": project, "company_partnership": cp}

    assert not ProjectPartnership.objects.filter(**q_data).exists()
    data = {k: v.id for k, v in q_data.items()}
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert not ProjectPartnership.objects.filter(**q_data).exists()
    assert response.data
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__accepted__not_owner__without_policy__fail(
    api_client,
    mock_policies_false,
    cu_owner_fi,
    get_cu_fi,
    get_company_partnership_fi,
    get_project_fi,
    get_company_fi,
    role,
):

    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    project = get_project_fi(company=r_cu.company)
    cp = get_company_partnership_fi(
        inviting_company_user=r_cu,
        invited_company=get_company_fi(),
        inviting_company_status=CPS.ACCEPT.value,
        invited_company_status=CPS.ACCEPT.value,
    )
    q_data = {"project": project, "company_partnership": cp}

    assert not ProjectPartnership.objects.filter(**q_data).exists()
    data = {k: v.id for k, v in q_data.items()}
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert not ProjectPartnership.objects.filter(**q_data).exists()
    assert response.data
    assert response.data == {"detail": PermissionDenied.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__accepted__not_owner__with_policy__success(
    api_client,
    monkeypatch,
    cu_owner_fi,
    get_cu_fi,
    get_company_partnership_fi,
    get_project_fi,
    get_company_fi,
    role,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    project = get_project_fi(company=r_cu.company)
    cp = get_company_partnership_fi(
        inviting_company_user=r_cu, invited_company=get_company_fi(), **CPS_ING_AND_ED_COMPANY_STATUS
    )
    q_data = {"project": project, "company_partnership": cp}
    assert not ProjectPartnership.objects.filter(**q_data).exists()
    data = {k: v.id for k, v in q_data.items()}
    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instances = ProjectPartnership.objects.filter(**q_data)
    assert created_instances.count() == 1
    assert response.data["id"] == created_instances.first().id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("cp_inviting_status", "cp_invited_status"),
    [(CPS.ACCEPT.value, CPS.INVITE.value), (CPS.ACCEPT.value, CPS.ACCEPT.value)],
)
def test__duplicates__return_same_result(
    api_client,
    monkeypatch,
    r_cu,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    cp_inviting_status,
    cp_invited_status,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    project = get_project_fi(company=r_cu.company)
    cp = get_company_partnership_fi(
        inviting_company_user=r_cu,
        inviting_company_status=cp_inviting_status,
        invited_company_status=cp_invited_status,
    )
    q_data = {"project": project, "company_partnership": cp}
    status_data = {"inviting_company_status": PPS.ACCEPT.value, "invited_company_status": PPS.INVITE.value}
    get_project_partnership_fi(**q_data, **status_data)
    assert ProjectPartnership.objects.filter(**q_data).exists()
    data = {k: v.id for k, v in q_data.items()}
    response = __get_response(api_client, data=data, user=r_cu.user)
    assert ProjectPartnership.objects.filter(**q_data).count() == 1
    assert response.data["id"] == ProjectPartnership.objects.filter(**q_data).first().id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("pp_inviting_status", "pp_invited_status"),
    [(PPS.CANCEL.value, PPS.ACCEPT.value), (PPS.ACCEPT.value, PPS.CANCEL.value)],
)
def test__duplicates__with_cancel__return_new_result(
    api_client,
    monkeypatch,
    r_cu,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    pp_inviting_status,
    pp_invited_status,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    project = get_project_fi(company=r_cu.company)
    cp = get_company_partnership_fi(inviting_company_user=r_cu, **CPS_ING_AND_ED_COMPANY_STATUS)
    q_data = {"project": project, "company_partnership": cp}
    status_cancel_data = dict(
        inviting_company_status=pp_inviting_status, invited_company_status=pp_invited_status
    )
    get_project_partnership_fi(**q_data, **status_cancel_data)
    assert ProjectPartnership.objects.filter(**q_data, **status_cancel_data).count() == 1
    data = {k: v.id for k, v in q_data.items()}
    response = __get_response(api_client, data=data, user=r_cu.user)
    pps = ProjectPartnership.objects.filter(**q_data)
    assert pps.count() == 2
    created_instance = ProjectPartnership.objects.filter(
        **q_data, inviting_company_status=CPS.ACCEPT.value, invited_company_status=CPS.INVITE.value
    ).first()
    assert response.data["id"] == created_instance.id
