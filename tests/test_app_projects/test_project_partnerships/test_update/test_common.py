import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from tests.utils import request_response_update, retrieve_response_instance
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from ma_saas.constants.company import CUR, CUS, CPS_ING_AND_ED_COMPANY_STATUS
from ma_saas.constants.project import PPS, PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES
from clients.policies.interface import Policies
from projects.models.project_partnership import ProjectPartnership

User = get_user_model()


__get_response = functools.partial(request_response_update, path="/api/v1/project-partnerships/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("company_partnership_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, {}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


def test__accepted_owners__success(
    api_client,
    mock_policies_false,
    get_cu_fi,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
):

    r_cu1 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    project1 = get_project_fi(company=r_cu1.company)
    cp1 = get_company_partnership_fi(inviting_company_user=r_cu1, **CPS_ING_AND_ED_COMPANY_STATUS)
    q_data1 = {"project": project1, "company_partnership": cp1}
    instance1 = get_project_partnership_fi(**q_data1, **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES)
    data1 = {"inviting_company_status": PPS.CANCEL.value}
    response1 = __get_response(api_client, instance1.id, data1, r_cu1.user)
    assert response1.data["id"] == instance1.id

    r_cu2 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    project2 = get_project_fi()
    cp2 = get_company_partnership_fi(
        invited_company=r_cu2.company, inviting_company=project2.company, **CPS_ING_AND_ED_COMPANY_STATUS
    )
    q_data2 = {"project": project2, "company_partnership": cp2}
    instance2 = get_project_partnership_fi(**q_data2, **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES)
    data2 = {"invited_company_status": PPS.CANCEL.value}
    response2 = __get_response(api_client, instance2.id, data2, r_cu2.user)
    assert response2.data["id"] == instance2.id


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

    pp_data1 = {"project": project1, "company_partnership": cp1}
    instance1 = get_project_partnership_fi(**pp_data1, **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES)
    response1 = __get_response(
        api_client, instance1.id, {"inviting_company_status": PPS.CANCEL.value}, r_cu1.user
    )
    response_instance1 = response1.data
    assert response_instance1.pop("id") == instance1.id
    if response_project1 := retrieve_response_instance(response_instance1, "project", dict):
        assert response_project1.pop("id") == instance1.project.id
        assert response_project1.pop("title") == instance1.project.title
        if response_company1 := retrieve_response_instance(response_project1, "company", dict):
            assert response_company1.pop("id") == instance1.project.company.id
            assert response_company1.pop("title") == instance1.project.company.title
            assert response_company1.pop("subdomain") == instance1.project.company.subdomain
            assert response_company1.pop("logo") == instance1.project.company.logo
            assert not response_company1
        assert not response_project1
    if response_inviting_company_user1 := retrieve_response_instance(
        response_instance1, "inviting_company_user", dict
    ):
        assert response_inviting_company_user1.pop("id") == instance1.inviting_company_user.id
        assert not response_inviting_company_user1
    assert response_instance1.pop("created_at")
    assert response_instance1.pop("updated_at")
    assert response_instance1.pop("invited_company_status") == PPS.ACCEPT.value
    assert response_instance1.pop("inviting_company_status") == PPS.CANCEL.value
    assert response_instance1.pop("company_partnership")["id"] == cp1.id
    assert response_instance1.pop("partner_company") is None
    assert not response_instance1

    r_cu2 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    cp2 = get_company_partnership_fi(invited_company=r_cu2.company, **CPS_ING_AND_ED_COMPANY_STATUS)
    project2 = get_project_fi(company=cp2.inviting_company)
    q_data2 = {"project": project2, "company_partnership": cp2}
    instance2 = get_project_partnership_fi(**q_data2, **PPS__INVITING_INVITE__AND__INVITED_ACCEPT__VALUES)
    response2 = __get_response(
        api_client, instance2.id, {"invited_company_status": PPS.CANCEL.value}, r_cu2.user
    )
    response_instance2 = response2.data
    assert response_instance2.pop("id") == instance2.id
    if response_project2 := retrieve_response_instance(response_instance2, "project", dict):
        assert response_project2.pop("id") == instance2.project.id
        assert response_project2.pop("title") == instance2.project.title
        if response_company2 := retrieve_response_instance(response_project2, "company", dict):
            assert response_company2.pop("id") == instance2.project.company.id
            assert response_company2.pop("title") == instance2.project.company.title
            assert response_company2.pop("subdomain") == instance2.project.company.subdomain
            assert response_company2.pop("logo") == instance2.project.company.logo
            assert not response_company2
        assert not response_project2
    if response_inviting_company_user2 := retrieve_response_instance(
        response_instance2, "inviting_company_user", dict
    ):
        assert response_inviting_company_user2.pop("id") == instance2.inviting_company_user.id
        assert not response_inviting_company_user2
    assert response_instance2.pop("created_at")
    assert response_instance2.pop("updated_at")
    assert response_instance2.pop("invited_company_status") == PPS.CANCEL.value
    assert response_instance2.pop("inviting_company_status") == PPS.INVITE.value
    assert response_instance2.pop("company_partnership")["id"] == cp2.id
    if response_partner_company2 := retrieve_response_instance(response_instance2, "partner_company", dict):
        assert response_partner_company2.pop("id") == cp2.invited_company.id
        assert response_partner_company2.pop("title") == cp2.invited_company.title
        assert not response_partner_company2
    assert not response_instance2


def test__update_invited_status__without__company_partnership__invited_company__fail(
    api_client,
    monkeypatch,
    get_cu_fi,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_company_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    old_ed_status, new_ed_status, ing_status = PPS.ACCEPT.value, PPS.CANCEL.value, PPS.ACCEPT.value
    r_cu1 = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    project1 = get_project_fi(company=r_cu1.company)
    cp1 = get_company_partnership_fi(inviting_company=r_cu1.company, **CPS_ING_AND_ED_COMPANY_STATUS)
    q_data1 = {"project": project1, "company_partnership": cp1}
    instance1 = get_project_partnership_fi(
        **q_data1, inviting_company_status=ing_status, invited_company_status=old_ed_status
    )
    assert instance1.invited_company_status == old_ed_status
    assert old_ed_status != new_ed_status

    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [project1.company.id])

    data = {"invited_company_status": new_ed_status}
    response1 = __get_response(api_client, instance1.id, data, user=r_cu1.user, status_codes=PermissionDenied)
    assert response1.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}
    updated_instance = ProjectPartnership.objects.get(id=instance1.id)
    assert updated_instance.invited_company_status == old_ed_status
