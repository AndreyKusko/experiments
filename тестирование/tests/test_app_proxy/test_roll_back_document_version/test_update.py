import functools

import pytest
import requests
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated, PermissionDenied

from tests.utils import request_response_update
from tests.mocked_instances import MockResponse
from ma_saas.constants.system import Callable
from ma_saas.constants.company import CUR, NOT_OWNER_ROLES, NOT_ACCEPT_CUS_VALUES
from proxy.permissions.documents import DOCUMENT_NOT_FOUND
from companies.models.company_user import NOT_TA_RCU_MUST_BE_ACCEPT, COMPANY_OWNER_ONLY_ALLOWED, CompanyUser
from companies.permissions.company_user import REQUESTING_USER_NOT_BELONG_TO_COMPANY

User = get_user_model()


__get_response = functools.partial(request_response_update, path="/api/v1/roll-back-document-version/")


def test__anonymous__fail(api_client, get_user_fi, get_authorization_token_fi: Callable):
    response = __get_response(api_client, instance_id=1, data={}, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(
    monkeypatch,
    api_client,
    docshub_document_response_fi: Callable,
    docshub_single_documents_response_fi: Callable,
    r_cu: CompanyUser,
):
    get_return_data = docshub_single_documents_response_fi(company_id=r_cu.company.id, version=2)
    monkeypatch.setattr(requests, "get", lambda *a, **k: MockResponse(data=get_return_data))
    patch_return_data = docshub_document_response_fi(company_id=r_cu.company.id, version=1)
    monkeypatch.setattr(requests, "patch", lambda *a, **k: MockResponse(data=patch_return_data))

    response = __get_response(api_client, instance_id=1, data={}, user=r_cu.user)
    assert response.data == {
        "id": 75,
        "key": "testovoe_obschenie",
        "realm_id": 1,
        "company_id": r_cu.company.id,
        "title": "Тестовое общение",
        "is_active": True,
        "description": "ы",
        "file_url": "https://docshub.millionagents.com/media/documents/75/%D0%91%D0%B5%D0%B7_%D0%BD%D0%B0%D0%B7%D0%B2%D0%B0%D0%BD%D0%B8%D1%8F.pdf",
        "version": 1,
        "is_accepted": False,
        "created_at": "2021-06-24T15:55:02.487789Z",
        "updated_at": "2021-06-24T15:55:02.495507Z",
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(
    api_client,
    mock_policies_false,
    monkeypatch,
    docshub_document_response_fi: Callable,
    docshub_single_documents_response_fi: Callable,
    r_cu: CompanyUser,
):
    get_return_data = docshub_single_documents_response_fi(company_id=r_cu.company.id)
    monkeypatch.setattr(requests, "get", lambda *a, **k: MockResponse(data=get_return_data))
    patch_return_data = docshub_document_response_fi(company_id=r_cu.company.id, version=1)
    monkeypatch.setattr(requests, "patch", lambda *a, **k: MockResponse(data=patch_return_data))

    response = __get_response(
        api_client,
        instance_id=1,
        data={},
        user=r_cu.user,
        status_codes=status_code.HTTP_200_OK,
    )

    assert response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__document__fail(
    monkeypatch,
    api_client,
    r_cu,
):
    monkeypatch.setattr(requests, "get", lambda *a, **k: MockResponse(data=[]))

    response = __get_response(
        api_client,
        instance_id=1,
        data={},
        user=r_cu.user,
        status_codes=NotFound,
    )

    assert response.data["detail"] == DOCUMENT_NOT_FOUND


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__system_file__fail(
    monkeypatch,
    api_client,
    docshub_single_documents_response_fi: Callable,
    r_cu: CompanyUser,
):
    get_return_data = docshub_single_documents_response_fi(company_id=0)
    monkeypatch.setattr(requests, "get", lambda *a, **k: MockResponse(data=get_return_data))

    response = __get_response(
        api_client,
        instance_id=1,
        data={},
        user=r_cu.user,
        status_codes=status_code.HTTP_403_FORBIDDEN,
    )

    assert response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("file", [pytest.lazy_fixture("document__pdf_file_fi")])
def test__another_company_cu__fail(
    monkeypatch,
    api_client,
    r_cu: CompanyUser,
    docshub_single_documents_response_fi: Callable,
    get_company_fi,
    file,
):
    company = get_company_fi()
    return_data = docshub_single_documents_response_fi(company_id=company.id)
    monkeypatch.setattr(requests, "get", lambda *a, **k: MockResponse(data=return_data))

    response = __get_response(
        api_client,
        instance_id=1,
        data={},
        user=r_cu.user,
        status_codes=PermissionDenied,
    )

    assert response.data["detail"] == REQUESTING_USER_NOT_BELONG_TO_COMPANY


@pytest.mark.parametrize("file", [pytest.lazy_fixture("document__docx_file_fi")])
@pytest.mark.parametrize("status", NOT_ACCEPT_CUS_VALUES)
def test__not_accepted_owner__fail(
    monkeypatch,
    api_client,
    docshub_single_documents_response_fi,
    get_cu_owner_fi,
    file,
    status,
):
    r_cu = get_cu_owner_fi(status=status)
    return_data = docshub_single_documents_response_fi(company_id=r_cu.company.id)
    monkeypatch.setattr(requests, "get", lambda *a, **k: MockResponse(data=return_data))

    response = __get_response(api_client, 1, {}, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("file", [pytest.lazy_fixture("document__docx_file_fi")])
@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__fail(
    monkeypatch,
    api_client,
    docshub_single_documents_response_fi: Callable,
    get_cu_fi,
    file,
    role,
):
    r_cu = get_cu_fi(role=role)
    return_data = docshub_single_documents_response_fi(company_id=r_cu.company.id, version=2)
    monkeypatch.setattr(requests, "get", lambda *a, **k: MockResponse(data=return_data))

    response = __get_response(
        api_client,
        instance_id=1,
        data={},
        user=r_cu.user,
        status_codes=status_code.HTTP_403_FORBIDDEN,
    )
    assert response.data["detail"] == COMPANY_OWNER_ONLY_ALLOWED
