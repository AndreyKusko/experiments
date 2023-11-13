import pytest
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied

from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from ma_saas.constants.company import CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES, CPS_ING_AND_ED_COMPANY_STATUS
from ma_saas.constants.project import PPS
from clients.policies.interface import Policies
from projects.models.project_partnership import ProjectPartnership
from projects.validators.project_partnership_serializer import FOLLOW_INVITING_STATUS_CHANGE_SEQUENCE
from tests.test_app_projects.test_project_partnerships.test_update.test_common import __get_response


@pytest.mark.parametrize(
    ("old_inviting_status", "new_inviting_status", "invited_status"),
    [
        (PPS.ACCEPT, PPS.CANCEL, PPS.INVITE),
        (PPS.ACCEPT, PPS.CANCEL, PPS.ACCEPT),
        (PPS.ACCEPT, PPS.CANCEL, PPS.CANCEL),
    ],
)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__update_inviting_company_status__correct_sequence__success(
    api_client,
    mock_policies_false,
    r_cu,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    old_inviting_status,
    new_inviting_status,
    invited_status,
):
    project = get_project_fi(company=r_cu.company)
    cp = get_company_partnership_fi(inviting_company_user=r_cu, **CPS_ING_AND_ED_COMPANY_STATUS)
    pp_data = {"project": project, "company_partnership": cp}
    instance = get_project_partnership_fi(
        **pp_data,
        inviting_company_status=old_inviting_status.value,
        invited_company_status=invited_status.value
    )
    assert instance.inviting_company_status == old_inviting_status
    assert old_inviting_status != new_inviting_status
    data = {"inviting_company_status": new_inviting_status.value}
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user, data=data)
    updated_instance = ProjectPartnership.objects.get(id=instance.id)
    assert response.data["id"] == instance.id
    assert response.data["inviting_company_status"] == new_inviting_status.value
    assert response.data["inviting_company_status"] == updated_instance.inviting_company_status


@pytest.mark.parametrize("permission", ["invited_company_perm"])
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__invited_company_perm__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_company_fi,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    permission,
):
    old_inviting_status, new_inviting_status = PPS.ACCEPT.value, PPS.CANCEL.value
    project = get_project_fi(company=r_cu.company)
    invited_company = get_company_fi()
    cp = get_company_partnership_fi(
        inviting_company=r_cu.company, invited_company=invited_company, **CPS_ING_AND_ED_COMPANY_STATUS
    )
    q_data1 = {"project": project, "company_partnership": cp}
    instance = get_project_partnership_fi(
        **q_data1, inviting_company_status=old_inviting_status, invited_company_status=PPS.ACCEPT.value
    )
    assert instance.inviting_company_status == old_inviting_status
    assert old_inviting_status != new_inviting_status

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    if permission == "invited_company_perm":
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [invited_company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    data = {"inviting_company_status": new_inviting_status}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize(
    "permission", ["project_perm", "pp_perm", "inviting_company_perm", "company_partnership_perm"]
)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__inviting_company_perm__success(
    api_client,
    monkeypatch,
    r_cu,
    get_company_fi,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    permission,
):
    old_inviting_status, new_inviting_status = PPS.ACCEPT.value, PPS.CANCEL.value
    project = get_project_fi(company=r_cu.company)
    inviting_company, invited_company = r_cu.company, get_company_fi()
    cp = get_company_partnership_fi(
        inviting_company=inviting_company, invited_company=invited_company, **CPS_ING_AND_ED_COMPANY_STATUS
    )
    pp_data = {"project": project, "company_partnership": cp}
    instance = get_project_partnership_fi(
        **pp_data, inviting_company_status=old_inviting_status, invited_company_status=PPS.ACCEPT.value
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

    data = {"inviting_company_status": new_inviting_status}
    response = __get_response(api_client, instance.id, data, r_cu.user)
    updated_instance = ProjectPartnership.objects.get(id=instance.id)
    assert response.data["id"] == instance.id
    assert response.data["inviting_company_status"] == new_inviting_status
    assert response.data["inviting_company_status"] == updated_instance.inviting_company_status


@pytest.mark.parametrize(
    ("old_inviting_status", "new_inviting_status", "invited_status"),
    [
        (PPS.CANCEL, PPS.ACCEPT, PPS.INVITE),
        (PPS.CANCEL, PPS.ACCEPT, PPS.ACCEPT),
        (PPS.CANCEL, PPS.ACCEPT, PPS.CANCEL),
    ],
)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__update_inviting_company_status__invalid_sequence__fail(
    api_client,
    mock_policies_false,
    r_cu,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    old_inviting_status,
    new_inviting_status,
    invited_status,
):
    project1 = get_project_fi(company=r_cu.company)
    cp = get_company_partnership_fi(inviting_company_user=r_cu, **CPS_ING_AND_ED_COMPANY_STATUS)
    pp_data = {"project": project1, "company_partnership": cp}
    instance = get_project_partnership_fi(
        **pp_data,
        inviting_company_status=old_inviting_status.value,
        invited_company_status=invited_status.value
    )
    assert instance.inviting_company_status == old_inviting_status
    assert old_inviting_status != new_inviting_status
    data = {"inviting_company_status": new_inviting_status.value}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    updated_instance = ProjectPartnership.objects.get(id=instance.id)
    assert updated_instance.inviting_company_status == old_inviting_status
    assert response.data == {"non_field_errors": [FOLLOW_INVITING_STATUS_CHANGE_SEQUENCE]}


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__update_inviting_company_status__correct_sequence__fail(
    api_client,
    mock_policies_false,
    get_cu_owner_fi,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    status,
):
    old_inviting_status, new_inviting_status = PPS.ACCEPT.value, PPS.CANCEL.value
    invited_status = PPS.INVITE.value

    r_cu = get_cu_owner_fi(status=status.value)
    project = get_project_fi(company=r_cu.company)
    cp = get_company_partnership_fi(inviting_company_user=r_cu, **CPS_ING_AND_ED_COMPANY_STATUS)
    pp_data = {"project": project, "company_partnership": cp}
    instance1 = get_project_partnership_fi(
        **pp_data, inviting_company_status=old_inviting_status, invited_company_status=invited_status
    )
    assert instance1.inviting_company_status == old_inviting_status
    assert old_inviting_status != new_inviting_status
    data = {"inviting_company_status": new_inviting_status}
    response1 = __get_response(api_client, instance1.id, data, r_cu.user, status_codes=NotFound)
    assert response1.data == {"detail": NotFound.default_detail}
    updated_instance = ProjectPartnership.objects.get(id=instance1.id)
    assert updated_instance.inviting_company_status == instance1.inviting_company_status


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__update_inviting_company_status__correct_sequence__fail(
    api_client,
    mock_policies_false,
    get_cu_fi,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    role,
):
    old_inviting_status, new_inviting_status = PPS.ACCEPT.value, PPS.CANCEL.value
    invited_status = PPS.INVITE.value

    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    project = get_project_fi(company=r_cu.company)
    cp = get_company_partnership_fi(inviting_company_user=r_cu, **CPS_ING_AND_ED_COMPANY_STATUS)
    pp_data = {"project": project, "company_partnership": cp}
    instance = get_project_partnership_fi(
        **pp_data, inviting_company_status=old_inviting_status, invited_company_status=invited_status
    )
    assert instance.inviting_company_status == old_inviting_status
    assert old_inviting_status != new_inviting_status
    data = {"inviting_company_status": new_inviting_status}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}
    updated_instance = ProjectPartnership.objects.get(id=instance.id)
    assert updated_instance.inviting_company_status == instance.inviting_company_status


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__with_policy__update_inviting_company_status__correct_sequence__success(
    api_client,
    monkeypatch,
    get_cu_fi,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    role,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    old_inviting_status, new_inviting_status = PPS.ACCEPT.value, PPS.CANCEL.value
    invited_status = PPS.INVITE.value
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    project = get_project_fi(company=r_cu.company)
    cp = get_company_partnership_fi(inviting_company_user=r_cu, **CPS_ING_AND_ED_COMPANY_STATUS)
    pp_data = {"project": project, "company_partnership": cp}
    instance = get_project_partnership_fi(
        **pp_data, inviting_company_status=old_inviting_status, invited_company_status=invited_status
    )
    assert instance.inviting_company_status == old_inviting_status
    assert old_inviting_status != new_inviting_status
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    data = {"inviting_company_status": new_inviting_status}
    response = __get_response(api_client, instance.id, data, r_cu.user)
    updated_instance = ProjectPartnership.objects.get(id=instance.id)
    assert updated_instance.inviting_company_status == new_inviting_status
    assert response.data["inviting_company_status"] == new_inviting_status


@pytest.mark.parametrize(
    ("old_inviting_status", "new_inviting_status", "invited_status"),
    [
        (PPS.ACCEPT.value, PPS.CANCEL.value, PPS.INVITE.value),
        (PPS.ACCEPT.value, PPS.CANCEL.value, PPS.ACCEPT.value),
        (PPS.ACCEPT.value, PPS.CANCEL.value, PPS.CANCEL.value),
    ],
)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__update_inviting_company_status__by_invited_company_user__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    old_inviting_status,
    new_inviting_status,
    invited_status,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    project = get_project_fi()
    cp = get_company_partnership_fi(
        invited_company=r_cu.company, inviting_company=project.company, **CPS_ING_AND_ED_COMPANY_STATUS
    )
    pp_data = {"project": project, "company_partnership": cp}
    instance = get_project_partnership_fi(
        **pp_data, inviting_company_status=old_inviting_status, invited_company_status=invited_status
    )
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    assert instance.inviting_company_status == old_inviting_status
    assert old_inviting_status != new_inviting_status
    data = {"inviting_company_status": new_inviting_status}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}
    updated_instance = ProjectPartnership.objects.get(id=instance.id)
    assert updated_instance.inviting_company_status == old_inviting_status
