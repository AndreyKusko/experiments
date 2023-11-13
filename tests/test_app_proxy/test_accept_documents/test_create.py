import typing as tp
import functools
from http.client import responses

import pytest
import requests
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotAuthenticated

from tests.utils import get_authorization_token, request_response_create
from tests.mocked_instances import MockResponse
from ma_saas.constants.system import Callable
from ma_saas.constants.company import CUS, ROLES
from proxy.views.accept_documents import CU_NOT_BELONG_TO_DOCUMENTS_COMPANIES
from companies.models.company_user import CompanyUser

User = get_user_model()


__get_response = functools.partial(request_response_create, path="/api/v1/accept-documents/")


def test__anonymous__fail(api_client, get_user_fi, get_authorization_token_fi: Callable):
    response = __get_response(api_client, data={}, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(
    monkeypatch,
    api_client,
    docshub_multiple_documents_response_fi,
    docshub_accept_document_response_fi: Callable,
    r_cu,
):
    document_id = 1

    return_data = docshub_multiple_documents_response_fi(company_id=r_cu.company.id)
    monkeypatch.setattr(requests, "get", lambda *a, **k: MockResponse(data=return_data))
    response_data = docshub_accept_document_response_fi(user_id=r_cu.user.id, document_id=document_id)
    monkeypatch.setattr(requests, "post", lambda *a, **k: MockResponse(data=response_data))

    response = __get_response(api_client, data={"documents": [document_id]}, user=r_cu.user)
    assert response.data == [
        {
            "document": 75,
            "ext_user_id": r_cu.user.id,
            "version": 1,
            "created_at": "2021-06-25T11:05:00.180013Z",
        },
        {
            "document": 69,
            "ext_user_id": r_cu.user.id,
            "version": 1,
            "created_at": "2021-06-25T11:05:00.180013Z",
        },
    ]


@pytest.mark.parametrize("status", CUS)
@pytest.mark.parametrize("role", ROLES)
def test__any_cu_status_and_role__success(
    monkeypatch,
    api_client,
    docshub_multiple_documents_response_fi,
    docshub_accept_document_response_fi: Callable,
    get_cu_fi,
    status,
    role,
):
    r_cu = get_cu_fi(role=role, status=status.value)
    document_id = 1

    return_data = docshub_multiple_documents_response_fi(company_id=r_cu.company.id)
    monkeypatch.setattr(requests, "get", lambda *a, **k: MockResponse(data=return_data))
    response_data = docshub_accept_document_response_fi(user_id=r_cu.user.id, document_id=document_id)
    monkeypatch.setattr(requests, "post", lambda *a, **k: MockResponse(data=response_data))

    response = __get_response(api_client, {"documents": [document_id]}, r_cu.user)

    assert response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_worker_fi")])
def test__not_related_to_company__company_user__fail(
    monkeypatch,
    api_client,
    docshub_multiple_documents_response_fi,
    docshub_accept_document_response_fi: Callable,
    r_cu: CompanyUser,
):
    document_id = 1
    return_data = docshub_multiple_documents_response_fi(company_id=r_cu.company.id + 1)
    monkeypatch.setattr(requests, "get", lambda *a, **k: MockResponse(data=return_data))
    response_data = docshub_accept_document_response_fi(user_id=r_cu.user.id, document_id=document_id)
    monkeypatch.setattr(requests, "post", lambda *a, **k: MockResponse(data=response_data))

    response = __get_response(
        api_client, {"documents": [document_id]}, r_cu.user, status_codes=ValidationError
    )
    not_matched_documents = {d["id"] for d in return_data}

    assert response.data[0] in {
        CU_NOT_BELONG_TO_DOCUMENTS_COMPANIES.format(
            documents_ids=f"{', '.join(list(map(str, not_matched_documents)))}"
        ),
        CU_NOT_BELONG_TO_DOCUMENTS_COMPANIES.format(
            documents_ids=f"{', '.join(list(map(str, not_matched_documents))[::-1])}"
        ),
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__duplicate__fail(monkeypatch, api_client, docshub_multiple_documents_response_fi, r_cu):
    get_return_data = docshub_multiple_documents_response_fi(company_id=r_cu.company.id)
    monkeypatch.setattr(requests, "get", lambda *a, **k: MockResponse(data=get_return_data))
    post_response_data = {
        "non_field_errors": ["The fields ext_user_id, document, version must make a unique set."]
    }
    monkeypatch.setattr(
        requests,
        "post",
        lambda *a, **k: MockResponse(status_code=ValidationError.status_code, data=post_response_data),
    )

    response = __get_response(
        api_client,
        data={"documents": [69, 75]},
        user=r_cu.user,
        status_codes=status_code.HTTP_200_OK,
    )

    assert response.data == [
        {
            "document": 75,
            "error": {
                "non_field_errors": ["The fields ext_user_id, document, version must make a unique set."]
            },
        },
        {
            "document": 69,
            "error": {
                "non_field_errors": ["The fields ext_user_id, document, version must make a unique set."]
            },
        },
    ]
