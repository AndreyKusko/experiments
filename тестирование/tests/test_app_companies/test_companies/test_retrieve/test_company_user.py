import pytest
from rest_framework.exceptions import NotFound, PermissionDenied

from ma_saas.constants.company import (
    CUR,
    ROLES,
    ACCEPT_OR_INVITE_CUS,
    NOT_ACCEPT_OR_INVITE_CUS,
    NOT_ACCEPT_OR_INVITE_CUS_VALUES,
)
from clients.policies.interface import Policies
from tests.test_app_companies.test_companies.test_retrieve.test_regular import __get_response


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", ACCEPT_OR_INVITE_CUS)
def test__related_to_company__any_accepted_or_invited_cu__success(
    monkeypatch, api_client, get_cu_fi, role, status
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    r_cu = get_cu_fi(role=role, status=status)
    response = __get_response(api_client, instance_id=r_cu.company.id, user=r_cu.user)
    assert response.data["id"] == r_cu.company.id


@pytest.mark.parametrize("status", NOT_ACCEPT_OR_INVITE_CUS)
def test__not_accepted(api_client, get_cu_fi, status):
    r_cu = get_cu_fi(status=status.value, role=CUR.OWNER)
    response = __get_response(api_client, r_cu.company.id, user=r_cu.user)
    assert response.data["id"] == r_cu.company.id
    # response = __get_response(api_client, r_cu.company.id, user=r_cu.user, status_codes=PermissionDenied)
    # assert response.data == {
    #     "detail": NOT_TA_r_cu_REASON.format(reason=CUS_MUST_BE_ACCEPT_OR_INVITE)
    # }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__company_user_foreign_company__fail(api_client, company_fi, r_cu):
    response = __get_response(api_client, company_fi.id, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}
