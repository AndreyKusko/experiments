import typing as tp
from http.client import responses

import pytest
import requests
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.exceptions import NotAuthenticated

from tests.utils import get_authorization_token
from ma_saas.settings import REALM_ID
from tests.mocked_instances import MockResponse
from ma_saas.constants.company import CUS

User = get_user_model()


def __get_response(
    api_client,
    status_codes: int,
    params,
    user: tp.Optional[User] = None,
) -> Response:
    """Return response."""
    if user:
        api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user))
    response = api_client.get(f"/api/v1/documents/{params}")
    assert response.status_code == status_codes, f"response.data = {response.data}"
    assert response.status_text == responses[status_codes]

    return response


def test__anonymous_user__fail(api_client, user_fi: User):
    response = __get_response(api_client, status_codes=NotAuthenticated, params="")
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("file", [pytest.lazy_fixture("document__docx_file_fi")])
@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", CUS)
def test__any_authenticated_user__success(
    monkeypatch,
    api_client,
    docshub_multiple_documents_response_fi,
    get_cu_fi,
    file,
    role,
    status,
):
    r_cu = get_cu_fi(role=role, status=status.value)
    company = r_cu.company
    get_return_data = docshub_multiple_documents_response_fi(company_id=company.id)
    monkeypatch.setattr(requests, "get", lambda *a, **k: MockResponse(data=get_return_data))

    response = __get_response(
        api_client,
        user=r_cu.user,
        status_codes=status_code.HTTP_200_OK,
        params=f"?company={r_cu.company.id}",
    )
    print("response.data 0 =", dict(response.data[0]))
    print("response.data 1 =", dict(response.data[1]))
    assert response.data[0] == {
        "id": 75,
        "key": "testovoe_obschenie",
        "realm_id": REALM_ID,
        "company_id": company.id,
        "title": "Тестовое общение",
        "is_active": True,
        "description": "ы",
        "file_url": "https://docshub.millionagents.com/media/documents/75/%D0%91%D0%B5%D0%B7_%D0%BD%D0%B0%D0%B7%D0%B2%D0%B0%D0%BD%D0%B8%D1%8F.pdf",
        "version": 1,
        "is_accepted": False,
        "created_at": "2021-06-24T15:55:02.487789Z",
        "updated_at": "2021-06-24T15:55:02.495507Z",
    }
    assert response.data[1] == {
        "id": 69,
        "key": "testovoe_obschenie",
        "realm_id": REALM_ID,
        "company_id": company.id,
        "title": "Тестовое общение",
        "is_active": True,
        "description": "ы",
        "file_url": "https://docshub.millionagents.com/media/documents/75/%D0%91%D0%B5%D0%B7_%D0%BD%D0%B0%D0%B7%D0%B2%D0%B0%D0%BD%D0%B8%D1%8F.pdf",
        "version": 1,
        "is_accepted": False,
        "created_at": "2021-06-24T15:55:02.487789Z",
        "updated_at": "2021-06-24T15:55:02.495507Z",
    }
    # assert response.data == [
    #     {
    #         "id": 75,
    #         "key": "testovoe_obschenie",
    #         "realm_id": REALM_ID,
    #         "company_id": company.id,
    #         "title": "Тестовое общение",
    #         "description": "ы",
    #         "file_url": "https://docshub.millionagents.com/media/documents/75/%D0%91%D0%B5%D0%B7_%D0%BD%D0%B0%D0%B7%D0%B2%D0%B0%D0%BD%D0%B8%D1%8F.pdf",
    #         "version": 1,
    #         "is_accepted": False,
    #         "created_at": "2021-06-24T15:55:02.487789Z",
    #         "updated_at": "2021-06-24T15:55:02.495507Z",
    #     },
    #     {
    #         "id": 69,
    #         "key": "testovoe_obschenie",
    #         "realm_id": REALM_ID,
    #         "company_id": company.id,
    #         "title": "Тестовое общение",
    #         "description": "ы",
    #         "file_url": "https://docshub.millionagents.com/media/documents/75/%D0%91%D0%B5%D0%B7_%D0%BD%D0%B0%D0%B7%D0%B2%D0%B0%D0%BD%D0%B8%D1%8F.pdf",
    #         "version": 1,
    #         "is_accepted": False,
    #         "created_at": "2021-06-24T15:55:02.487789Z",
    #         "updated_at": "2021-06-24T15:55:02.495507Z",
    #     },
    # ]
