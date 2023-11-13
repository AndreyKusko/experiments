import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_update
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from ma_saas.constants.company import CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from ma_saas.constants.company import CompanyPartnershipStatus as CPS
from clients.policies.interface import Policies
from companies.models.company_partnership import CompanyPartnership
from companies.serializers.company_partnership import INVALID_COMPANY_PARTNERSHIP_STATUS_SEQUENCE

User = get_user_model()


__get_response = functools.partial(request_response_update, path="/api/v1/company-partnerships/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("company_partnership_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, {}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


def test__accepted_owner__success(
    api_client, mock_policies_false, get_cu_owner_fi, get_company_partnership_fi
):
    old_status, new_status = CPS.ACCEPT.value, CPS.CANCEL.value

    r_cu1 = get_cu_owner_fi(status=CUS.ACCEPT.value)
    instance1 = get_company_partnership_fi(invited_company=r_cu1.company, invited_company_status=old_status)

    data = {"invited_company_status": new_status}
    response1 = __get_response(api_client, instance1.id, data, user=r_cu1.user)
    assert response1.data["id"] == instance1.id
    updated_instance1 = CompanyPartnership.objects.get(id=instance1.id)
    assert response1.data["invited_company_status"] == new_status
    assert new_status == updated_instance1.invited_company_status
    assert instance1.invited_company_status != updated_instance1.invited_company_status
    assert instance1.inviting_company_status == updated_instance1.inviting_company_status
    assert instance1.inviting_company == updated_instance1.inviting_company
    assert instance1.invited_company == updated_instance1.invited_company

    r_cu2 = get_cu_owner_fi(status=CUS.ACCEPT.value)
    instance2 = get_company_partnership_fi(inviting_company_user=r_cu2, inviting_company_status=old_status)
    data = {"inviting_company_status": new_status}
    response2 = __get_response(api_client, instance2.id, data, user=r_cu2.user)
    assert response2.data["id"] == instance2.id
    updated_instance2 = CompanyPartnership.objects.get(id=instance2.id)
    assert response2.data["inviting_company_status"] == new_status
    assert new_status == updated_instance2.inviting_company_status
    assert instance2.inviting_company_status != updated_instance2.inviting_company_status
    assert instance2.invited_company_status == updated_instance2.invited_company_status
    assert instance2.inviting_company == updated_instance2.inviting_company
    assert instance2.invited_company == updated_instance2.invited_company


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__fail(api_client, mock_policies_false, get_cu_fi, role, get_company_partnership_fi):

    r_cu1 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    instance1 = get_company_partnership_fi(inviting_company_user=r_cu1)
    response1 = __get_response(api_client, instance1.id, data={}, user=r_cu1.user, status_codes=NotFound)
    assert response1.data["detail"] == NotFound.default_detail

    r_cu2 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    instance2 = get_company_partnership_fi(invited_company=r_cu2.company)
    response2 = __get_response(api_client, instance2.id, data={}, user=r_cu2.user, status_codes=NotFound)
    assert response2.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__with_policy__success(
    api_client, monkeypatch, get_cu_fi, role, get_company_partnership_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu1 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    instance1 = get_company_partnership_fi(
        inviting_company_user=r_cu1, inviting_company_status=CompanyPartnershipStatus.ACCEPT.value
    )
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [instance1.inviting_company.id])
    response1 = __get_response(
        api_client,
        instance1.id,
        user=r_cu1.user,
        data=dict(inviting_company_status=CompanyPartnershipStatus.CANCEL.value),
    )
    assert response1.data
    assert response1.data["id"] == instance1.id

    r_cu2 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    instance2 = get_company_partnership_fi(
        invited_company=r_cu2.company, invited_company_status=CompanyPartnershipStatus.ACCEPT.value
    )
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [instance2.invited_company.id])
    response2 = __get_response(
        api_client,
        instance2.id,
        data=dict(invited_company_status=CompanyPartnershipStatus.CANCEL.value),
        user=r_cu2.user,
    )
    assert response2.data
    assert response2.data["id"] == instance2.id


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__related_to_company__with_policy__success(
    api_client, monkeypatch, get_cu_fi, role, get_company_partnership_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu1 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    instance1 = get_company_partnership_fi(
        inviting_company_user=r_cu1, inviting_company_status=CompanyPartnershipStatus.ACCEPT.value
    )
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [instance1.inviting_company.id])
    response1 = __get_response(
        api_client,
        instance1.id,
        user=r_cu1.user,
        data=dict(inviting_company_status=CompanyPartnershipStatus.CANCEL.value),
    )
    assert response1.data
    assert response1.data["id"] == instance1.id

    r_cu2 = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    instance2 = get_company_partnership_fi(
        invited_company=r_cu2.company, invited_company_status=CompanyPartnershipStatus.ACCEPT.value
    )
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [instance2.invited_company.id])
    response2 = __get_response(
        api_client,
        instance2.id,
        user=r_cu2.user,
        data=dict(invited_company_status=CompanyPartnershipStatus.CANCEL.value),
    )
    assert response2.data
    assert response2.data["id"] == instance2.id


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__not_related_to_company__with_policy__fail(
    api_client, monkeypatch, get_cu_fi, role, get_company_partnership_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    instance = get_company_partnership_fi()
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [instance.inviting_company.id])
    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__fail(
    api_client, mock_policies_false, get_cu_owner_fi, status, get_company_partnership_fi
):
    r_cu1 = get_cu_owner_fi(status=status.value)
    instance1 = get_company_partnership_fi(inviting_company_user=r_cu1)
    response1 = __get_response(api_client, instance1.id, {}, user=r_cu1.user, status_codes=NotFound)
    assert response1.data == {"detail": NotFound.default_detail}

    r_cu2 = get_cu_owner_fi(status=status.value)
    instance2 = get_company_partnership_fi(invited_company=r_cu2.company)
    response2 = __get_response(api_client, instance2.id, {}, user=r_cu2.user, status_codes=NotFound)
    assert response2.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("invited_company_status", "inviting_company_status", "new_inviting_company_status"),
    [
        (CPS.INVITE.value, CPS.ACCEPT.value, CPS.ACCEPT.value),
        (CPS.INVITE.value, CPS.ACCEPT.value, CPS.CANCEL.value),
        (CPS.INVITE.value, CPS.CANCEL.value, CPS.CANCEL.value),
        (CPS.ACCEPT.value, CPS.ACCEPT.value, CPS.ACCEPT.value),
        (CPS.ACCEPT.value, CPS.ACCEPT.value, CPS.CANCEL.value),
        (CPS.ACCEPT.value, CPS.CANCEL.value, CPS.CANCEL.value),
        (CPS.CANCEL.value, CPS.ACCEPT.value, CPS.ACCEPT.value),
        (CPS.CANCEL.value, CPS.ACCEPT.value, CPS.CANCEL.value),
        (CPS.CANCEL.value, CPS.CANCEL.value, CPS.CANCEL.value),
    ],
)
def test__correct__convert__inviting_company_status__success(
    api_client,
    mock_policies_false,
    r_cu,
    get_company_partnership_fi,
    invited_company_status,
    inviting_company_status,
    new_inviting_company_status,
):
    instance = get_company_partnership_fi(
        inviting_company_user=r_cu,
        invited_company_status=invited_company_status,
        inviting_company_status=inviting_company_status,
    )
    assert instance.inviting_company_status == inviting_company_status
    assert instance.invited_company_status == invited_company_status

    data = {"inviting_company_status": new_inviting_company_status}
    response = __get_response(api_client, instance.id, data, user=r_cu.user)
    assert response.data["id"] == instance.id
    updated_instance = CompanyPartnership.objects.get(id=instance.id)
    assert response.data["inviting_company_status"] == new_inviting_company_status
    assert response.data["invited_company_status"] == invited_company_status
    assert invited_company_status == updated_instance.invited_company_status
    assert updated_instance.inviting_company_status == new_inviting_company_status


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("inviting_company_status", "invited_company_status", "new_invited_company_status"),
    [
        (CPS.INVITE.value, CPS.ACCEPT.value, CPS.ACCEPT.value),
        (CPS.INVITE.value, CPS.ACCEPT.value, CPS.CANCEL.value),
        (CPS.INVITE.value, CPS.CANCEL.value, CPS.CANCEL.value),
        (CPS.ACCEPT.value, CPS.ACCEPT.value, CPS.ACCEPT.value),
        (CPS.ACCEPT.value, CPS.ACCEPT.value, CPS.CANCEL.value),
        (CPS.ACCEPT.value, CPS.CANCEL.value, CPS.CANCEL.value),
        (CPS.CANCEL.value, CPS.ACCEPT.value, CPS.ACCEPT.value),
        (CPS.CANCEL.value, CPS.ACCEPT.value, CPS.CANCEL.value),
        (CPS.CANCEL.value, CPS.CANCEL.value, CPS.CANCEL.value),
    ],
)
def test__correct__convert__invited_company_status__success(
    api_client,
    mock_policies_false,
    r_cu,
    get_company_partnership_fi,
    invited_company_status,
    inviting_company_status,
    new_invited_company_status,
):
    instance = get_company_partnership_fi(
        invitied_company_user=r_cu,
        invited_company_status=invited_company_status,
        inviting_company_status=inviting_company_status,
    )
    assert instance.invited_company_status == invited_company_status
    assert instance.invited_company_status != new_invited_company_status
    assert instance.inviting_company_status == inviting_company_status
    data = {"invited_company_status": new_invited_company_status}
    response = __get_response(api_client, instance.id, data, user=r_cu.user)
    assert response.data["id"] == instance.id
    updated_instance = CompanyPartnership.objects.get(id=instance.id)
    assert response.data["inviting_company_status"] == inviting_company_status
    assert inviting_company_status == updated_instance.inviting_company_status

    assert response.data["invited_company_status"] == new_invited_company_status
    assert updated_instance.invited_company_status == new_invited_company_status
    assert updated_instance.invited_company_status != invited_company_status


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("invited_company_status", "inviting_company_status", "new_inviting_company_status"),
    [(CPS.ACCEPT.value, CPS.CANCEL.value, CPS.ACCEPT.value)],
)
def test__invalid__convert__inviting_company_status__fail(
    api_client,
    mock_policies_false,
    r_cu,
    get_company_partnership_fi,
    invited_company_status,
    inviting_company_status,
    new_inviting_company_status,
):
    instance = get_company_partnership_fi(
        inviting_company_user=r_cu,
        invited_company_status=invited_company_status,
        inviting_company_status=inviting_company_status,
    )
    assert instance.inviting_company_status == inviting_company_status
    assert instance.inviting_company_status != new_inviting_company_status
    assert instance.invited_company_status == invited_company_status
    data = {"inviting_company_status": new_inviting_company_status}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    assert response.data == [INVALID_COMPANY_PARTNERSHIP_STATUS_SEQUENCE]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("inviting_company_status", "invited_company_status", "new_invited_company_status"),
    [
        (CPS.INVITE.value, CPS.CANCEL.value, CPS.ACCEPT.value),
        (CPS.ACCEPT.value, CPS.CANCEL.value, CPS.ACCEPT.value),
        (CPS.CANCEL.value, CPS.CANCEL.value, CPS.ACCEPT.value),
    ],
)
def test__correct__convert__invited_company_status__success(
    api_client,
    mock_policies_false,
    r_cu,
    get_company_partnership_fi,
    invited_company_status,
    inviting_company_status,
    new_invited_company_status,
):
    instance = get_company_partnership_fi(
        invited_company=r_cu.company,
        invited_company_status=invited_company_status,
        inviting_company_status=inviting_company_status,
    )
    assert instance.invited_company_status == invited_company_status
    assert instance.invited_company_status != new_invited_company_status
    assert instance.inviting_company_status == inviting_company_status

    data = {"invited_company_status": new_invited_company_status}
    response = __get_response(api_client, instance.id, data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == [INVALID_COMPANY_PARTNERSHIP_STATUS_SEQUENCE]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("inviting_company_status", "invited_company_status", "new_invited_company_status"),
    [
        (CPS.INVITE.value, CPS.ACCEPT.value, CPS.INVITE.value),
        (CPS.INVITE.value, CPS.ACCEPT.value, CPS.CANCEL.value),
        (CPS.INVITE.value, CPS.INVITE.value, CPS.CANCEL.value),
        (CPS.INVITE.value, CPS.CANCEL.value, CPS.INVITE.value),
        (CPS.INVITE.value, CPS.CANCEL.value, CPS.ACCEPT.value),
        (CPS.ACCEPT.value, CPS.ACCEPT.value, CPS.INVITE.value),
        (CPS.ACCEPT.value, CPS.ACCEPT.value, CPS.CANCEL.value),
        (CPS.ACCEPT.value, CPS.INVITE.value, CPS.CANCEL.value),
        (CPS.ACCEPT.value, CPS.CANCEL.value, CPS.INVITE.value),
        (CPS.ACCEPT.value, CPS.CANCEL.value, CPS.ACCEPT.value),
        (CPS.CANCEL.value, CPS.ACCEPT.value, CPS.INVITE.value),
        (CPS.CANCEL.value, CPS.ACCEPT.value, CPS.CANCEL.value),
        (CPS.CANCEL.value, CPS.INVITE.value, CPS.CANCEL.value),
        (CPS.CANCEL.value, CPS.CANCEL.value, CPS.INVITE.value),
        (CPS.CANCEL.value, CPS.CANCEL.value, CPS.ACCEPT.value),
    ],
)
def test__update_invited_status_by__inviting_user__fail(
    api_client,
    mock_policies_false,
    r_cu,
    get_company_partnership_fi,
    inviting_company_status,
    invited_company_status,
    get_company_fi,
    new_invited_company_status,
):
    instance = get_company_partnership_fi(
        inviting_company_user=r_cu,
        invited_company=get_company_fi(),
        invited_company_status=invited_company_status,
        inviting_company_status=inviting_company_status,
    )
    assert instance.inviting_company_status == inviting_company_status
    assert instance.invited_company_status != new_invited_company_status
    assert instance.invited_company_status == invited_company_status
    data = {"invited_company_status": new_invited_company_status}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("inviting_company_status", "invited_company_status", "new_invited_company_status"),
    [(CPS.INVITE.value, CPS.ACCEPT.value, CPS.INVITE.value)],
)
def test__update_invited__if_no_invited_company__fail(
    api_client,
    mock_policies_false,
    r_cu,
    get_company_partnership_fi,
    inviting_company_status,
    invited_company_status,
    get_company_fi,
    new_invited_company_status,
):
    instance = get_company_partnership_fi(
        inviting_company_user=r_cu,
        invited_company_status=invited_company_status,
        inviting_company_status=inviting_company_status,
    )
    assert instance.inviting_company_status == inviting_company_status
    assert instance.invited_company_status != new_invited_company_status
    assert instance.invited_company_status == invited_company_status

    data = {"invited_company_status": new_invited_company_status}
    response = __get_response(api_client, instance.id, data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("inviting_company_status", "invited_company_status", "new_invited_company_status"),
    [
        (CPS.ACCEPT.value, CPS.CANCEL.value, CPS.ACCEPT.value),
        (CPS.ACCEPT.value, CPS.CANCEL.value, CPS.INVITE.value),
        (CPS.ACCEPT.value, CPS.ACCEPT.value, CPS.INVITE.value),
        (CPS.CANCEL.value, CPS.CANCEL.value, CPS.ACCEPT.value),
        (CPS.CANCEL.value, CPS.CANCEL.value, CPS.INVITE.value),
        (CPS.CANCEL.value, CPS.ACCEPT.value, CPS.INVITE.value),
    ],
)
def test__update_inviting_status_by__invited_user__fail(
    api_client,
    mock_policies_false,
    r_cu,
    get_company_partnership_fi,
    invited_company_status,
    inviting_company_status,
    new_invited_company_status,
):
    instance = get_company_partnership_fi(
        invited_company=r_cu.company,
        invited_company_status=invited_company_status,
        inviting_company_status=inviting_company_status,
    )
    assert instance.invited_company_status == invited_company_status
    assert instance.invited_company_status != new_invited_company_status
    assert instance.inviting_company_status == inviting_company_status
    data = {"invited_company_status": new_invited_company_status}
    response = __get_response(api_client, instance.id, data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == [INVALID_COMPANY_PARTNERSHIP_STATUS_SEQUENCE]


def test__response_data(
    api_client, mock_policies_false, get_company_partnership_fi, get_cu_owner_fi, get_company_fi
):
    r_cu0 = get_cu_owner_fi(status=CUS.ACCEPT.value)
    instances0 = get_company_partnership_fi(
        inviting_company_user=r_cu0, inviting_company_status=CompanyPartnershipStatus.ACCEPT.value
    )
    response0 = __get_response(
        api_client,
        instances0.id,
        user=r_cu0.user,
        data=dict(inviting_company_status=CompanyPartnershipStatus.CANCEL.value),
    )
    assert isinstance(response0.data, dict)
    assert len(response0.data) == 10
    assert response0.data["id"] == instances0.id
    assert response0.data["invited_company_user_email"]

    assert len(response0.data["invited_company"]) == 0

    assert len(response0.data["inviting_company"]) == 4
    assert response0.data["inviting_company"]["id"] == r_cu0.company.id
    assert response0.data["inviting_company"]["title"] == r_cu0.company.title
    assert response0.data["inviting_company"]["subdomain"] == r_cu0.company.subdomain
    assert response0.data["inviting_company"]["logo"] == r_cu0.company.logo
    assert len(response0.data["inviting_company_user"]) == 1
    assert response0.data["inviting_company_user"]["id"] == r_cu0.id
    assert response0.data["invited_company_status"] == instances0.invited_company_status
    assert response0.data["invited_project_partnership_qty_map"]
    assert response0.data["updated_at"]
    assert response0.data["created_at"]

    r_cu1 = get_cu_owner_fi(status=CUS.ACCEPT.value)
    instance1 = get_company_partnership_fi(inviting_company_user=r_cu1, invited_company=get_company_fi())
    response1 = __get_response(api_client, instance1.id, user=r_cu1.user, data={})
    assert isinstance(response1.data, dict)
    assert len(response1.data) == 10
    assert response1.data["id"] == instance1.id
    assert not response1.data["invited_company_user_email"]

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
    assert response1.data["invited_company_status"] == instance1.invited_company_status
    assert response1.data["invited_project_partnership_qty_map"]
    assert response1.data["updated_at"]
    assert response1.data["created_at"]

    r_cu2 = get_cu_owner_fi(status=CUS.ACCEPT.value)
    instance2 = get_company_partnership_fi(
        invited_company=r_cu2.company, invited_company_status=CompanyPartnershipStatus.ACCEPT.value
    )
    response2 = __get_response(
        api_client,
        instance2.id,
        user=r_cu2.user,
        data=dict(invited_company_status=CompanyPartnershipStatus.CANCEL.value),
    )
    assert isinstance(response2.data, dict)
    assert len(response2.data) == 10
    assert response2.data["id"] == instance2.id
    assert not response2.data["invited_company_user_email"]

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
    assert response2.data["invited_company_status"] == CompanyPartnershipStatus.CANCEL.value
    assert response2.data["invited_project_partnership_qty_map"]
    assert response2.data["updated_at"]
    assert response2.data["created_at"]
