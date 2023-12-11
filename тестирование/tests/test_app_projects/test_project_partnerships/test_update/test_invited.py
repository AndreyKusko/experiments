import pytest
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied

from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from ma_saas.constants.company import CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES, CPS_ING_AND_ED_COMPANY_STATUS
from ma_saas.constants.project import PPS
from clients.policies.interface import Policies
from projects.models.project_partnership import ProjectPartnership
from projects.validators.project_partnership_serializer import FOLLOW_INVITED_STATUS_CHANGE_SEQUENCE
from tests.test_app_projects.test_project_partnerships.test_update.test_common import __get_response


@pytest.mark.parametrize(
    ("old_invited_status", "new_invited_status", "inviting_status"),
    [
        (PPS.ACCEPT.value, PPS.CANCEL.value, PPS.ACCEPT.value),
        (PPS.ACCEPT.value, PPS.CANCEL.value, PPS.CANCEL.value),
        (PPS.INVITE.value, PPS.CANCEL.value, PPS.ACCEPT.value),
        (PPS.INVITE.value, PPS.CANCEL.value, PPS.CANCEL.value),
        (PPS.INVITE.value, PPS.ACCEPT.value, PPS.ACCEPT.value),
        (PPS.INVITE.value, PPS.ACCEPT.value, PPS.CANCEL.value),
    ],
)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__update_invited_status__correct_sequence__success(
    api_client,
    mock_policies_false,
    r_cu,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    old_invited_status,
    new_invited_status,
    inviting_status,
):
    project = get_project_fi()
    cp1 = get_company_partnership_fi(
        inviting_company=project.company, invited_company=r_cu.company, **CPS_ING_AND_ED_COMPANY_STATUS
    )
    q_data1 = {"project": project, "company_partnership": cp1}
    instance1 = get_project_partnership_fi(
        **q_data1, inviting_company_status=inviting_status, invited_company_status=old_invited_status
    )
    assert instance1.invited_company_status == old_invited_status
    assert old_invited_status != new_invited_status
    data = {"invited_company_status": new_invited_status}
    response1 = __get_response(api_client, instance1.id, data, r_cu.user)
    updated_instance = ProjectPartnership.objects.get(id=instance1.id)
    assert response1.data["id"] == instance1.id
    assert response1.data["invited_company_status"] == new_invited_status
    assert response1.data["invited_company_status"] == updated_instance.invited_company_status


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accept__owner__fail(
    api_client,
    mock_policies_false,
    get_company_fi,
    get_cu_owner_fi,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    status,
):
    old_ed_status, new_ed_status, ing_status = PPS.ACCEPT.value, PPS.CANCEL.value, PPS.ACCEPT.value

    r_cu = get_cu_owner_fi(status=status.value)
    project1 = get_project_fi(company=r_cu.company)
    cp1 = get_company_partnership_fi(
        inviting_company=get_company_fi(), invited_company=r_cu.company, **CPS_ING_AND_ED_COMPANY_STATUS
    )
    q_data1 = {"project": project1, "company_partnership": cp1}
    instance1 = get_project_partnership_fi(
        **q_data1, inviting_company_status=ing_status, invited_company_status=old_ed_status
    )
    assert instance1.invited_company_status == old_ed_status
    assert old_ed_status != new_ed_status
    data = {"invited_company_status": new_ed_status}
    response1 = __get_response(api_client, instance1.id, data, r_cu.user, status_codes=NotFound)
    assert response1.data["detail"] == NotFound.default_detail
    updated_instance = ProjectPartnership.objects.get(id=instance1.id)
    assert updated_instance.invited_company_status == old_ed_status


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__without_policy__update_invited_status__correct_sequence__fail(
    api_client,
    mock_policies_false,
    get_cu_fi,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    role,
):
    old_ed_status, new_ed_status, ing_status = PPS.ACCEPT.value, PPS.CANCEL.value, PPS.ACCEPT.value

    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    project1 = get_project_fi()
    cp1 = get_company_partnership_fi(
        inviting_company=project1.company, invited_company=r_cu.company, **CPS_ING_AND_ED_COMPANY_STATUS
    )
    q_data1 = {"project": project1, "company_partnership": cp1}
    instance1 = get_project_partnership_fi(
        **q_data1, inviting_company_status=ing_status, invited_company_status=old_ed_status
    )
    assert instance1.invited_company_status == old_ed_status
    assert old_ed_status != new_ed_status
    data = {"invited_company_status": new_ed_status}
    response1 = __get_response(api_client, instance1.id, data, r_cu.user, status_codes=NotFound)
    updated_instance = ProjectPartnership.objects.get(id=instance1.id)
    assert response1.data["detail"] == NotFound.default_detail
    assert updated_instance.invited_company_status == old_ed_status


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__with_policy__update_invited_status__correct_sequence__success(
    api_client,
    monkeypatch,
    get_cu_fi,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_company_fi,
    role,
):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    old_ed_status, new_ed_status, ing_status = PPS.ACCEPT.value, PPS.CANCEL.value, PPS.ACCEPT.value
    project1 = get_project_fi()
    cp1 = get_company_partnership_fi(
        inviting_company=project1.company, invited_company=r_cu.company, **CPS_ING_AND_ED_COMPANY_STATUS
    )
    q_data1 = {"project": project1, "company_partnership": cp1}
    instance1 = get_project_partnership_fi(
        **q_data1, inviting_company_status=ing_status, invited_company_status=old_ed_status
    )

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [instance1.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    assert instance1.invited_company_status == old_ed_status
    assert old_ed_status != new_ed_status
    data = {"invited_company_status": new_ed_status}
    response1 = __get_response(api_client, instance_id=instance1.id, user=r_cu.user, data=data)
    assert response1.data["id"] == instance1.id
    updated_instance = ProjectPartnership.objects.get(id=instance1.id)
    assert updated_instance.invited_company_status == new_ed_status


@pytest.mark.parametrize("permission", ["pp_perm", "invited_company_perm", "company_partnership_perm"])
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__invited_company_perm__success(
    api_client,
    monkeypatch,
    r_cu,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_company_fi,
    permission,
):
    project = get_project_fi()
    cp = get_company_partnership_fi(
        inviting_company=project.company, invited_company=r_cu.company, **CPS_ING_AND_ED_COMPANY_STATUS
    )
    q_data1 = {"project": project, "company_partnership": cp}
    old_ed_status, new_ed_status, ing_status = PPS.ACCEPT.value, PPS.CANCEL.value, PPS.ACCEPT.value
    instance1 = get_project_partnership_fi(
        **q_data1, inviting_company_status=ing_status, invited_company_status=old_ed_status
    )
    assert instance1.invited_company_status == old_ed_status
    assert old_ed_status != new_ed_status
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    if permission == "pp_perm":
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [instance1.id])
    elif permission == "invited_company_perm":
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    elif permission == "company_partnership_perm":
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [cp.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    data = {"invited_company_status": new_ed_status}
    response1 = __get_response(api_client, instance_id=instance1.id, user=r_cu.user, data=data)
    assert response1.data["id"] == instance1.id
    updated_instance = ProjectPartnership.objects.get(id=instance1.id)
    assert updated_instance.invited_company_status == new_ed_status


@pytest.mark.parametrize("permission", ["project_perm", "inviting_company_perm"])
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__inviting_company_perm__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_company_fi,
    permission,
):
    project = get_project_fi()
    inviting_company = project.company
    cp1 = get_company_partnership_fi(
        inviting_company=inviting_company, invited_company=r_cu.company, **CPS_ING_AND_ED_COMPANY_STATUS
    )
    q_data1 = {"project": project, "company_partnership": cp1}
    old_ed_status, new_ed_status, ing_status = PPS.ACCEPT.value, PPS.CANCEL.value, PPS.ACCEPT.value
    instance = get_project_partnership_fi(
        **q_data1, inviting_company_status=ing_status, invited_company_status=old_ed_status
    )
    assert instance.invited_company_status == old_ed_status
    assert old_ed_status != new_ed_status

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    if permission == "project_perm":
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [project.id])
    elif permission == "inviting_company_perm":
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [inviting_company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    data = {"invited_company_status": new_ed_status}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize(
    ("old_invited_status", "new_invited_status", "inviting_status"),
    [
        (PPS.CANCEL.value, PPS.ACCEPT.value, PPS.ACCEPT.value),
        (PPS.CANCEL.value, PPS.INVITE.value, PPS.ACCEPT.value),
        (PPS.ACCEPT.value, PPS.INVITE.value, PPS.ACCEPT.value),
    ],
)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__update_invited_status__invalid_sequence__fail(
    api_client,
    mock_policies_false,
    r_cu,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    old_invited_status,
    new_invited_status,
    inviting_status,
):
    project = get_project_fi()
    cp = get_company_partnership_fi(
        invited_company=r_cu.company, inviting_company=project.company, **CPS_ING_AND_ED_COMPANY_STATUS
    )
    q_data1 = {"project": project, "company_partnership": cp}
    instance1 = get_project_partnership_fi(
        **q_data1, inviting_company_status=inviting_status, invited_company_status=old_invited_status
    )
    assert instance1.invited_company_status == old_invited_status
    assert old_invited_status != new_invited_status
    data = {"invited_company_status": new_invited_status}
    response = __get_response(api_client, instance1.id, data, r_cu.user, status_codes=ValidationError)
    assert response.data["non_field_errors"][0] == FOLLOW_INVITED_STATUS_CHANGE_SEQUENCE
    updated_instance = ProjectPartnership.objects.get(id=instance1.id)
    assert updated_instance.invited_company_status == old_invited_status


@pytest.mark.parametrize(
    ("old_invited_status", "new_invited_status", "inviting_status"),
    [
        (PPS.ACCEPT.value, PPS.CANCEL.value, PPS.ACCEPT.value),
        (PPS.ACCEPT.value, PPS.CANCEL.value, PPS.CANCEL.value),
        (PPS.INVITE.value, PPS.CANCEL.value, PPS.ACCEPT.value),
        (PPS.INVITE.value, PPS.CANCEL.value, PPS.CANCEL.value),
        (PPS.INVITE.value, PPS.ACCEPT.value, PPS.ACCEPT.value),
        (PPS.INVITE.value, PPS.ACCEPT.value, PPS.CANCEL.value),
    ],
)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__update_invited_status__by_inviting_company_user__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_company_fi,
    old_invited_status,
    new_invited_status,
    inviting_status,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    project1 = get_project_fi(company=r_cu.company)
    cp1 = get_company_partnership_fi(
        inviting_company=get_company_fi(), invited_company=project1.company, **CPS_ING_AND_ED_COMPANY_STATUS
    )
    q_data1 = {"project": project1, "company_partnership": cp1}
    instance1 = get_project_partnership_fi(
        **q_data1, inviting_company_status=inviting_status, invited_company_status=old_invited_status
    )
    assert instance1.invited_company_status == old_invited_status
    assert old_invited_status != new_invited_status
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [cp1.invited_company.id])
    data = {"invited_company_status": new_invited_status}
    response1 = __get_response(api_client, instance1.id, data, r_cu.user, status_codes=PermissionDenied)
    assert response1.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}
    updated_instance = ProjectPartnership.objects.get(id=instance1.id)
    assert updated_instance.invited_company_status == old_invited_status
