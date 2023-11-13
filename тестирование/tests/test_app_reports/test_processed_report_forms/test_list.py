import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated

from tests.utils import request_response_list, retrieve_response_instance
from tests.constants import ROLES_WITH_DIFFERENT_LOGIC
from ma_saas.constants.company import CUR, CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from clients.policies.interface import Policies
from tests.fixtures.processed_report_form import MEDIA1, MEDIA2

User = get_user_model()


__get_response = functools.partial(request_response_list, path="/api/v1/processed-report-forms/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


def test__user_without_companies_got_nothing(api_client, monkeypatch, user_fi: User):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    response = __get_response(api_client, user=user_fi)
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("qty", (1, 3))
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, get_processed_report_form_fi, qty):
    instances = [get_processed_report_form_fi(company=r_cu.company) for _ in range(qty)]
    instances.reverse()
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == qty
    for index, response_instance in enumerate(response.data):
        assert response_instance["id"] == instances[index].id


@pytest.mark.xfail
@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__with_policy__fail(
    api_client, monkeypatch, get_cu_fi, get_processed_report_form_fi, status
):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    get_processed_report_form_fi(company=r_cu.company)
    response = __get_response(api_client, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__without_policy__fail(
    api_client, monkeypatch, get_cu_fi, get_processed_report_form_fi, status
):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    get_processed_report_form_fi(company=r_cu.company)
    response = __get_response(api_client, r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__without_policy__fail(
    api_client, monkeypatch, get_cu_fi, get_processed_report_form_fi, role
):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    get_processed_report_form_fi(company=r_cu.company)
    response = __get_response(api_client, r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__with_policy__success(
    api_client, monkeypatch, get_cu_fi, get_processed_report_form_fi, role
):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    instance = get_processed_report_form_fi(company=r_cu.company)
    response = __get_response(api_client, r_cu.user)
    assert response.data[0]["id"] == instance.id


@pytest.mark.parametrize("role", ROLES_WITH_DIFFERENT_LOGIC)
@pytest.mark.parametrize("status", CUS)
@pytest.mark.parametrize("qty", (1, 3))
def test__different_company_user__fail(
    api_client, monkeypatch, get_cu_fi, get_processed_report_form_fi, role, status, qty
):
    r_cu = get_cu_fi(role=role, status=status.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    [get_processed_report_form_fi() for _ in range(qty)]
    response = __get_response(api_client, user=r_cu.user)
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__more_than_single_media_field(api_client, monkeypatch, r_cu, get_processed_report_form_fi):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    media_field_id1, media_field_id2 = "1", "2"
    fields_specs = {media_field_id1: MEDIA1, media_field_id2: MEDIA2}
    instances = [get_processed_report_form_fi(company=r_cu.company, fields_specs=fields_specs)]
    instances.reverse()

    response = __get_response(api_client, user=r_cu.user)
    for index, response_instance in enumerate(response.data):
        assert response_instance.pop("id") == instances[index].id
        if response_project_scheme := retrieve_response_instance(response_instance, "project_scheme", dict):
            assert response_project_scheme.pop("id") == instances[index].project_scheme.id
        assert not response_project_scheme
        assert response_instance.pop("created_at")
        assert response_instance.pop("updated_at")
        fields_specs = response_instance.pop("fields_specs")
        assert len(fields_specs) == len(instances[index].fields_specs)
        for field_id, field_data in fields_specs.items():
            for key, value in instances[index].fields_specs[field_id].items():
                assert field_data[key] == value
        assert not response_instance


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("qty", (3,))
def test__response_data(api_client, monkeypatch, r_cu, get_processed_report_form_fi, qty):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    instances = [get_processed_report_form_fi(company=r_cu.company) for _ in range(qty)]
    instances.reverse()
    response = __get_response(api_client, user=r_cu.user)
    for index, response_instance in enumerate(response.data):
        assert response_instance.pop("id") == instances[index].id
        if response_project_scheme := retrieve_response_instance(response_instance, "project_scheme", dict):
            assert response_project_scheme.pop("id") == instances[index].project_scheme.id
        assert not response_project_scheme
        assert response_instance.pop("created_at")
        assert response_instance.pop("updated_at")
        fields_specs = response_instance.pop("fields_specs")
        assert len(fields_specs) == len(instances[index].fields_specs)
        for field_id, field_data in fields_specs.items():
            for key, value in instances[index].fields_specs[field_id].items():
                assert field_data[key] == value
        assert not response_instance
