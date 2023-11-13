import json
import typing as tp
import functools
from copy import deepcopy

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_create, retrieve_response_instance
from accounts.models import USER_IS_BLOCKED, USER_IS_DELETED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from projects.models.project import PROJECT_IS_DELETED, NOT_TA_PROJECT_REASON, PROJECT_STATUS_MUST_BE_SETUP
from companies.models.company import COMPANY_IS_DELETED, NOT_TA_COMPANY_REASON
from ma_saas.constants.report import FIELD_SPEC_VALUES_TYPES, ProcessedReportFormFieldSpecKeys
from ma_saas.constants.system import TYPE, Callable
from ma_saas.constants.company import CUR, CUS, ROLES, NOT_OWNER_ROLES, NOT_ACCEPT_CUS_VALUES
from ma_saas.constants.project import NOT_SETUP_PROJECT_STATUS_VALUES, ProjectStatus
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_REASON, NOT_TA_RCU_MUST_BE_ACCEPT, CompanyUser
from projects.models.project_scheme import NOT_TA_PROJECT_SCHEME_REASON
from reports.models.processed_report_form import ProcessedReportForm
from tests.fixtures.processed_report_form import MEDIA1, MEDIA2, UNIQUE_TYPE_FIELDS, ALL_FIELDS_SPECS_LIST
from reports.validators.processed_report_form import (
    FIELD_SPEC_ERRORS,
    LOST_KEYS_REQUIRED,
    FIELD_TYPE_IS_INVALID,
    UNIQUE_FILED_TYPE_ERROR,
    FIELD_KEY_VALUE_TYPE_INVALID,
)

User = get_user_model()

INVALID_FIELD_DATA_TYPES = {str: 123, bool: "qwe", int: "qwe", list: "qwe"}

__get_response = functools.partial(request_response_create, path="/api/v1/processed-report-forms/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, {}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__acccpeted_owner__success(
    api_client, mock_policies_false, r_cu, get_project_fi, new_processed_report_form_data
):
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance_data = new_processed_report_form_data(project=project)
    response = __get_response(api_client, instance_data, r_cu.user)
    assert response.data["id"]


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS_VALUES)
def test__not_accepted_owner__fail(
    api_client,
    monkeypatch,
    get_cu_owner_fi,
    get_project_fi,
    new_processed_report_form_data,
    status,
):
    r_cu = get_cu_owner_fi(status=status)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance_data = new_processed_report_form_data(project=project)
    response = __get_response(api_client, instance_data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner_without_policy__fail(
    api_client,
    mock_policies_false,
    get_cu_fi,
    get_project_fi,
    new_processed_report_form_data,
    role,
):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance_data = new_processed_report_form_data(project=project)
    response = __get_response(api_client, instance_data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PermissionDenied.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__with_policy__success(
    api_client, monkeypatch, get_cu_fi, get_project_fi, new_processed_report_form_data, role
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu = get_cu_fi(role=role)
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    data = new_processed_report_form_data(project=project)
    response = __get_response(api_client, data, r_cu.user)
    assert response.data["id"]


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", CUS)
def test__user_from_different_company__with_policy__fail(
    api_client, monkeypatch, get_cu_fi, new_processed_report_form_data, role, status
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    r_cu = get_cu_fi(role=role, status=status.value)
    data = new_processed_report_form_data()
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(api_client, monkeypatch, r_cu, get_project_fi, new_processed_report_form_data):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    specs_fields = {1: MEDIA1}
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance_data = new_processed_report_form_data(project=project, fields_specs=specs_fields)
    response = __get_response(api_client, instance_data, r_cu.user)
    response_instance = response.data
    instance_data["fields_specs"] = json.loads(instance_data["fields_specs"])
    instance_id = response.data.pop("id")
    created_instance = ProcessedReportForm.objects.get(id=instance_id)
    if response_project_scheme := retrieve_response_instance(response_instance, "project_scheme", dict):
        assert created_instance.project_scheme.id == response_project_scheme.pop("id")
        assert created_instance.project_scheme.id == instance_data["project_scheme"]
    assert not response_project_scheme
    created_fields_specs = response_instance.pop("fields_specs")
    assert created_fields_specs
    assert created_fields_specs == created_instance.fields_specs
    assert response_instance.pop("created_at")
    assert response_instance.pop("updated_at")
    assert not response_instance


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("field_spec", [field for field in ALL_FIELDS_SPECS_LIST if field != MEDIA1])
def test__any_spec_fields__success(
    api_client,
    monkeypatch,
    r_cu,
    get_project_fi,
    new_processed_report_form_data,
    field_spec: tp.Dict[str, tp.Any],
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    # monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    media_field_id, field_spec_id = 1, 2
    fields_specs = {media_field_id: MEDIA1, field_spec_id: field_spec}
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance_data = new_processed_report_form_data(project=project, fields_specs=fields_specs)

    response = __get_response(api_client, instance_data, r_cu.user)
    instance_data["fields_specs"] = json.loads(instance_data["fields_specs"])
    instance_id = response.data.pop("id")
    created_instance = ProcessedReportForm.objects.get(id=instance_id)

    created_fields_specs = response.data.get("fields_specs")
    assert created_fields_specs
    assert created_fields_specs == created_instance.fields_specs
    assert len(created_fields_specs) == 2
    assert created_fields_specs.pop(f"{media_field_id}") == MEDIA1
    assert created_fields_specs.pop(f"{field_spec_id}") == field_spec
    assert not created_fields_specs


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__more_than_one_media_field__success(
    api_client, monkeypatch, r_cu, get_project_fi, new_processed_report_form_data
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    media_field_id1, media_field_id2 = 1, 2
    fields_specs = {media_field_id1: MEDIA1, media_field_id2: MEDIA2}

    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance_data = new_processed_report_form_data(project=project, fields_specs=fields_specs)
    response = __get_response(api_client, instance_data, r_cu.user)
    instance_data["fields_specs"] = json.loads(instance_data["fields_specs"])
    instance_id = response.data.pop("id")
    created_instance = ProcessedReportForm.objects.get(id=instance_id)

    created_fields_specs = response.data.get("fields_specs")
    assert created_fields_specs
    assert created_fields_specs == created_instance.fields_specs
    assert len(created_fields_specs) == 2
    created_media_field = created_fields_specs.pop(f"{media_field_id1}")
    assert created_media_field == MEDIA1
    created_field_spec = created_fields_specs.pop(f"{media_field_id2}")
    assert created_field_spec == MEDIA2
    assert not created_fields_specs


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("project_status", NOT_SETUP_PROJECT_STATUS_VALUES)
def test__not_setup_project__fail(
    api_client, monkeypatch, r_cu, new_processed_report_form_data, get_project_fi, project_status
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    project = get_project_fi(company=r_cu.company, status=project_status)
    instance_data = new_processed_report_form_data(project=project)
    response = __get_response(api_client, instance_data, r_cu.user, status_codes=ValidationError)
    assert response.data == {"project_scheme": [PROJECT_STATUS_MUST_BE_SETUP]}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("field_spec", ALL_FIELDS_SPECS_LIST)
@pytest.mark.parametrize("key", [key for key in ProcessedReportFormFieldSpecKeys.all_ if key != TYPE])
def test__invalid_value__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_project_fi,
    new_processed_report_form_data: Callable,
    field_spec: tp.Dict[str, any],
    key: str,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    spec_id = "1"
    fields_specs = {spec_id: deepcopy(field_spec)}
    fields_specs[spec_id][key] = INVALID_FIELD_DATA_TYPES[FIELD_SPEC_VALUES_TYPES[key]]

    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    data = new_processed_report_form_data(fields_specs=fields_specs, project=project)
    response = __get_response(api_client, data, r_cu.user, status_codes=ValidationError)

    field_name = fields_specs[spec_id].get(ProcessedReportFormFieldSpecKeys.NAME)
    reason = FIELD_KEY_VALUE_TYPE_INVALID.format(key=key)
    assert response.data == [
        FIELD_SPEC_ERRORS.format(
            spec_id=spec_id, field_name=field_name, spec_type=fields_specs[spec_id].get(TYPE), reason=reason
        )
    ]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("field_spec", ALL_FIELDS_SPECS_LIST)
def test__invalid_field_spec_type__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_project_fi,
    new_processed_report_form_data,
    field_spec: tp.Dict[str, any],
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    spec_id, invalid_field_type = "1", "qwe"
    fields_specs = {spec_id: deepcopy(field_spec)}
    fields_specs[spec_id][TYPE] = invalid_field_type
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    data = new_processed_report_form_data(project=project, fields_specs=fields_specs)
    response = __get_response(api_client, data, r_cu.user, status_codes=ValidationError)
    assert response.data[0] == FIELD_SPEC_ERRORS.format(
        spec_id=spec_id,
        field_name=fields_specs[spec_id].get(ProcessedReportFormFieldSpecKeys.NAME),
        spec_type=fields_specs[spec_id].get(TYPE),
        reason=FIELD_TYPE_IS_INVALID.format(field_type=invalid_field_type),
    )


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("field_spec", ALL_FIELDS_SPECS_LIST)
@pytest.mark.parametrize("key", ProcessedReportFormFieldSpecKeys.all_)
def test__lost_key__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_project_fi,
    new_processed_report_form_data: Callable,
    field_spec: tp.Dict[str, any],
    key: str,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    if key not in field_spec.keys():
        return
    spec_id = "1"
    fields_specs = {spec_id: deepcopy(field_spec)}
    fields_specs[spec_id].pop(key, None)
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    data = new_processed_report_form_data(project=project, fields_specs=fields_specs)
    response = __get_response(api_client, data, r_cu.user, status_codes=ValidationError)

    field_name = fields_specs[spec_id].get(ProcessedReportFormFieldSpecKeys.NAME)
    reason = LOST_KEYS_REQUIRED.format(missed_required_keys=[key])
    assert response.data == [
        FIELD_SPEC_ERRORS.format(
            spec_id=spec_id, field_name=field_name, spec_type=fields_specs[spec_id].get(TYPE), reason=reason
        )
    ]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("field_spec", UNIQUE_TYPE_FIELDS)
def test__creating_with_several_unique_fields__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_project_fi,
    new_processed_report_form_data: Callable,
    field_spec: tp.Dict[str, any],
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    fields_specs = {"1": field_spec, "2": field_spec}
    if fields_specs != MEDIA1:
        fields_specs[3] = MEDIA1
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    data = new_processed_report_form_data(project=project, fields_specs=fields_specs)
    response = __get_response(api_client, data, r_cu.user, status_codes=ValidationError)
    assert response.data[0] == UNIQUE_FILED_TYPE_ERROR.format(spec_type=field_spec[TYPE])


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("is_user", "field", "err_text"),
    (
        (True, "is_blocked", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_BLOCKED)),
        (True, "is_deleted", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_DELETED)),
        (False, "is_deleted", REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY),
    ),
)
def test__not_ta__cu__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_project_fi,
    new_processed_report_form_data,
    is_user,
    field,
    err_text,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    data = new_processed_report_form_data(project=project)
    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()
    else:
        setattr(r_cu, field, True)
        r_cu.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": err_text}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_company__fail(
    api_client, monkeypatch, r_cu, get_project_fi, new_processed_report_form_data
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    data = new_processed_report_form_data(project=project)
    r_cu.company.is_deleted = True
    r_cu.company.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": NOT_TA_RCU_REASON.format(reason=NOT_TA_COMPANY_REASON.format(reason=COMPANY_IS_DELETED))
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_project__fail(
    api_client, monkeypatch, r_cu, new_processed_report_form_data, get_project_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    data = new_processed_report_form_data(project=project)
    project.is_deleted = True
    project.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=ValidationError)
    assert response.data == {
        "project_scheme": [
            NOT_TA_PROJECT_SCHEME_REASON.format(
                reason=NOT_TA_PROJECT_REASON.format(reason=PROJECT_IS_DELETED)
            )
        ]
    }
