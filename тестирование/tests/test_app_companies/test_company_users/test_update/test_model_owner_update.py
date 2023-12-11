import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, PermissionDenied

from tests.utils import request_response_update, retrieve_response_instance
from tests.constants import ROLES_WITH_DIFFERENT_LOGIC
from ma_saas.constants.company import CUS, ROLES
from companies.models.company_user import CompanyUser
from clients.billing.interfaces.worker import WorkerBilling
from companies.permissions.company_user import CU_CAN_NOT_UPDATE_SELF_STATUS
from companies.serializers.company_user import (
    FOLLOW_STATUS_UPDATING_SEQUENCE,
    CHANGE_TO_INVITE_STATUS_FORBIDDEN,
)

User = get_user_model()

__get_response = functools.partial(request_response_update, path="/api/v1/company-users/")


def test__response_data(api_client, mock_policies_false, get_cu_fi, new_company_user_data):

    instance = get_cu_fi()
    r_cu = instance

    new_data = new_company_user_data(
        user=instance.user, company=instance.company, role=instance.role, status=instance.status
    )
    response = __get_response(api_client, instance.id, new_data, r_cu.user)
    response_instance = response.data
    assert response_instance.pop("id") == instance.id

    if response_user := retrieve_response_instance(response_instance, "user", dict):
        assert response_user.pop("id") == instance.user.id
        assert response_user.pop("email") == instance.user.email
        assert response_user.pop("phone") == instance.user.phone
        assert response_user.pop("first_name") == instance.user.first_name
        assert response_user.pop("last_name") == instance.user.last_name
        assert response_user.pop("city") == instance.user.city
        assert response_user.pop("lat") == instance.user.lat
        assert response_user.pop("lon") == instance.user.lon
        assert response_user.pop("middle_name") == instance.user.middle_name
        assert response_user.pop("birthdate") == instance.user.birthdate
        assert response_user.pop("avatar") == "{}"
    assert not response_user

    if response_company := retrieve_response_instance(response_instance, "company", dict):
        assert response_company.pop("id") == instance.company.id
        assert response_company.pop("title") == instance.company.title
        assert response_company.pop("logo") == instance.company.logo
        assert response_company.pop("support_email") == instance.company.support_email
        assert response_company.pop("work_wo_inn") is None
    assert not response_company

    assert response_instance.pop("role") == instance.role
    assert response_instance.pop("status") == instance.status
    assert response_instance.pop("accepted_at")
    assert response_instance.pop("created_at")
    assert response_instance.pop("updated_at")

    assert not response_instance


@pytest.mark.parametrize("current_role", ROLES_WITH_DIFFERENT_LOGIC)
@pytest.mark.parametrize("target_role", ROLES_WITH_DIFFERENT_LOGIC)
def test__role_update__fail(
    api_client,
    mock_policies_false,
    get_cu_fi,
    new_company_user_data,
    current_role,
    target_role,
):

    if current_role == target_role:
        return
    instance = get_cu_fi(role=current_role)
    new_data = new_company_user_data(
        company=instance.company, user=instance.user, role=target_role, status=instance.status
    )
    __get_response(api_client, instance.id, new_data, instance.user)

    updated_instance = CompanyUser.objects.get(id=instance.id)
    assert updated_instance.role == instance.role


@pytest.mark.parametrize(
    ("current_status", "target_status"),
    [
        (CUS.INVITE, CUS.INVITE),
        (CUS.INVITE, CUS.ACCEPT),
        (CUS.INVITE, CUS.REJECT),
        (CUS.REJECT, CUS.REJECT),
        (CUS.ACCEPT, CUS.ACCEPT),
        (CUS.ACCEPT, CUS.QUIT),
        (CUS.CANCEL, CUS.CANCEL),
        (CUS.BLOCK, CUS.BLOCK),
        (CUS.QUIT, CUS.QUIT),
    ],
)
@pytest.mark.parametrize("role", ROLES)
def test__allowed_status_updating_sequence__success(
    api_client,
    monkeypatch,
    mock_policies_false,
    get_cu_fi,
    role,
    current_status,
    target_status,
):
    monkeypatch.setattr(WorkerBilling, "create_u2_account", lambda *args, **kwargs: None)
    monkeypatch.setattr(WorkerBilling, "create_u1_account", lambda *args, **kwargs: None)
    monkeypatch.setattr(CompanyUser, "deactivate_policies", lambda *a, **kw: None)

    instance = get_cu_fi(role=role, status=current_status.value)
    assert instance.status == current_status.value
    response = __get_response(api_client, instance.id, {"status": target_status.value}, user=instance.user)
    updated_instance = CompanyUser.objects.get(id=instance.id)
    assert updated_instance.status == response.data["status"] == target_status.value


@pytest.mark.parametrize(
    ("current_status", "target_status"),
    [(CUS.REJECT, CUS.INVITE), (CUS.ACCEPT, CUS.INVITE), (CUS.CANCEL, CUS.INVITE), (CUS.QUIT, CUS.INVITE)],
)
@pytest.mark.parametrize("role", ROLES)
def test__convert_status_to_invite__fail(
    api_client, mock_policies_false, get_cu_fi, current_status, target_status, role
):
    f"""
    Проверить запрет использования статуса {CUS.INVITE.name}

    У овнера будет ошибка валидации и запрет использования эндпинта,
    у остальных пользователей - ошибка пермишена и запрет использования статуса.
    """

    instance = get_cu_fi(status=current_status.value, role=role)
    assert instance.status == current_status
    response = __get_response(
        api_client,
        instance.id,
        {"status": target_status.value},
        instance.user,
        status_codes={ValidationError.status_code, PermissionDenied.status_code},
    )
    updated_instance = CompanyUser.objects.get(id=instance.id)
    assert updated_instance.status == instance.status == current_status.value
    assert (
        response.data == {"detail": CU_CAN_NOT_UPDATE_SELF_STATUS}
        or response.data == CHANGE_TO_INVITE_STATUS_FORBIDDEN
        or response.data == [CHANGE_TO_INVITE_STATUS_FORBIDDEN]
        or response.data == {"detail": CHANGE_TO_INVITE_STATUS_FORBIDDEN}
    )


@pytest.mark.parametrize(
    ("current_status", "target_status"),
    [(CUS.INVITE, CUS.BLOCK), (CUS.INVITE, CUS.QUIT), (CUS.INVITE, CUS.CANCEL)]
    + [(CUS.REJECT, status) for status in CUS if status not in {CUS.REJECT, CUS.INVITE}]
    + [
        (CUS.ACCEPT, status)
        for status in CUS
        if status not in {CUS.ACCEPT, CUS.REJECT, CUS.QUIT, CUS.BLOCK, CUS.INVITE}
    ]
    + [(CUS.CANCEL, status) for status in CUS if status not in {CUS.CANCEL, CUS.REJECT, CUS.INVITE}]
    + [(CUS.BLOCK, status) for status in CUS if status not in {CUS.BLOCK, CUS.ACCEPT}]
    + [(CUS.QUIT, status) for status in CUS if status not in {CUS.QUIT, CUS.INVITE, CUS.INVITE}],
)
@pytest.mark.parametrize("role", ROLES)
def test__restricted_status_updating_sequence__fail(
    api_client, mock_policies_false, get_cu_fi, current_status, target_status, role
):
    instance = get_cu_fi(status=current_status.value, role=role)
    assert instance.status == current_status
    response = __get_response(
        api_client,
        instance.id,
        {"status": target_status.value},
        instance.user,
        status_codes={PermissionDenied.status_code, ValidationError.status_code},
    )
    updated_instance = CompanyUser.objects.get(id=instance.id)
    assert updated_instance.status == instance.status == current_status.value
    assert (
        response.data == {"detail": FOLLOW_STATUS_UPDATING_SEQUENCE}
        or response.data == {"detail": CU_CAN_NOT_UPDATE_SELF_STATUS}
        or response.data == [FOLLOW_STATUS_UPDATING_SEQUENCE]
        or response.data == [FOLLOW_STATUS_UPDATING_SEQUENCE]
    )


@pytest.mark.parametrize("current_role", ROLES)
@pytest.mark.parametrize("target_role", ROLES)
def test__self_update_role__fail(api_client, mock_policies_false, get_cu_fi, current_role, target_role):
    instance = get_cu_fi(status=CUS.ACCEPT.value, role=current_role)
    response = __get_response(api_client, instance.id, {"role": target_role}, instance.user)
    updated_instance = CompanyUser.objects.get(id=instance.id)
    assert instance.role == updated_instance.role == response.data["role"]
