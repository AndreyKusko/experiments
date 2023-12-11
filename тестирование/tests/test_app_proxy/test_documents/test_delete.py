import functools

import pytest
import requests
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from tests.utils import request_response_delete
from tests.mocked_instances import MockResponse
from ma_saas.constants.company import NOT_OWNER_ROLES, NOT_ACCEPT_CUS_VALUES
from companies.models.company_user import NOT_TA_RCU_MUST_BE_ACCEPT, COMPANY_OWNER_ONLY_ALLOWED
from companies.permissions.company_user import REQUESTING_USER_NOT_BELONG_TO_COMPANY

User = get_user_model()


__get_response = functools.partial(request_response_delete, path="/api/v1/documents/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("project_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codess={NotAuthenticated.status_code})
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(
    api_client, mock_policies_false, monkeypatch, r_cu, docshub_single_documents_response_fi
):
    company = r_cu.company
    get_return_data = docshub_single_documents_response_fi(company_id=company.id)
    monkeypatch.setattr(requests, "get", lambda *a, **k: MockResponse(data=get_return_data))
    _mocked_response = MockResponse(status_code=status_code.HTTP_204_NO_CONTENT)
    monkeypatch.setattr(requests, "delete", lambda *a, **k: _mocked_response)

    response = __get_response(api_client, instance_id=1, user=r_cu.user)
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__system_file__fail(monkeypatch, api_client, r_cu, docshub_single_documents_response_fi):
    get_return_data = docshub_single_documents_response_fi(company_id=0)
    monkeypatch.setattr(requests, "get", lambda *a, **k: MockResponse(data=get_return_data))

    response = __get_response(api_client, instance_id=1, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PermissionDenied.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__another__company__user__fail(
    monkeypatch, api_client, r_cu, docshub_single_documents_response_fi, get_company_fi
):
    company = get_company_fi()
    get_return_data = docshub_single_documents_response_fi(company_id=company.id)
    monkeypatch.setattr(requests, "get", lambda *a, **k: MockResponse(data=get_return_data))
    _mocked_response = MockResponse(status_code=status_code.HTTP_204_NO_CONTENT)
    monkeypatch.setattr(requests, "delete", lambda *a, **k: _mocked_response)

    response = __get_response(api_client, instance_id=1, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_COMPANY}


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS_VALUES)
def test__not_accepted_owner__fail(
    monkeypatch, api_client, docshub_single_documents_response_fi, get_cu_owner_fi, status
):
    r_cu = get_cu_owner_fi(status=status)
    return_data = docshub_single_documents_response_fi(company_id=r_cu.company.id)
    monkeypatch.setattr(requests, "get", lambda *a, **k: MockResponse(data=return_data))

    response = __get_response(api_client, instance_id=1, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__fail(
    monkeypatch,
    api_client,
    docshub_single_documents_response_fi,
    get_cu_fi,
    role,
):
    r_cu = get_cu_fi(role=role)
    return_data = docshub_single_documents_response_fi(company_id=r_cu.company.id)
    monkeypatch.setattr(requests, "get", lambda *a, **k: MockResponse(data=return_data))
    response = __get_response(api_client, instance_id=1, user=r_cu.user, status_codess=PermissionDenied)
    assert response.data["detail"] == COMPANY_OWNER_ONLY_ALLOWED
