import json
import typing as tp
import functools
from copy import deepcopy

import pytest
from django.forms import model_to_dict
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, ValidationError, NotAuthenticated, PermissionDenied

import ma_saas.constants.report
import ma_saas.constants.system
from tests.utils import request_response_update, retrieve_response_instance
from projects.models.project import PROJECT_STATUS_MUST_BE_SETUP
from ma_saas.constants.report import (
    FIELD_SPEC_VALUES_TYPES,
    ProcessedReportFormFieldSpecKeys,
    ProcessedReportFormFieldSpecTypes,
)
from ma_saas.constants.system import TYPE
from ma_saas.constants.company import CUR, CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from ma_saas.constants.project import ProjectStatus
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_REASON, CUS_MUST_BE_ACCEPT, NOT_TA_RCU_MUST_BE_ACCEPT
from reports.models.processed_report_form import ProcessedReportForm
from tests.fixtures.processed_report_form import (
    STR2,
    MEDIA1,
    MEDIA2,
    UNIQUE_TYPE_FIELDS,
    ALL_FIELDS_SPECS_LIST,
)
from reports.validators.processed_report_form import (
    FIELD_SPEC_ERRORS,
    LOST_KEYS_REQUIRED,
    UNIQUE_FILED_TYPE_ERROR,
    FIELD_KEY_VALUE_TYPE_INVALID,
)
from reports.serializers.processed_report_form import (
    CHANGED_FIELDS,
    CHANGE_FIELDS_TYPES_FORBIDDEN,
    VALIDATION_ERROR_FORBIDDEN_TO_REMOVE_FIELDS_SPECS,
)
from tests.test_app_reports.test_processed_report_forms.test_create import INVALID_FIELD_DATA_TYPES

User = get_user_model()

__get_response = functools.partial(request_response_update, path="/api/v1/processed-report-forms/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("processed_report_form_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, {}, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(
    api_client, mock_policies_false, r_cu, get_project_fi, get_processed_report_form_fi
):
    project = get_project_fi(status=ProjectStatus.SETUP.value, company=r_cu.company)
    instance = get_processed_report_form_fi(project=project)
    response = __get_response(api_client, instance.id, {}, r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__without_policies__fail(
    api_client,
    mock_policies_false,
    get_cu_fi,
    get_processed_report_form_fi,
    get_project_fi,
    status,
):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    project = get_project_fi(status=ProjectStatus.SETUP.value, company=r_cu.company)
    instance = get_processed_report_form_fi(project=project)

    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__with_policies__fail(
    api_client, monkeypatch, get_cu_owner_fi, get_processed_report_form_fi, get_project_fi, status
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    r_cu = get_cu_owner_fi(status=status.value)
    project = get_project_fi(status=ProjectStatus.SETUP.value, company=r_cu.company)
    instance = get_processed_report_form_fi(project=project)

    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__without_policies__fail(
    api_client,
    mock_policies_false,
    get_cu_fi,
    get_project_fi,
    get_processed_report_form_fi,
    role,
):
    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)
    project = get_project_fi(status=ProjectStatus.SETUP.value, company=r_cu.company)
    instance = get_processed_report_form_fi(project=project)
    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__with_policy__success(
    api_client, monkeypatch, get_cu_fi, get_processed_report_form_fi, get_project_fi, role
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    project = get_project_fi(status=ProjectStatus.SETUP.value, company=r_cu.company)
    instance = get_processed_report_form_fi(project=project)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    response = __get_response(api_client, instance.id, {}, r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__user_from_different_company__fail(api_client, monkeypatch, r_cu, get_processed_report_form_fi):
    instance = get_processed_report_form_fi()

    company = instance.project_scheme.project.company

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    new_processed_report_form_data,
    get_project_fi,
    updated_processed_report_form_fields_specs_data_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance = get_processed_report_form_fi(project=project)

    fields_specs = updated_processed_report_form_fields_specs_data_fi(instance.fields_specs)
    instance_new_data = new_processed_report_form_data(fields_specs=fields_specs)
    del instance_new_data["project_scheme"]
    response = __get_response(api_client, instance.id, instance_new_data, r_cu.user)
    response_instance = response.data
    updated_instance = ProcessedReportForm.objects.get(id=instance.id)
    assert response_instance.pop("id") == instance.id == updated_instance.id
    if response_project_scheme := retrieve_response_instance(response_instance, "project_scheme", dict):
        assert instance.project_scheme.id == response_project_scheme.pop("id")
        assert instance.project_scheme.id == updated_instance.project_scheme.id
    assert not response_project_scheme
    assert response_instance.pop("created_at")
    assert response_instance.pop("updated_at")
    fields_specs = response_instance.pop("fields_specs")
    assert len(fields_specs) == len(instance.fields_specs)
    for field_id, field_data in fields_specs.items():
        for key, value in instance.fields_specs[field_id].items():
            assert field_data[key] == value
    assert not response_instance


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("project_status", [s.value for s in ProjectStatus if s != ProjectStatus.SETUP])
def test__not_setup_project__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    new_processed_report_form_data,
    updated_processed_report_form_fields_specs_data_fi,
    get_project_fi,
    project_status,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    project = get_project_fi(company=r_cu.company, status=project_status)
    instance = get_processed_report_form_fi(project=project)
    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=ValidationError)
    assert response.data["non_field_errors"][0] == PROJECT_STATUS_MUST_BE_SETUP


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__add_field_spec__success(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    get_project_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    project = get_project_fi(status=ProjectStatus.SETUP.value, company=r_cu.company)
    instance = get_processed_report_form_fi(project=project, fields_specs={1: MEDIA1})
    retrieve_max_field_spec_id = max(instance.fields_specs.keys())
    new_field_spec_id = str(int(retrieve_max_field_spec_id) + 1)
    new_field_spec = {new_field_spec_id: STR2}
    data = {"fields_specs": json.dumps({**instance.fields_specs, **new_field_spec})}
    response = __get_response(api_client, instance.id, data, r_cu.user)
    updated_instance = ProcessedReportForm.objects.get(id=instance.id)
    assert updated_instance.fields_specs[new_field_spec_id] == STR2
    assert response.data["fields_specs"][new_field_spec_id] == STR2


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__totally_remove_filed_spec__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    get_project_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    deleted_field_spec_id = "2"
    instance_fields_specs = {"1": MEDIA1, deleted_field_spec_id: STR2}
    project = get_project_fi(status=ProjectStatus.SETUP.value, company=r_cu.company)
    instance = get_processed_report_form_fi(project=project, fields_specs=instance_fields_specs)
    data = {"fields_specs": json.dumps({1: MEDIA1})}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    assert response.data == {
        "fields_specs": [VALIDATION_ERROR_FORBIDDEN_TO_REMOVE_FIELDS_SPECS.format(set(deleted_field_spec_id))]
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("field", [field for field in ALL_FIELDS_SPECS_LIST if field != MEDIA1])
def test__all_fields_specs_update__success(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    field: tp.Dict[str, tp.Any],
    updated_processed_report_form_fields_specs_data_fi,
    get_project_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    fields_specs = {"2": field}

    project = get_project_fi(status=ProjectStatus.SETUP.value, company=r_cu.company)
    __fd_processed_report_form = dict(project=project, fields_specs=fields_specs)
    instance = get_processed_report_form_fi(**__fd_processed_report_form)

    new_field_specs = updated_processed_report_form_fields_specs_data_fi(fields_specs)
    data = {"fields_specs": json.dumps(new_field_specs)}
    response = __get_response(api_client, instance.id, data, r_cu.user)
    updated_instance = ProcessedReportForm.objects.get(id=instance.id)
    for field_id, field_data in new_field_specs.items():
        for key, value in field_data.items():
            assert value == updated_instance.fields_specs[field_id][key]
            assert value == response.data["fields_specs"][field_id][key]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("field", [field for field in ALL_FIELDS_SPECS_LIST if field != MEDIA1])
def test__more_than_single_media_field__success(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    field: tp.Dict[str, tp.Any],
    updated_processed_report_form_fields_specs_data_fi,
    get_project_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    media_field_id1, media_field_id2 = "1", "3"
    fields_specs = {media_field_id1: MEDIA1, "2": field}

    project = get_project_fi(status=ProjectStatus.SETUP.value, company=r_cu.company)
    __fd_processed_report_form = dict(project=project, fields_specs=fields_specs)
    instance: ProcessedReportForm = get_processed_report_form_fi(**__fd_processed_report_form)

    new_field_specs = instance.fields_specs
    new_field_specs[media_field_id2] = MEDIA2
    data = {"fields_specs": json.dumps(new_field_specs)}
    response = __get_response(api_client, instance.id, data, r_cu.user)
    updated_instance = ProcessedReportForm.objects.get(id=instance.id)
    for field_id, field_data in new_field_specs.items():
        for key, value in field_data.items():
            assert value == response.data["fields_specs"][field_id][key]
            assert value == updated_instance.fields_specs[field_id][key]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("field_spec", ALL_FIELDS_SPECS_LIST)
@pytest.mark.parametrize("key", ProcessedReportFormFieldSpecKeys.all_)
def test__field_spec_lost_key__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    get_project_fi,
    field_spec: tp.Dict[str, any],
    key: str,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    if key not in field_spec.keys():
        return
    instance_fields_specs = {"1": deepcopy(field_spec)}
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance = get_processed_report_form_fi(project=project, fields_specs=instance_fields_specs)
    field_id = "1"
    instance_fields_specs[field_id].pop(key, None)
    instance_fields_specs_dump = json.dumps(instance_fields_specs)
    data = {"fields_specs": instance_fields_specs_dump}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    field_type = instance_fields_specs[field_id].get(ma_saas.constants.system.TYPE)
    reason = LOST_KEYS_REQUIRED.format(missed_required_keys=[key])

    assert response.data == [
        FIELD_SPEC_ERRORS.format(
            spec_id=field_id,
            field_name=instance_fields_specs[field_id].get(ProcessedReportFormFieldSpecKeys.NAME),
            spec_type=field_type,
            reason=reason,
        )
    ]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("field_spec", ALL_FIELDS_SPECS_LIST)
@pytest.mark.parametrize(
    "key", [key for key in ProcessedReportFormFieldSpecKeys.all_ if key != ma_saas.constants.system.TYPE]
)
def test__invalid_field_spec_value__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    get_project_fi,
    field_spec: tp.Dict[str, any],
    key: str,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance_fields_specs = {"1": deepcopy(field_spec)}

    project = get_project_fi(status=ProjectStatus.SETUP.value, company=r_cu.company)
    instance = get_processed_report_form_fi(project=project, fields_specs=instance_fields_specs)
    field_id = "1"
    instance_fields_specs[field_id][key] = INVALID_FIELD_DATA_TYPES[FIELD_SPEC_VALUES_TYPES[key]]
    instance_fields_specs_dump = json.dumps(instance_fields_specs)
    data = {"fields_specs": instance_fields_specs_dump}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    assert response.data == [
        FIELD_SPEC_ERRORS.format(
            spec_id=field_id,
            field_name=instance_fields_specs[field_id].get(ProcessedReportFormFieldSpecKeys.NAME),
            spec_type=field_spec[ma_saas.constants.system.TYPE],
            reason=FIELD_KEY_VALUE_TYPE_INVALID.format(key=key),
        )
    ], f"response.data = {response.data}"


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__change_field_spec_type__fail(
    api_client, monkeypatch, r_cu, get_processed_report_form_fi, get_project_fi
):
    """
    Проверить, что менять псевдотипы спецификаций полей запрещено.
    В некоторой степени повторяет тест test_lost_key_or_invalid_field_spec_value__forbidden.

    Только тут провряется на правильных данных.
    """
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    project = get_project_fi(status=ProjectStatus.SETUP.value, company=r_cu.company)
    field_id = "1"
    instance = get_processed_report_form_fi(project=project, fields_specs={field_id: MEDIA1})
    fields_spec_data = instance.fields_specs[field_id]
    old_type = instance.fields_specs[field_id][ma_saas.constants.system.TYPE]
    new_field_spec = ProcessedReportFormFieldSpecTypes.STR
    fields_spec_data["type"] = new_field_spec
    new_fields = json.dumps({field_id: fields_spec_data})
    data = {"fields_specs": new_fields}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    assert response.data == {
        "fields_specs": [
            CHANGE_FIELDS_TYPES_FORBIDDEN.format(
                data=CHANGED_FIELDS.format(spec_id=field_id, old_type=old_type, new_type=new_field_spec)
            )
        ]
    }, f"response.data = {response.data}"


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__duplicates__success(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    new_processed_report_form_data,
    get_project_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    duplicate_instance = get_processed_report_form_fi(project=project)
    instance = get_processed_report_form_fi(project_scheme=duplicate_instance.project_scheme)

    instance_new_data = new_processed_report_form_data(
        project_scheme=duplicate_instance.project_scheme, fields_specs=duplicate_instance.fields_specs
    )
    del instance_new_data["project_scheme"]
    response = __get_response(api_client, instance.id, instance_new_data, r_cu.user)
    updated_instance_data = model_to_dict(ProcessedReportForm.objects.get(id=instance.id))
    assert (
        instance.project_scheme.id
        == duplicate_instance.project_scheme.id
        == response.data["project_scheme"]["id"]
        == updated_instance_data["project_scheme"]
    )

    for field_id, field_data in json.loads(instance_new_data["fields_specs"]).items():
        for key, value in field_data.items():
            assert (
                updated_instance_data["fields_specs"][field_id][key]
                == response.data["fields_specs"][field_id][key]
                == value
            )


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__restricted_field__not_updating(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    new_processed_report_form_data,
    get_project_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance = get_processed_report_form_fi(project=project)
    instance_new_data = new_processed_report_form_data(project_scheme=instance.project_scheme)
    response = __get_response(api_client, instance.id, instance_new_data, r_cu.user)
    updated_instance_data = ProcessedReportForm.objects.get(id=instance.id)
    assert (
        response.data["project_scheme"]["id"]
        == updated_instance_data.project_scheme.id
        == instance.project_scheme.id
    )


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("field_spec", UNIQUE_TYPE_FIELDS)
def test__with_several_unique_fields__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    get_project_fi,
    field_spec: tp.Dict[str, any],
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    fields_specs = {"1": field_spec}
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance = get_processed_report_form_fi(project=project, fields_specs=fields_specs)
    data = {"fields_specs": json.dumps({**fields_specs, "3": field_spec})}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    assert response.data == [UNIQUE_FILED_TYPE_ERROR.format(spec_type=field_spec[TYPE])]
