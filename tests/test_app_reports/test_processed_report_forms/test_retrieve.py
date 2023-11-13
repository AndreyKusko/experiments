import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated

from tests.utils import request_response_get, retrieve_response_instance
from ma_saas.constants.company import CUR, CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from clients.policies.interface import Policies
from tests.fixtures.processed_report_form import MEDIA1, MEDIA2

User = get_user_model()


__get_response = functools.partial(request_response_get, path="/api/v1/processed-report-forms/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("processed_report_form_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, get_processed_report_form_fi, r_cu):
    instance = get_processed_report_form_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.xfail
@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__with_policy__fail(
    api_client, monkeypatch, get_cu_fi, get_processed_report_form_fi, status
):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    instance = get_processed_report_form_fi(company=r_cu.company)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__without_policies__fail(
    api_client, mock_policies_false, get_cu_fi, get_processed_report_form_fi, role
):
    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)
    instance = get_processed_report_form_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__with_policies__success(
    api_client, monkeypatch, get_cu_fi, get_processed_report_form_fi, role
):
    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_processed_report_form_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__user_from_different_company__with_policy__fail(
    api_client, monkeypatch, r_cu, get_processed_report_form_fi
):
    instance = get_processed_report_form_fi()
    company = instance.project_scheme.project.company

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [company.id])

    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__more_than_single_media_field__success(api_client, monkeypatch, get_processed_report_form_fi, r_cu):

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    media_field_id1, media_field_id2 = "1", "2"
    fields_specs = {media_field_id1: MEDIA1, media_field_id2: MEDIA2}

    instance = get_processed_report_form_fi(company=r_cu.company, fields_specs=fields_specs)
    response = __get_response(api_client, instance.id, r_cu.user)
    response_instance = response.data
    assert response_instance["fields_specs"] == instance.fields_specs


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(api_client, monkeypatch, get_processed_report_form_fi, r_cu):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    instance = get_processed_report_form_fi(company=r_cu.company)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    response = __get_response(api_client, instance.id, r_cu.user)
    response_instance = response.data

    assert response_instance.pop("id") == instance.id

    if response_project_scheme := retrieve_response_instance(response_instance, "project_scheme", dict):
        assert response_project_scheme.pop("id") == instance.project_scheme.id
    assert not response_project_scheme

    assert response_instance.pop("created_at")
    assert response_instance.pop("updated_at")

    fields_specs = response_instance.pop("fields_specs")
    assert len(fields_specs) == len(instance.fields_specs)
    for field_id, field_data in fields_specs.items():
        for key, value in instance.fields_specs[field_id].items():
            assert field_data[key] == value

    assert not response_instance
