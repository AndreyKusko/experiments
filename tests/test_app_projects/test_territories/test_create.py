import functools
from copy import deepcopy

import pytest
from django.forms import model_to_dict
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_create
from accounts.models.users import (
    USER_IS_BLOCKED,
    USER_IS_DELETED,
    NOT_TA_USER_REASON,
    USER_EMAIL_NOT_VERIFIED,
)
from companies.models.company import COMPANY_IS_DELETED, NOT_TA_COMPANY_REASON, Company
from ma_saas.constants.system import Callable
from ma_saas.constants.company import CUR, CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from projects.models.territory import UNIQ_CONSTRAINT_ERR, Territory
from companies.models.company_user import (
    NOT_TA_RCU_REASON,
    NOT_TA_RCU_MUST_BE_ACCEPT,
    COMPANY_OWNER_ONLY_ALLOWED,
)
from companies.permissions.company_user import REQUESTING_USER_NOT_BELONG_TO_COMPANY

User = get_user_model()


__get_response = functools.partial(request_response_create, path="/api/v1/territories/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, {}, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(api_client, r_cu, new_territory_data: Callable):
    data = new_territory_data(company=r_cu.company)
    response = __get_response(api_client, data, r_cu.user)
    assert all(response.data[key] == value for key, value in data.items())
    new_instance = model_to_dict(Territory.objects.get(id=response.data["id"]))
    assert all(new_instance[key] == value for key, value in data.items())


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, new_territory_data: Callable):
    data = new_territory_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user)
    assert response.data


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__fail(api_client, get_cu_fi, new_territory_data, role):
    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)
    data = new_territory_data(company=r_cu.company)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data["detail"] == COMPANY_OWNER_ONLY_ALLOWED


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_cu__fail(api_client, get_cu_owner_fi, new_territory_data, status):
    r_cu = get_cu_owner_fi(status=status)
    data = new_territory_data(company=r_cu.company)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__not_existing_company__fail(api_client, r_cu, new_territory_data):
    data = new_territory_data(company=r_cu.company)
    data["inviting_company"] += 1
    response = __get_response(api_client, data, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_COMPANY}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__duplicates__fail(api_client, r_cu, new_territory_data, get_territory_fi):
    data = new_territory_data(company=r_cu.company)
    duplicate_data = deepcopy(data)
    duplicate_data["inviting_company"] = Company.objects.get(id=data["inviting_company"])
    duplicated_instance = get_territory_fi(**duplicate_data)
    response = __get_response(api_client, data, r_cu.user, status_codes=ValidationError)
    assert response.data == [
        UNIQ_CONSTRAINT_ERR.format(company=duplicated_instance.company.id, title=duplicated_instance.title)
    ]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_company__fail(api_client, r_cu, new_territory_data):
    r_cu.company.is_deleted = True
    r_cu.company.save()
    data = new_territory_data(company=r_cu.company)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": NOT_TA_RCU_REASON.format(reason=NOT_TA_COMPANY_REASON.format(reason=COMPANY_IS_DELETED))
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__foreign_company_cu__fail(api_client, company_fi, r_cu, new_territory_data):
    data = new_territory_data(company=company_fi)
    response = __get_response(api_client, data, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_COMPANY}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__blocked_user__fail(api_client, r_cu, new_territory_data):
    r_cu.user.is_blocked = True
    r_cu.user.save()
    data = new_territory_data(company=r_cu.company)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": NOT_TA_RCU_REASON.format(reason=NOT_TA_USER_REASON.format(reason=USER_IS_BLOCKED))
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_user__fail(api_client, r_cu, new_territory_data):
    r_cu.user.is_deleted = True
    r_cu.user.save()
    data = new_territory_data(company=r_cu.company)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": NOT_TA_RCU_REASON.format(reason=NOT_TA_USER_REASON.format(reason=USER_IS_DELETED))
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__not_verified_email__fail(api_client, r_cu, new_territory_data):
    r_cu.user.is_verified_email = False
    r_cu.user.save()
    data = new_territory_data(company=r_cu.company)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": NOT_TA_RCU_REASON.format(reason=NOT_TA_USER_REASON.format(reason=USER_EMAIL_NOT_VERIFIED))
    }
