import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied

from tests.utils import retrieve_response_instance
from tests.constants import ROLES_WITH_DIFFERENT_LOGIC
from ma_saas.constants.company import CUR, CUS, ROLES, NOT_ACCEPT_CUS
from clients.policies.interface import Policies
from companies.models.company_user import CUS_MUST_BE_ACCEPT, NOT_TA_COMPANY_USER_REASON, CompanyUser
from companies.permissions.company_user import (
    CU_NOT_ALLOWED_TO_REQUESTED_ROLE,
    CU_NOT_ALLOWED_TO_REQUESTING_STATUS,
)
from companies.serializers.company_user import CHANGE_TO_INVITE_STATUS_FORBIDDEN
from tests.test_app_companies.test_company_users.test_update.test_model_owner_update import __get_response

User = get_user_model()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(api_client, monkeypatch, r_cu, get_cu_fi, new_company_user_data):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_cu_fi(company=r_cu.company, role=CUR.WORKER)
    new_data = new_company_user_data(status=instance.status)
    response = __get_response(api_client, instance.id, new_data, r_cu.user)
    response_instance = response.data
    assert response_instance.pop("id") == instance.id
    if response_user := retrieve_response_instance(response_instance, "user", dict):
        assert response_user.pop("id") == instance.user.id
        assert response_user.pop("email") == instance.user.email
        assert response_user.pop("phone") == instance.user.phone
        assert response_user.pop("first_name") == instance.user.first_name
        assert response_user.pop("last_name") == instance.user.last_name
        assert response_user.pop("middle_name") == instance.user.middle_name
        assert response_user.pop("birthdate") == instance.user.birthdate
        assert response_user.pop("city") == instance.user.city
        assert response_user.pop("lat") == instance.user.lat
        assert response_user.pop("lon") == instance.user.lon
        assert response_user.pop("avatar") == "{}"
    assert not response_user
    if response_company := retrieve_response_instance(response_instance, "company", dict):
        assert response_company.pop("id") == instance.company.id
        assert response_company.pop("title") == instance.company.title
        assert response_company.pop("logo") == instance.company.logo
        assert response_company.pop("support_email") == instance.company.support_email
        assert response_company.pop("work_wo_inn") is None
    assert not response_company
    assert response_instance.pop("role") == instance.role == new_data["role"]  # потому что роль не изменяется
    assert int(response_instance.pop("status")) == int(instance.status) == int(new_data["status"])
    assert response_instance.pop("accepted_at")
    assert response_instance.pop("created_at")
    assert response_instance.pop("updated_at")
    assert not response_instance


@pytest.mark.parametrize("current_role", ROLES_WITH_DIFFERENT_LOGIC)
@pytest.mark.parametrize("target_role", ROLES_WITH_DIFFERENT_LOGIC)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__role_updating__fail(api_client, monkeypatch, r_cu, get_cu_fi, current_role, target_role):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_cu_fi(company=r_cu.company, role=current_role)
    response = __get_response(api_client, instance.id, {"role": target_role}, r_cu.user)
    updated_instance = CompanyUser.objects.get(id=instance.id)
    assert response.data["role"] == updated_instance.role == current_role


@pytest.mark.parametrize(
    ("current_status", "target_status"),
    (
        (CUS.INVITE, CUS.INVITE),
        (CUS.INVITE, CUS.CANCEL),
        (CUS.REJECT, CUS.REJECT),
        (CUS.ACCEPT, CUS.ACCEPT),
        (CUS.ACCEPT, CUS.BLOCK),
        (CUS.CANCEL, CUS.CANCEL),
        (CUS.BLOCK, CUS.BLOCK),
        (CUS.QUIT, CUS.QUIT),
    ),
)
@pytest.mark.parametrize("role", [CUR.WORKER])
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__allowed_status_conversion_sequence__success(
    api_client, monkeypatch, get_cu_fi, new_company_user_data, r_cu, role, current_status, target_status
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    monkeypatch.setattr(CompanyUser, "deactivate_policies", lambda *a, **kw: None)

    instance = get_cu_fi(company=r_cu.company, status=current_status.value, role=role)
    assert instance.status == current_status.value
    new_data = new_company_user_data(
        user=instance.user, company=r_cu.company, role=role, status=target_status.value
    )
    response = __get_response(api_client, instance.id, new_data, r_cu.user)
    updated_instance = CompanyUser.objects.get(id=instance.id)
    assert response.data["status"] == updated_instance.status == target_status.value


@pytest.mark.parametrize(
    ("current_status", "target_status"),
    ((CUS.REJECT, CUS.INVITE), (CUS.CANCEL, CUS.INVITE), (CUS.QUIT, CUS.INVITE)),
)
@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__update_model_to_invite_status__fail(
    api_client, monkeypatch, r_cu, get_cu_fi, new_company_user_data, role, current_status, target_status
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    company = r_cu.company
    instance = get_cu_fi(company=company, status=current_status.value, role=role)
    data = new_company_user_data(
        user=instance.user, company=company, role=r_cu.role, status=target_status.value
    )
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    assert response.data == [CHANGE_TO_INVITE_STATUS_FORBIDDEN]


@pytest.mark.parametrize(
    ("current_status", "target_status"),
    [(CUS.INVITE, status) for status in CUS if status not in {CUS.INVITE, CUS.CANCEL, CUS.REMOVE}]
    + [(CUS.REJECT, status) for status in CUS if status not in {CUS.INVITE, CUS.REJECT, CUS.REMOVE}]
    + [(CUS.ACCEPT, status) for status in CUS if status not in {CUS.ACCEPT, CUS.BLOCK, CUS.REMOVE}]
    + [(CUS.CANCEL, status) for status in CUS if status not in {CUS.CANCEL, CUS.INVITE, CUS.REMOVE}]
    + [(CUS.BLOCK, status) for status in CUS if status not in {CUS.BLOCK, CUS.INVITE, CUS.REMOVE}]
    + [(CUS.QUIT, status) for status in CUS if status not in {CUS.QUIT, CUS.INVITE, CUS.REMOVE}],
)
@pytest.mark.parametrize("target_role", ROLES)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__forbidden_status_updating_sequence__fail(
    api_client,
    monkeypatch,
    get_cu_fi,
    new_company_user_data,
    r_cu,
    current_status,
    target_status,
    target_role,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    instance = get_cu_fi(company=r_cu.company, status=current_status.value, role=target_role)
    data = {"status": target_status.value}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=PermissionDenied)
    not_allowed_to_role = {"detail": CU_NOT_ALLOWED_TO_REQUESTED_ROLE}
    not_allowed_to_status = {"detail": CU_NOT_ALLOWED_TO_REQUESTING_STATUS}
    assert response.data == not_allowed_to_role or response.data == not_allowed_to_status


@pytest.mark.parametrize("requesting_role", [CUR.OWNER])
@pytest.mark.parametrize("target_role", [CUR.WORKER, CUR.OWNER, CUR.PROJECT_MANAGER])
def test__another_company__fail(api_client, monkeypatch, get_cu_fi, requesting_role, target_role):
    r_cu = get_cu_fi(role=requesting_role)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    instance = get_cu_fi(role=target_role)
    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("requesting_role", ROLES_WITH_DIFFERENT_LOGIC)
@pytest.mark.parametrize("requesting_status", NOT_ACCEPT_CUS)
def test__not_accepted_cu__fail(api_client, monkeypatch, get_cu_fi, requesting_role, requesting_status):
    r_cu = get_cu_fi(role=requesting_role, status=requesting_status.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    instance = get_cu_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_COMPANY_USER_REASON.format(reason=CUS_MUST_BE_ACCEPT)}
