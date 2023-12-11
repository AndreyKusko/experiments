import json
import functools

import pytest
import requests
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied
from rest_framework.serializers import CharField

from tests.utils import request_response_create
from accounts.permissions import WORKER_ONLY_CAN_HAVE_INN
from proxy.serializers.inn import INN_MUST_BE_INTEGER
from tests.mocked_instances import MockResponse
from companies.models.company_user import CompanyUser

User = get_user_model()


__get_response = functools.partial(request_response_create, path="/api/v1/inn/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, {}, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_worker_fi")])
def test__worker__success(api_client, monkeypatch, r_cu):
    inn = "123456789201"
    mock_return = lambda *a, **kw: MockResponse(content=json.dumps({"inn": inn, "id": 1, "ext_id": 1}))
    monkeypatch.setattr(requests, "request", mock_return)
    response = __get_response(api_client, user=r_cu.user, data={"inn": inn})
    assert response.data["inn"] == inn


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__manager__fail(api_client, monkeypatch, r_cu):
    inn = "12345678901"
    mock_return = lambda *a, **kw: MockResponse(content=json.dumps({"inn": inn, "id": 1, "ext_id": 1}))
    monkeypatch.setattr(requests, "post", mock_return)
    response = __get_response(api_client, {"inn": inn}, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": WORKER_ONLY_CAN_HAVE_INN}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_worker_fi")])
@pytest.mark.parametrize(
    ("inn", "err_txt"),
    [
        ("1", CharField.default_error_messages["min_length"].format(min_length=12)),
        ("1234567890121", CharField.default_error_messages["max_length"].format(max_length=12)),
        ("-12345678290", INN_MUST_BE_INTEGER),
        ("123456782abc", INN_MUST_BE_INTEGER),
        ("", CharField.default_error_messages["blank"]),
    ],
)
def test__invalid_inn__fail(api_client, monkeypatch, r_cu, inn: str, err_txt: str):
    mock_return = lambda *a, **kw: MockResponse(content=json.dumps({"inn": inn, "id": 1, "ext_id": 1}))
    monkeypatch.setattr(requests, "request", mock_return)
    response = __get_response(api_client, user=r_cu.user, data={"inn": inn}, status_codes=ValidationError)
    assert response.data["inn"][0] == err_txt
