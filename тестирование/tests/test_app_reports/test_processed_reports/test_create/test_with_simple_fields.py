import json
import typing as tp
from copy import deepcopy

import pytest
from django.forms import model_to_dict
from rest_framework.exceptions import ValidationError

import ma_saas.constants.report
import ma_saas.constants.system
from ma_saas.constants.report import WorkerReportStatus as WRS
from ma_saas.constants.report import ProcessedReportFormFieldSpecKeys
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
    CHECK_IN1,
    CHECK_IN2,
    DATETIME1,
    DATETIME2,
    DATETIME3,
    DATETIME4,
    GEO_POINT_NAME1,
    GEO_POINT_NAME2,
    GEO_POINT_ADDRESS1,
    GEO_POINT_ADDRESS2,
    SIMPLE_REQUIRED_FIELDS,
)
from reports.validators.processed_report_model import (
    LESS_VALUES_REQUIRED,
    MORE_VALUES_REQUIRED,
    MISSED_FIELDS_IDS_REQUIRED,
    PROCESSED_REPORT_FIELD_ERROR,
)
from tests.test_app_reports.test_processed_reports.test_create.test_common import __get_response


@pytest.mark.parametrize(
    "field_spec",
    (
        STR1,
        INT1,
        FLOAT1,
        CHOICE1,
        DATETIME1,
        DATETIME2,
        DATETIME3,
        STR2,
        INT2,
        FLOAT2,
        CHOICE2,
        DATETIME4,
        CHECK_IN1,
        CHECK_IN2,
        GEO_POINT_ADDRESS1,
        GEO_POINT_ADDRESS2,
        GEO_POINT_NAME1,
        GEO_POINT_NAME2,
    ),
)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__not_select_field__success(
    api_client,
    monkeypatch,
    r_cu,
    get_worker_report_fi,
    get_processed_report_form_fi,
    new_processed_report_data_fi,
    generate_processed_report_field_fi,
    processed_report_media_field_fi,
    get_project_territory_fi,
    field_spec: tp.Dict[str, tp.Any],
    get_schedule_time_slot_fi,
    get_reservation_fi,
):
    pt = get_project_territory_fi(company=r_cu.company)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    schedule_time_slot = get_schedule_time_slot_fi(project_territory=pt)
    reservation = get_reservation_fi(schedule_time_slot=schedule_time_slot)
    worker_report = get_worker_report_fi(
        project_territory_worker=reservation.project_territory_worker,
        schedule_time_slot=schedule_time_slot,
        status=WRS.ACCEPTED.value,
    )

    media_field_id = "1"
    fields_specs = {media_field_id: MEDIA1, "2": field_spec}
    processed_report_form = get_processed_report_form_fi(project=pt.project, fields_specs=fields_specs)
    f_values = dict(field_spec=field_spec, values_qty=field_spec.get("min"))

    json_fields = {
        media_field_id: processed_report_media_field_fi,
        "2": {"values": generate_processed_report_field_fi(**f_values)},
    }
    data = new_processed_report_data_fi(
        company_user=r_cu,
        project_territory=pt,
        worker_report=worker_report,
        processed_report_form=processed_report_form,
        json_fields=json_fields,
    )
    data.pop("company_user")
    response = __get_response(api_client, data, user=r_cu.user)

    assert response.data
    assert response.data["json_fields"] == json.loads(data["json_fields"])


@pytest.mark.parametrize("field_spec", (SELECT1, SELECT2))
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__select_field__success(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    new_processed_report_data_fi,
    processed_report_media_field_fi,
    generate_processed_report_field_fi,
    field_spec: tp.Dict[str, tp.Any],
    get_project_territory_fi,
):
    media_field_id = "1"

    pt = get_project_territory_fi(company=r_cu.company)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    processed_report_form = get_processed_report_form_fi(
        project=pt.project, fields_specs={media_field_id: MEDIA1, "2": field_spec}
    )
    f_values = dict(field_spec=field_spec, values_qty=field_spec.get("min"))
    json_fields = {
        media_field_id: processed_report_media_field_fi,
        "2": {"values": generate_processed_report_field_fi(**f_values)},
    }
    data = new_processed_report_data_fi(
        company_user=r_cu,
        project_territory=pt,
        processed_report_form=processed_report_form,
        json_fields=json_fields,
    )
    response = __get_response(api_client, data, user=r_cu.user)

    assert response.data
    assert response.data["json_fields"] == json.loads(data["json_fields"])


@pytest.mark.parametrize("modify_qty", (-1, 1))
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__wrong_qty_select_field__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    new_processed_report_data_fi,
    generate_processed_report_field_fi,
    processed_report_media_field_fi,
    modify_qty,
    get_project_territory_fi,
):
    prf_field = deepcopy(SELECT2)

    pt = get_project_territory_fi(company=r_cu.company)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    prf = get_processed_report_form_fi(project=pt.project, fields_specs={"1": MEDIA1, "2": prf_field})
    if modify_qty > 0:
        values_qty = prf_field["max"] + modify_qty
        error_reason = LESS_VALUES_REQUIRED.format(current_qty=values_qty, max_qty=prf_field["max"])
    else:
        values_qty = prf_field["min"] + modify_qty
        error_reason = MORE_VALUES_REQUIRED.format(current_qty=values_qty, min_qty=prf_field["min"])

    invalid_field_id = "2"
    json_fields = {
        "1": processed_report_media_field_fi,
        invalid_field_id: {
            "values": generate_processed_report_field_fi(field_spec=prf_field, values_qty=values_qty)
        },
    }
    data = new_processed_report_data_fi(
        company_user=r_cu, project_territory=pt, processed_report_form=prf, json_fields=json_fields
    )
    response = __get_response(api_client, data, user=r_cu.user, status_codes=ValidationError)

    assert response.data[0] == PROCESSED_REPORT_FIELD_ERROR.format(
        field_id=invalid_field_id,
        type_=prf_field[ma_saas.constants.system.TYPE],
        name=prf_field[ProcessedReportFormFieldSpecKeys.NAME],
        reason=error_reason,
    )


@pytest.mark.parametrize("field_spec", SIMPLE_REQUIRED_FIELDS)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__without_simple_required_field__fail(
    api_client,
    monkeypatch,
    get_processed_report_form_fi: Callable,
    new_processed_report_data_fi,
    processed_report_media_field_fi,
    field_spec: tp.Dict[str, tp.Any],
    r_cu,
    get_project_territory_fi,
):
    pt = get_project_territory_fi(company=r_cu.company)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    missed_field_id = "2"
    fields_specs = {"1": MEDIA1, missed_field_id: field_spec}
    prf = get_processed_report_form_fi(project=pt.project, fields_specs=fields_specs)

    json_fields = {"1": processed_report_media_field_fi}
    data = new_processed_report_data_fi(
        company_user=r_cu, project_territory=pt, processed_report_form=prf, json_fields=json_fields
    )
    data.pop("company_user")
    print("data =", data)
    response = __get_response(api_client, data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == [
        PROCESSED_REPORT_JSON_FIELDS_KEYS_INVALID.format(
            reason=MISSED_FIELDS_IDS_REQUIRED.format(missed_ids={missed_field_id})
        )
    ]
