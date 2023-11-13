import functools

import pytest
import requests
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from tests.utils import request_response_create
from tests.mocked_instances import MockResponse
from proxy.serializers.geocoder import GEOCODER_FORM_FIELD_REQUIRED
from companies.models.company_user import CompanyUser

User = get_user_model()

__get_response = functools.partial(request_response_create, path="/api/v1/geocoder/")


def test__anonymous_user__success(monkeypatch, api_client, search_by_non_format_field_data_fi_):
    non_format_address, geocoder_response, result = search_by_non_format_field_data_fi_
    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(data=geocoder_response))

    response = __get_response(api_client, data={"non_format_address": non_format_address})
    assert response.data == result


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__search_by_non_format_field__success(
    api_client, monkeypatch, r_cu, search_by_non_format_field_data_fi_
):
    non_format_address, geocoder_response, result = search_by_non_format_field_data_fi_
    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(data=geocoder_response))
    response = __get_response(api_client, data={"non_format_address": non_format_address}, user=r_cu.user)
    assert response.data == result


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__search_by_coordinates__success(api_client, monkeypatch, r_cu, search_by_coords_data_fi_):
    lat, lon, geocoder_response, result = search_by_coords_data_fi_
    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(data=geocoder_response))
    response = __get_response(api_client, data={"lat": lat, "lon": lon}, user=r_cu.user)
    assert response.data == result


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__search_by_city__success(api_client, monkeypatch, r_cu, search_by_city_data_fi_):
    city, geocoder_response, result = search_by_city_data_fi_
    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(data=geocoder_response))
    response = __get_response(api_client, data={"city": city}, user=r_cu.user)
    assert response.data == result


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__search_by_address__success(api_client, monkeypatch, r_cu, search_by_address_data_fi_):
    address, geocoder_response, result = search_by_address_data_fi_
    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(data=geocoder_response))
    response = __get_response(api_client, data={"address": address}, user=r_cu.user)
    assert response.data == result


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__only_one_coordinate__fail(api_client, monkeypatch, r_cu, search_by_coords_data_fi_):
    lat, lon, geocoder_response, result = search_by_coords_data_fi_
    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(data=geocoder_response))
    response = __get_response(api_client, {"lat": lat}, r_cu.user, status_codes=ValidationError)
    assert response.data[0] == GEOCODER_FORM_FIELD_REQUIRED
    response = __get_response(api_client, {"lon": lon}, r_cu.user, status_codes=ValidationError)
    assert response.data[0] == GEOCODER_FORM_FIELD_REQUIRED


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__no_data__fail(api_client, monkeypatch, r_cu: CompanyUser):
    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(data=""))
    response = __get_response(api_client, {}, r_cu.user, status_codes=ValidationError)
    assert response.data[0] == GEOCODER_FORM_FIELD_REQUIRED
