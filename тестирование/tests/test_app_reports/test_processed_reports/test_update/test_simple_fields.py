import json
import typing as tp
from copy import deepcopy

import pytest
from rest_framework.exceptions import ValidationError

import ma_saas.constants.report
import ma_saas.constants.system
from ma_saas.constants.report import WorkerReportStatus, ProcessedReportFormFieldSpecKeys
from ma_saas.constants.system import Callable
from clients.policies.interface import Policies
from reports.models.processed_report import PROCESSED_REPORT_JSON_FIELDS_KEYS_INVALID, ProcessedReport
from tests.fixtures.processed_report_form import (
    INT1,
    INT2,
    STR1,
    STR2,
    FLOAT1,
    FLOAT2,
    MEDIA1,
    CHOICE1,
    CHOICE2,
    SELECT1,
    SELECT2,
    DATETIME1,
    DATETIME2,
    DATETIME3,
    DATETIME4,
    SIMPLE_REQUIRED_FIELDS,
    SIMPLE_NOT_REQUIRED_FIELDS,
)
from reports.validators.processed_report_model import (
    LESS_VALUES_REQUIRED,
    MORE_VALUES_REQUIRED,
    MISSED_FIELDS_IDS_REQUIRED,
    PROCESSED_REPORT_FIELD_ERROR,
)
from tests.test_app_reports.test_processed_reports.test_update.test_common import __get_response


@pytest.mark.parametrize(
    "field_spec",
    (STR1, INT1, FLOAT1, CHOICE1, DATETIME1, DATETIME2, DATETIME3, STR2, INT2, FLOAT2, CHOICE2, DATETIME4),
)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__not_select_field__success(
    api_client,
    monkeypatch,
    get_schedule_time_slot_fi,
    get_reservation_fi,
    get_worker_report_fi,
    get_processed_report_form_fi,
    get_processed_report_fi,
    generate_processed_report_field_fi,
    processed_report_media_field_fi,
    field_spec: tp.Dict[str, tp.Any],
    r_cu,
    get_project_territory_fi,
):
    pt = get_project_territory_fi(company=r_cu.company)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    schedule_time_slot = get_schedule_time_slot_fi(project_territory=pt)
    reservation = get_reservation_fi(schedule_time_slot=schedule_time_slot)
    worker_report = get_worker_report_fi(
        project_territory_worker=reservation.project_territory_worker,
        schedule_time_slot=schedule_time_slot,
        status=WorkerReportStatus.ACCEPTED.value,
    )
    __media_field_id = "1"
    fields_specs = {__media_field_id: MEDIA1, "2": field_spec}
    processed_report_form = get_processed_report_form_fi(project=pt.project, fields_specs=fields_specs)

    f_values = dict(field_spec=field_spec, values_qty=field_spec.get("min"))
    __media_field = {__media_field_id: processed_report_media_field_fi}
    json_fields = {**__media_field, "2": {"values": generate_processed_report_field_fi(**f_values)}}
    instance = get_processed_report_fi(
        company_user=r_cu,
        project_territory=pt,
        worker_report=worker_report,
        processed_report_form=processed_report_form,
        json_fields=json_fields,
    )
    new_json_fields = {**__media_field, "2": {"values": generate_processed_report_field_fi(**f_values)}}
    data = {"json_fields": json.dumps(new_json_fields)}

    response = __get_response(api_client, instance.id, data, r_cu.user)
    updated_instance = ProcessedReport.objects.get(id=instance.id)
    assert response.data["json_fields"]["2"] == new_json_fields["2"]
    assert updated_instance.json_fields["2"] == new_json_fields["2"]


@pytest.mark.parametrize("field_spec", (SELECT1, SELECT2))
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__select_field__success(
    api_client,
    monkeypatch,
    get_worker_report_fi: Callable,
    get_processed_report_form_fi: Callable,
    get_processed_report_fi,
    processed_report_media_field_fi,
    generate_processed_report_field_fi,
    get_schedule_time_slot_fi,
    get_reservation_fi,
    r_cu,
    get_project_territory_fi,
    field_spec: tp.Dict[str, tp.Any],
):
    pt = get_project_territory_fi(company=r_cu.company)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    sts = get_schedule_time_slot_fi(company=r_cu.company)
    reservation = get_reservation_fi(schedule_time_slot=sts)
    worker_report = get_worker_report_fi(
        project_territory_worker=reservation.project_territory_worker,
        schedule_time_slot=sts,
        status=WorkerReportStatus.ACCEPTED.value,
    )
    processed_report_form = get_processed_report_form_fi(
        project_scheme=sts.project_scheme, fields_specs={"1": MEDIA1, "2": field_spec}
    )
    field_id, __media_field = "2", {"1": processed_report_media_field_fi}
    f_values = dict(field_spec=field_spec, values_qty=field_spec.get("min"))
    instance_fields = {**__media_field, field_id: {"values": generate_processed_report_field_fi(**f_values)}}
    instance = get_processed_report_fi(
        company_user=r_cu,
        project_territory=pt,
        worker_report=worker_report,
        processed_report_form=processed_report_form,
        json_fields=instance_fields,
    )
    f_values = dict(field_spec=field_spec, values_qty=field_spec.get("min"))
    new_json_fields = {**__media_field, field_id: {"values": generate_processed_report_field_fi(**f_values)}}
    new_json_fields_dump = json.dumps(new_json_fields)
    data = {"json_fields": new_json_fields_dump}

    response = __get_response(api_client, instance.id, data, r_cu.user)
    updated_instance = ProcessedReport.objects.get(id=instance.id)
    assert response.data["json_fields"][field_id] == new_json_fields[field_id]
    assert updated_instance.json_fields[field_id] == new_json_fields[field_id]


@pytest.mark.parametrize("modify_qty", (-1, 1))
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__wrong_qty_select_field__fail(
    api_client,
    monkeypatch,
    get_processed_report_form_fi,
    generate_processed_report_field_fi,
    get_processed_report_fi,
    processed_report_media_field_fi,
    modify_qty,
    r_cu,
    get_project_territory_fi,
):
    prf_field = deepcopy(SELECT2)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    prf = get_processed_report_form_fi(project=pt.project, fields_specs={"1": MEDIA1, "2": prf_field})
    instance = get_processed_report_fi(company_user=r_cu, project_territory=pt, processed_report_form=prf)
    values_qty = prf_field["max"] + modify_qty if modify_qty > 0 else prf_field["min"] + modify_qty
    field_id = "2"
    mrf_values = generate_processed_report_field_fi(field_spec=prf_field, values_qty=values_qty)
    new_fields = {"1": processed_report_media_field_fi, field_id: {"values": mrf_values}}
    new_fields_dump = json.dumps(new_fields)
    data = {"json_fields": new_fields_dump}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    if modify_qty > 0:
        max_qty = prf_field[ProcessedReportFormFieldSpecKeys.MAX]
        error_reason = LESS_VALUES_REQUIRED.format(current_qty=values_qty, max_qty=max_qty)
    else:
        min_qty = prf_field[ProcessedReportFormFieldSpecKeys.MIN]
        error_reason = MORE_VALUES_REQUIRED.format(current_qty=values_qty, min_qty=min_qty)
    assert response.data == [
        PROCESSED_REPORT_FIELD_ERROR.format(
            field_id=field_id,
            type_=prf_field[ma_saas.constants.system.TYPE],
            name=prf_field[ProcessedReportFormFieldSpecKeys.NAME],
            reason=error_reason,
        )
    ]


@pytest.mark.parametrize("field_spec", SIMPLE_REQUIRED_FIELDS)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__without_simple_required_field__fails(
    api_client,
    monkeypatch,
    get_worker_report_fi,
    get_processed_report_form_fi,
    get_processed_report_fi,
    get_schedule_time_slot_fi,
    get_reservation_fi,
    processed_report_media_field_fi,
    generate_processed_report_field_fi,
    field_spec: tp.Dict[str, tp.Any],
    r_cu,
    get_project_territory_fi,
):

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    schedule_time_slot = get_schedule_time_slot_fi(company=r_cu.company)
    reservation = get_reservation_fi(schedule_time_slot=schedule_time_slot)

    worker_report = get_worker_report_fi(
        project_territory_worker=reservation.project_territory_worker,
        schedule_time_slot=schedule_time_slot,
        status=WorkerReportStatus.ACCEPTED.value,
    )
    prf = get_processed_report_form_fi(
        project_scheme=schedule_time_slot.project_scheme, fields_specs={"1": MEDIA1, "2": field_spec}
    )

    field_id, __media_field = "2", {"1": processed_report_media_field_fi}
    f_values = dict(field_spec=field_spec, values_qty=field_spec.get("min"))
    json_fields = {**__media_field, field_id: {"values": generate_processed_report_field_fi(**f_values)}}
    instance = get_processed_report_fi(
        company_user=r_cu,
        project_territory=pt,
        worker_report=worker_report,
        processed_report_form=prf,
        json_fields=json_fields,
    )
    new_fields_dump = json.dumps(__media_field)
    data = {"json_fields": new_fields_dump}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    assert response.data == [
        PROCESSED_REPORT_JSON_FIELDS_KEYS_INVALID.format(
            reason=MISSED_FIELDS_IDS_REQUIRED.format(missed_ids={field_id})
        )
    ]


@pytest.mark.parametrize("field_spec", SIMPLE_NOT_REQUIRED_FIELDS)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__without_simple_required_field__success(
    api_client,
    monkeypatch,
    get_worker_report_fi,
    get_schedule_time_slot_fi,
    get_reservation_fi,
    get_processed_report_form_fi: Callable,
    get_processed_report_fi,
    processed_report_media_field_fi,
    generate_processed_report_field_fi,
    field_spec: tp.Dict[str, tp.Any],
    r_cu,
    get_project_territory_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    sts = get_schedule_time_slot_fi(company=r_cu.company)
    reservation = get_reservation_fi(schedule_time_slot=sts)
    worker_report = get_worker_report_fi(
        project_territory_worker=reservation.project_territory_worker,
        schedule_time_slot=sts,
        status=WorkerReportStatus.ACCEPTED.value,
    )

    fields_specs = {"1": MEDIA1, "2": field_spec}
    prf = get_processed_report_form_fi(project_scheme=sts.project_scheme, fields_specs=fields_specs)
    __media_field = {"1": processed_report_media_field_fi}
    f_values = dict(field_spec=field_spec, values_qty=field_spec.get("min"))
    instance_json_fields = {**__media_field, "2": {"values": generate_processed_report_field_fi(**f_values)}}
    instance = get_processed_report_fi(
        company_user=r_cu,
        project_territory=pt,
        worker_report=worker_report,
        processed_report_form=prf,
        json_fields=instance_json_fields,
    )
    new_json_fields_dump = json.dumps(__media_field)
    data = {"json_fields": new_json_fields_dump}
    response = __get_response(api_client, instance.id, data, r_cu.user)

    updated_instance = ProcessedReport.objects.get(id=instance.id)
    assert not response.data["json_fields"].get("2")
    assert not updated_instance.json_fields.get("2")
