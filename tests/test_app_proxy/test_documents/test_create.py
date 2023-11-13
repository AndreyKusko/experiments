import typing as tp
from http.client import responses

import pytest
import requests
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import get_authorization_token
from tests.mocked_instances import MockResponse
from ma_saas.constants.system import Callable
from ma_saas.constants.company import CUS, NOT_OWNER_ROLES, NOT_ACCEPT_CUS_VALUES
from companies.models.company_user import NOT_TA_RCU_MUST_BE_ACCEPT, COMPANY_OWNER_ONLY_ALLOWED, CompanyUser

User = get_user_model()


def __get_response(
    api_client, data: tp.Dict[str, tp.Any], status_codes: int, user: tp.Optional[User] = None
) -> Response:
    """Return response."""
    if user:
        api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user))
    response = api_client.post("/api/v1/documents/", data=data)

    assert response.status_code == status_codes, f"response.data = {response.data}"
    assert response.status_text == responses[status_codes]
    return response


def test__anonymous__fail(api_client, get_user_fi, get_authorization_token_fi: Callable):
    response = __get_response(api_client, data={}, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture("document__docx_file_fi"),
        pytest.lazy_fixture("document__doc_file_fi"),
        pytest.lazy_fixture("document__pdf_file_fi"),
    ],
)
def test__response_data(
    monkeypatch, api_client, docshub_document_response_fi: Callable, r_cu: CompanyUser, file
):
    """Тестировать с разными типами файлов."""
    company = r_cu.company
    return_data = docshub_document_response_fi(company_id=company.id)
    monkeypatch.setattr(requests, "post", lambda *a, **k: MockResponse(data=return_data))

    file_txt_data = {"doc_type": "law", "title": "Тестовое соглашение", "description": "ы"}
    create_instance_data = {**file_txt_data, "company_id": company.id, "file": file}

    response = __get_response(
        api_client,
        data=create_instance_data,
        user=r_cu.user,
    )
    assert response.data == {
        "id": 75,
        "key": "testovoe_obschenie",
        "realm_id": 1,
        "company_id": company.id,
        "title": "Тестовое общение",
        "is_active": True,
        "description": "ы",
        "file_url": "https://docshub.millionagents.com/media/documents/75/%D0%91%D0%B5%D0%B7_%D0%BD%D0%B0%D0%B7%D0%B2%D0%B0%D0%BD%D0%B8%D1%8F.pdf",
        "version": 2,
        "is_accepted": False,
        "created_at": "2021-06-24T15:55:02.487789Z",
        "updated_at": "2021-06-24T15:55:02.495507Z",
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("file", [pytest.lazy_fixture("document__docx_file_fi")])
def test__accepted_owner__success(
    api_client, mock_policies_false, monkeypatch, docshub_document_response_fi, r_cu, file
):
    """Тестировать с разными типами файлов."""
    return_data = docshub_document_response_fi(company_id=r_cu.company.id)
    monkeypatch.setattr(requests, "post", lambda *a, **k: MockResponse(data=return_data))
    file_txt_data = {"doc_type": "law", "title": "Тестовое общение", "description": "ы"}
    create_instance_data = {**file_txt_data, "company_id": r_cu.company.id, "file": file}

    response = __get_response(api_client, data=create_instance_data, user=r_cu.user)
    assert response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("file", [pytest.lazy_fixture("document__docx_file_fi")])
def test__owner__system_file__fail(
    monkeypatch, api_client, docshub_document_response_fi: Callable, r_cu: CompanyUser, file
):
    """Тестировать с разными типами файлов."""
    file_txt_data = {"doc_type": "law", "title": "Тестовое общение", "description": "ы"}
    create_instance_data = {**file_txt_data, "company_id": 0, "file": file}

    response = __get_response(
        api_client, data=create_instance_data, user=r_cu.user, status_codes=PermissionDenied
    )
    assert response.data["detail"] == PermissionDenied.default_detail


@pytest.mark.parametrize("file", [pytest.lazy_fixture("document__docx_file_fi")])
@pytest.mark.parametrize("status", NOT_ACCEPT_CUS_VALUES)
def test__not_accepted_cu_owner__fail(monkeypatch, api_client, get_cu_owner_fi, file, status):
    r_cu = get_cu_owner_fi(status=status)
    file_txt_data = {"doc_type": "law", "title": "Тестовое общение", "description": "ы"}
    create_instance_data = {**file_txt_data, "company_id": r_cu.company.id, "file": file}

    response = __get_response(api_client, create_instance_data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("file", [pytest.lazy_fixture("document__docx_file_fi")])
@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__fail(monkeypatch, api_client, get_cu_fi, file, role):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)

    file_txt_data = {"doc_type": "law", "title": "Тестовое общение", "description": "ы"}
    create_instance_data = {**file_txt_data, "company_id": r_cu.company.id, "file": file}

    response = __get_response(
        api_client,
        data=create_instance_data,
        user=r_cu.user,
        status_codes=status_code.HTTP_403_FORBIDDEN,
    )
    assert response.data["detail"] == COMPANY_OWNER_ONLY_ALLOWED


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("file", [pytest.lazy_fixture("document__docx_file_fi")])
def test__duplicate_error(monkeypatch, api_client, r_cu: CompanyUser, file):
    """Тестировать с разными типами файлов."""

    return_data = [
        'IntegrityError duplicate key value violates unique constraint "hub_document_user_id_key_realm_id_company_id_e5d2d755_uniq"\nDETAIL:  Key (user_id, key, realm_id, company_id)=(2, testovoe_obschenie, 1, 2) already exists.\n'
    ]

    monkeypatch.setattr(
        requests,
        "post",
        lambda *a, **k: MockResponse(status_code=ValidationError.status_code, data=return_data),
    )
    file_txt_data = {"doc_type": "law", "title": "Тестовое общение", "description": "ы"}
    create_instance_data = {**file_txt_data, "company_id": r_cu.company.id, "file": file}

    response = __get_response(api_client, data=create_instance_data, user=r_cu.user)
    assert response.data == {"error": return_data}
