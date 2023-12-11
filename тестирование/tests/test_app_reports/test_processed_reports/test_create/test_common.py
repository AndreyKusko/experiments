import functools
from copy import deepcopy

import pytest
from django.contrib.auth import get_user_model
from rest_framework.utils import json
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_create, retrieve_response_instance
from ma_saas.utils import system
from geo_objects.models import NOT_TA_GEO_POINT_REASON
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from projects.models.project import PROJECT_STATUS_MUST_BE_ACTIVE
from ma_saas.constants.report import NOT_DECLINED_PROCESSED_REPORT_STATUSES_VALUES
from ma_saas.constants.report import WorkerReportStatus as WRS
from ma_saas.constants.report import ProcessedReportStatus, ProcessedReportFormFieldSpecTypes
from ma_saas.constants.company import CUR, CUS, ROLES, NOT_ACCEPT_CUS
from ma_saas.constants.project import NOT_ACTIVE_PROJECT_STATUS
from clients.policies.interface import Policies
from reports.models.worker_report import NOT_TA_WORKER_REPORT_REASON, WorkerReport
from companies.models.company_user import NOT_TA_RCU_MUST_BE_ACCEPT, CompanyUser
from reports.models.processed_report import (
    PROCESSED_REPORT_DUPLICATION_ERROR,
    PROCESSED_REPORT_JSON_FIELDS_KEYS_INVALID,
    ProcessedReport,
)
from tasks.models.schedule_time_slot import NOT_TA_SCHEDULE_TIME_SLOT_REASON
from projects.models.project_territory import NOT_TA_PT_REASON, PT_STATUS_NOT_ACTIVE
from reports.models.processed_report_form import ProcessedReportForm
from reports.permissions.processed_report import (
    WORKER_REPORT_MUST_HAVE_STATUS_THAT_ALLOW_PROCESSED_REPORT_CREATION,
)
from tests.fixtures.processed_report_form import STR1, MEDIA1, MEDIA2, ALL_FIELDS_SPECS_LIST
from reports.validators.processed_report_model import (
    VALIDATION_ERROR_PROCESSED_REPORT_FIELDS_DO_NOT_BELONG_PRF,
)
from tests.test_app_reports.test_processed_reports.constants import PROCESSED_REPORTS_PATH

User = get_user_model()

__get_response = functools.partial(request_response_create, path=PROCESSED_REPORTS_PATH)


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, {}, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(
    api_client,
    mock_policies_false,
    new_processed_report_data_fi,
    get_project_fi,
    get_processed_report_form_fi,
    get_project_territory_fi,
    generate_processed_report_field_fi,
    r_cu,
):
    clean_fields = dict()
    existed_unique_fields = set()
    for index, field in enumerate(ALL_FIELDS_SPECS_LIST):
        if field["type"] in ProcessedReportFormFieldSpecTypes.unique_by_type:
            if field["type"] in existed_unique_fields:
                continue
            else:
                existed_unique_fields.add(field["type"])
        clean_fields[index] = field
    project = get_project_fi(company=r_cu.company)
    processed_report_form = get_processed_report_form_fi(project=project, fields_specs=clean_fields)
    project_territory = get_project_territory_fi(project=project)
    json_fields = dict()
    for field_id, field_spec in clean_fields.items():
        json_fields[field_id] = {"values": generate_processed_report_field_fi(field_spec=field_spec)}

    data = new_processed_report_data_fi(
        project_territory=project_territory,
        processed_report_form=processed_report_form,
        json_fields=json_fields,
    )

    response = __get_response(api_client, data, r_cu.user)
    assert response.data.get("id"), f"response.data = {response.data}"


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__contractor__manager__success(
    api_client,
    r_cu,
    new_processed_report_data_fi,
    get_processed_report_form_fi,
    generate_processed_report_field_fi,
    get_project_territory_fi,
):
    clean_fields = dict()
    existed_unique_fields = set()
    for index, field in enumerate(ALL_FIELDS_SPECS_LIST):
        if field["type"] in ProcessedReportFormFieldSpecTypes.unique_by_type:
            if field["type"] in existed_unique_fields:
                continue
            else:
                existed_unique_fields.add(field["type"])
        clean_fields[index] = field

    pt = get_project_territory_fi(company=r_cu.company)
    processed_report_form = get_processed_report_form_fi(pt.project, fields_specs=clean_fields)
    json_fields = dict()
    for field_id, field_spec in clean_fields.items():
        json_fields[field_id] = {"values": generate_processed_report_field_fi(field_spec=field_spec)}

    data = new_processed_report_data_fi(
        project_territory=pt, processed_report_form=processed_report_form, json_fields=json_fields
    )

    response = __get_response(api_client, data, r_cu.user)
    assert response.data
    assert response.data["company_user"] == r_cu.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
@pytest.mark.parametrize("manager_report_status", ProcessedReportStatus)
def test__creating_with_any_status_no_influence__fail(
    api_client,
    monkeypatch,
    r_cu,
    new_processed_report_data_fi,
    get_processed_report_form_fi,
    get_project_territory_fi,
    generate_processed_report_field_fi,
    manager_report_status,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    clean_fields = dict()
    existed_unique_fields = set()
    for index, field in enumerate(ALL_FIELDS_SPECS_LIST):
        if field["type"] in ProcessedReportFormFieldSpecTypes.unique_by_type:
            if field["type"] in existed_unique_fields:
                continue
            else:
                existed_unique_fields.add(field["type"])
        clean_fields[index] = field

    prf = get_processed_report_form_fi(project=pt.project, fields_specs=clean_fields)
    json_fields = dict()
    for field_id, field_spec in clean_fields.items():
        json_fields[field_id] = {"values": generate_processed_report_field_fi(field_spec=field_spec)}

    data = new_processed_report_data_fi(
        project_territory=pt,
        processed_report_form=prf,
        json_fields=json_fields,
        status=manager_report_status,
    )
    response = __get_response(api_client, data, r_cu.user)
    assert response.data["id"]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__contractor__manager__success(
    api_client,
    monkeypatch,
    r_cu,
    new_processed_report_data_fi,
    get_project_territory_fi,
    get_processed_report_form_fi,
    generate_processed_report_field_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    clean_fields = dict()
    existed_unique_fields = set()
    for index, field in enumerate(ALL_FIELDS_SPECS_LIST):
        if field["type"] in ProcessedReportFormFieldSpecTypes.unique_by_type:
            if field["type"] in existed_unique_fields:
                continue
            else:
                existed_unique_fields.add(field["type"])
        clean_fields[index] = field

    pt = get_project_territory_fi(company=r_cu.company)
    prf = get_processed_report_form_fi(project=pt.project, fields_specs=clean_fields)
    json_fields = dict()
    for field_id, field_spec in clean_fields.items():
        json_fields[field_id] = {"values": generate_processed_report_field_fi(field_spec=field_spec)}

    data = new_processed_report_data_fi(
        project_territory=pt, processed_report_form=prf, json_fields=json_fields
    )
    response = __get_response(api_client, data, r_cu.user)
    assert response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
@pytest.mark.parametrize("existing_report_status", NOT_DECLINED_PROCESSED_REPORT_STATUSES_VALUES)
def test__duplicates__with_not_declined_status__fail(
    api_client,
    monkeypatch,
    r_cu,
    new_processed_report_data_fi,
    get_processed_report_fi,
    get_cu_fi,
    get_processed_report_form_fi,
    get_project_territory_fi,
    generate_processed_report_field_fi,
    existing_report_status,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    clean_fields = dict()
    existed_unique_fields = set()
    for index, field in enumerate(ALL_FIELDS_SPECS_LIST):
        if field["type"] in ProcessedReportFormFieldSpecTypes.unique_by_type:
            if field["type"] in existed_unique_fields:
                continue
            else:
                existed_unique_fields.add(field["type"])
        clean_fields[index] = field

    pt = get_project_territory_fi(company=r_cu.company)
    prf = get_processed_report_form_fi(project=pt.project, fields_specs=clean_fields)
    json_fields = dict()
    for field_id, field_spec in clean_fields.items():
        json_fields[field_id] = {"values": generate_processed_report_field_fi(field_spec=field_spec)}

    data = new_processed_report_data_fi(
        company_user=r_cu, project_territory=pt, processed_report_form=prf, json_fields=json_fields
    )
    duplicate_data = deepcopy(data)
    duplicate_data["processed_report_form"] = ProcessedReportForm.objects.get(
        id=duplicate_data["processed_report_form"]
    )
    duplicate_data["worker_report"] = WorkerReport.objects.get(id=duplicate_data["worker_report"])
    duplicate_data["company_user"] = CompanyUser.objects.get(id=duplicate_data["company_user"])
    duplicate_data["json_fields"] = json.loads(duplicate_data["json_fields"])
    duplicate_data["status"] = existing_report_status
    get_processed_report_fi(**duplicate_data)

    response = __get_response(api_client, data, r_cu.user, status_codes=ValidationError)
    assert response.data == [
        PROCESSED_REPORT_DUPLICATION_ERROR.format(worker_report_id=data["worker_report"])
    ]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__duplicates__with_declined_status__success(
    api_client,
    monkeypatch,
    r_cu,
    new_processed_report_data_fi,
    get_processed_report_fi,
    get_cu_fi,
    get_processed_report_form_fi,
    generate_processed_report_field_fi,
    get_project_territory_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    clean_fields = dict()
    existed_unique_fields = set()
    for index, field in enumerate(ALL_FIELDS_SPECS_LIST):
        if field["type"] in ProcessedReportFormFieldSpecTypes.unique_by_type:
            if field["type"] in existed_unique_fields:
                continue
            else:
                existed_unique_fields.add(field["type"])
        clean_fields[index] = field

    pt = get_project_territory_fi(company=r_cu.company)
    prf = get_processed_report_form_fi(project=pt.project, fields_specs=clean_fields)
    json_fields = dict()
    for field_id, field_spec in clean_fields.items():
        json_fields[field_id] = {"values": generate_processed_report_field_fi(field_spec=field_spec)}

    data = new_processed_report_data_fi(
        company_user=r_cu, project_territory=pt, processed_report_form=prf, json_fields=json_fields
    )
    duplicate_data = deepcopy(data)
    duplicate_data["processed_report_form"] = ProcessedReportForm.objects.get(
        id=duplicate_data["processed_report_form"]
    )
    duplicate_data["worker_report"] = WorkerReport.objects.get(id=duplicate_data["worker_report"])
    duplicate_data["company_user"] = CompanyUser.objects.get(id=duplicate_data["company_user"])
    duplicate_data["json_fields"] = json.loads(duplicate_data["json_fields"])
    duplicate_data["status"] = ProcessedReportStatus.DECLINED.value
    get_processed_report_fi(**duplicate_data)

    response = __get_response(api_client, data, r_cu.user)
    assert response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__contractor_all_fields_at_once__success(
    api_client,
    monkeypatch,
    r_cu,
    new_processed_report_data_fi,
    get_processed_report_form_fi,
    generate_processed_report_field_fi,
    get_project_territory_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    clean_fields = dict()
    existed_unique_fields = set()
    for index, field in enumerate(ALL_FIELDS_SPECS_LIST):
        if field["type"] in ProcessedReportFormFieldSpecTypes.unique_by_type:
            if field["type"] in existed_unique_fields:
                continue
            else:
                existed_unique_fields.add(field["type"])
        clean_fields[index] = field

    pt = get_project_territory_fi(company=r_cu.company)
    prf = get_processed_report_form_fi(project=pt.project, fields_specs=clean_fields)
    json_fields = dict()
    for field_id, field_spec in clean_fields.items():
        json_fields[field_id] = {"values": generate_processed_report_field_fi(field_spec=field_spec)}

    data = new_processed_report_data_fi(
        project_territory=pt, processed_report_form=prf, json_fields=json_fields
    )
    response = __get_response(api_client, data, r_cu.user)
    assert response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__contractor_inaccessible_fields_do_not_update(
    api_client, monkeypatch, r_cu, new_processed_report_data_fi, get_cu_fi, get_project_territory_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    data = new_processed_report_data_fi(project_territory=pt)
    data["company_user"] = get_cu_fi().id
    data["accepted_at"] = system.get_now()
    response = __get_response(api_client, data, r_cu.user)
    created_instance = ProcessedReport.objects.get(id=response.data["id"])
    assert data["company_user"] != response.data["company_user"]["id"]
    assert data["company_user"] != created_instance.company_user.id
    assert response.data["company_user"]["id"] == created_instance.company_user.id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_manager__fail(
    api_client, get_cu_fi, new_processed_report_data_fi, status, get_project_territory_fi
):
    r_cu = get_cu_fi(status=status.value, role=CUR.PROJECT_MANAGER)
    pt = get_project_territory_fi(company=r_cu.company)
    data = new_processed_report_data_fi(project_territory=pt)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
@pytest.mark.parametrize("status", NOT_ACTIVE_PROJECT_STATUS)
def test__not_active_project__fail(
    api_client, r_cu, new_processed_report_data_fi, get_project_territory_fi, status
):
    pt = get_project_territory_fi(company=r_cu.company)
    pt.project.status = status.value
    pt.project.save()
    data = new_processed_report_data_fi(project_territory=pt)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PROJECT_STATUS_MUST_BE_ACTIVE}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__contractor_not_active_project_territory__fail(
    api_client, monkeypatch, r_cu, new_processed_report_data_fi, get_project_territory_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    pt = get_project_territory_fi(company=r_cu.company)
    pt.is_active = False
    pt.save()
    data = new_processed_report_data_fi(project_territory=pt)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": NOT_TA_WORKER_REPORT_REASON.format(
            reason=NOT_TA_SCHEDULE_TIME_SLOT_REASON.format(
                reason=NOT_TA_GEO_POINT_REASON.format(
                    reason=NOT_TA_PT_REASON.format(reason=PT_STATUS_NOT_ACTIVE)
                )
            )
        )
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
@pytest.mark.parametrize("status", (WRS.ACCEPTED, WRS.DECLINED))
def test__contractor_with_worker_report_in_any_final_status__success(
    api_client,
    monkeypatch,
    r_cu,
    get_worker_report_fi,
    get_project_territory_fi,
    new_processed_report_data_fi,
    get_reservation_fi,
    get_schedule_time_slot_fi,
    status,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    schedule_time_slot = get_schedule_time_slot_fi(project_territory=pt)
    reservation = get_reservation_fi(schedule_time_slot=schedule_time_slot)
    worker_report = get_worker_report_fi(
        project_territory_worker=reservation.project_territory_worker,
        schedule_time_slot=schedule_time_slot,
        status=status.value,
    )
    data = new_processed_report_data_fi(worker_report=worker_report)
    assert __get_response(api_client, data, r_cu.user)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
@pytest.mark.parametrize("status", (s for s in WRS if s not in {WRS.LOADED, WRS.ACCEPTED, WRS.DECLINED}))
def test__contractor_not_moderated_worker_report__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_worker_report_fi,
    get_project_territory_fi,
    new_processed_report_data_fi,
    get_schedule_time_slot_fi,
    get_reservation_fi,
    status,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    schedule_time_slot = get_schedule_time_slot_fi(project_territory=pt)
    reservation = get_reservation_fi(schedule_time_slot=schedule_time_slot)
    worker_report = get_worker_report_fi(
        project_territory_worker=reservation.project_territory_worker,
        schedule_time_slot=schedule_time_slot,
        status=status.value,
    )
    data = new_processed_report_data_fi(project_territory=pt, worker_report=worker_report)
    response = __get_response(api_client, data, r_cu.user, status_codes=ValidationError)
    assert response.data == {
        "worker_report": [WORKER_REPORT_MUST_HAVE_STATUS_THAT_ALLOW_PROCESSED_REPORT_CREATION]
    }


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", CUS)
def test__contractor_different_company_user__fail(
    api_client,
    get_cu_fi,
    get_project_territory_fi,
    new_processed_report_data_fi,
    role,
    status,
):
    r_cu = get_cu_fi(role=role, status=status.value)
    pt = get_project_territory_fi()
    data = new_processed_report_data_fi(project_territory=pt)

    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__contractor_without_deleted_field__success(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    get_project_territory_fi,
    new_processed_report_data_fi,
    processed_report_media_field_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    deleted_field = deepcopy(STR1)
    deleted_field["is_deleted"] = True
    media_field_id, deleted_field_id = "1", "2"
    fields_specs = {media_field_id: MEDIA1, deleted_field_id: deleted_field}
    prf = get_processed_report_form_fi(project=pt.project, fields_specs=fields_specs)

    instance_json_fields = {media_field_id: processed_report_media_field_fi}
    data = new_processed_report_data_fi(
        company_user=r_cu, project_territory=pt, processed_report_form=prf, json_fields=instance_json_fields
    )
    response = __get_response(api_client, data, r_cu.user)
    assert len(response.data["json_fields"]) == 1
    assert response.data["json_fields"] == json.loads(data["json_fields"])


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__more_than_one_media_fields__success(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    get_project_territory_fi,
    new_processed_report_data_fi,
    processed_report_media_field_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    deleted_field = deepcopy(STR1)
    deleted_field["is_deleted"] = True
    media_id1, media_id2 = "1", "2"
    fields_specs = {media_id1: MEDIA1, media_id2: MEDIA2}
    processed_report_form = get_processed_report_form_fi(project=pt.project, fields_specs=fields_specs)

    instance_json_fields = {
        media_id1: processed_report_media_field_fi,
        media_id2: processed_report_media_field_fi,
    }
    data = new_processed_report_data_fi(
        company_user=r_cu,
        project_territory=pt,
        processed_report_form=processed_report_form,
        json_fields=instance_json_fields,
    )
    response = __get_response(api_client, data, r_cu.user)
    assert len(response.data["json_fields"]) == 2
    assert response.data["json_fields"] == json.loads(data["json_fields"])


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__not_required_media_field__success(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    get_project_territory_fi,
    new_processed_report_data_fi,
    processed_report_media_field_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    deleted_field = deepcopy(STR1)
    deleted_field["is_deleted"] = True
    media_field_id1, media_field_id2 = "1", "2"
    fields_specs = {media_field_id1: MEDIA1, media_field_id2: MEDIA2}
    prf = get_processed_report_form_fi(project=pt.project, fields_specs=fields_specs)
    instance_json_fields = {media_field_id1: processed_report_media_field_fi}
    data = new_processed_report_data_fi(
        company_user=r_cu, project_territory=pt, processed_report_form=prf, json_fields=instance_json_fields
    )
    response = __get_response(api_client, data, r_cu.user)
    assert len(response.data["json_fields"]) == 1
    assert response.data["json_fields"] == json.loads(data["json_fields"])
    assert response.data["json_fields"][media_field_id1]
    assert media_field_id2 not in response.data["json_fields"]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__contractor_without_deleted_field__success(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    get_project_territory_fi,
    new_processed_report_data_fi,
    processed_report_media_field_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    deleted_field = deepcopy(STR1)
    deleted_field["is_deleted"] = True
    media_field_id1, deleted_field_id, media_field_id2 = "1", "2", "3"
    fields_specs = {media_field_id1: MEDIA1, deleted_field_id: deleted_field, media_field_id2: MEDIA1}
    pt = get_project_territory_fi(company=r_cu.company)
    prf = get_processed_report_form_fi(project=pt.project, fields_specs=fields_specs)
    instance_json_fields = {media_field_id1: processed_report_media_field_fi}
    data = new_processed_report_data_fi(
        company_user=r_cu, project_territory=pt, processed_report_form=prf, json_fields=instance_json_fields
    )
    response = __get_response(api_client, data, r_cu.user)
    assert len(response.data["json_fields"]) == 1

    assert response.data["json_fields"] == json.loads(data["json_fields"])


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__not_required_media_field__success(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    get_project_territory_fi,
    new_processed_report_data_fi,
    processed_report_media_field_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    deleted_field = deepcopy(STR1)
    deleted_field["is_deleted"] = True
    media_field_id1, media_field_id2 = "1", "2"
    fields_specs = {media_field_id1: MEDIA1, media_field_id2: MEDIA2}
    pt = get_project_territory_fi(company=r_cu.company)
    prf = get_processed_report_form_fi(project=pt.project, fields_specs=fields_specs)

    instance_json_fields = {media_field_id1: processed_report_media_field_fi}
    data = new_processed_report_data_fi(
        company_user=r_cu, project_territory=pt, processed_report_form=prf, json_fields=instance_json_fields
    )
    response = __get_response(api_client, data, r_cu.user)
    assert len(response.data["json_fields"]) == 1
    assert response.data["json_fields"] == json.loads(data["json_fields"])
    assert response.data["json_fields"][media_field_id1]
    assert media_field_id2 not in response.data["json_fields"]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__contractor_without_deleted_field__success(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    get_project_territory_fi,
    new_processed_report_data_fi,
    processed_report_media_field_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    deleted_field = deepcopy(STR1)
    deleted_field["is_deleted"] = True
    media_field_id1, deleted_field_id = "1", "2"
    fields_specs = {media_field_id1: MEDIA1, deleted_field_id: deleted_field}
    pt = get_project_territory_fi(company=r_cu.company)
    prf = get_processed_report_form_fi(project=pt.project, fields_specs=fields_specs)
    instance_json_fields = {media_field_id1: processed_report_media_field_fi}
    data = new_processed_report_data_fi(
        company_user=r_cu, project_territory=pt, processed_report_form=prf, json_fields=instance_json_fields
    )
    response = __get_response(api_client, data, r_cu.user)
    assert len(response.data["json_fields"]) == 1
    assert response.data["json_fields"] == json.loads(data["json_fields"])


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__contractor_with_deleted_field__fail(
    api_client,
    monkeypatch,
    get_processed_report_form_fi,
    get_project_territory_fi,
    new_processed_report_data_fi,
    processed_report_media_field_fi,
    generate_processed_report_field_fi,
    r_cu,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    deleted_field = deepcopy(STR1)
    deleted_field_id = "2"
    pt = get_project_territory_fi(company=r_cu.company)
    fields_specs = {"1": MEDIA1, deleted_field_id: deleted_field}
    processed_report_form = get_processed_report_form_fi(project=pt.project, fields_specs=fields_specs)
    __f_values = dict(field_spec=deleted_field, values_qty=deleted_field.get("min"))
    instance_json_fields = {
        "1": processed_report_media_field_fi,
        deleted_field_id: {"values": generate_processed_report_field_fi(**__f_values)},
    }
    data = new_processed_report_data_fi(
        project_territory=pt, processed_report_form=processed_report_form, json_fields=instance_json_fields
    )
    processed_report_form.fields_specs[deleted_field_id]["is_deleted"] = True
    processed_report_form.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=ValidationError)
    assert response.data == [
        PROCESSED_REPORT_JSON_FIELDS_KEYS_INVALID.format(
            reason=VALIDATION_ERROR_PROCESSED_REPORT_FIELDS_DO_NOT_BELONG_PRF.format(
                fields_ids={deleted_field_id}
            )
        )
    ]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(
    api_client,
    new_processed_report_data_fi,
    get_project_fi,
    get_processed_report_form_fi,
    get_project_territory_fi,
    generate_processed_report_field_fi,
    r_cu,
):
    clean_fields = dict()
    existed_unique_fields = set()
    for index, field in enumerate(ALL_FIELDS_SPECS_LIST):
        if field["type"] in ProcessedReportFormFieldSpecTypes.unique_by_type:
            if field["type"] in existed_unique_fields:
                continue
            else:
                existed_unique_fields.add(field["type"])
        clean_fields[index] = field
    project = get_project_fi(company=r_cu.company)
    processed_report_form = get_processed_report_form_fi(project=project, fields_specs=clean_fields)
    project_territory = get_project_territory_fi(project=project)
    json_fields = dict()
    for field_id, field_spec in clean_fields.items():
        json_fields[field_id] = {"values": generate_processed_report_field_fi(field_spec=field_spec)}

    data = new_processed_report_data_fi(
        project_territory=project_territory,
        processed_report_form=processed_report_form,
        json_fields=json_fields,
    )
    response = __get_response(api_client, data, r_cu.user)
    response_instance = response.data
    assert response_instance

    created_instance = ProcessedReport.objects.filter(id=response_instance.pop("id")).first()
    assert created_instance
    if response_company_user := retrieve_response_instance(response_instance, "company_user", dict):
        assert response_company_user.pop("id") == r_cu.id
        if response_user := retrieve_response_instance(response_company_user, "user", dict):
            assert response_user.pop("id") == r_cu.user.id
            assert response_user.pop("first_name") == r_cu.user.first_name
            assert response_user.pop("middle_name") == r_cu.user.middle_name
            assert response_user.pop("last_name") == r_cu.user.last_name
            assert response_user.pop("phone") == r_cu.user.phone
            assert response_user.pop("email") == r_cu.user.email
        assert not response_user
        if response_company := retrieve_response_instance(response_company_user, "company", dict):
            assert response_company.pop("id") == r_cu.company.id
            assert response_company.pop("title") == r_cu.company.title
        assert not response_company
    assert not response_company_user

    if response_worker_report := retrieve_response_instance(response_instance, "worker_report", dict):
        assert response_worker_report.pop("id") == data["worker_report"]
        worker_report = created_instance.worker_report
        if response_wr_cu := retrieve_response_instance(response_worker_report, "company_user", dict):
            assert response_wr_cu.pop("id") == worker_report.company_user.id
            if response_wr_cu_user := retrieve_response_instance(response_wr_cu, "user", dict):
                assert response_wr_cu_user.pop("id") == worker_report.company_user.user.id
                assert response_wr_cu_user.pop("phone") == worker_report.company_user.user.phone
                assert response_wr_cu_user.pop("email") == worker_report.company_user.user.email
                assert response_wr_cu_user.pop("first_name") == worker_report.company_user.user.first_name
                assert response_wr_cu_user.pop("middle_name") == worker_report.company_user.user.middle_name
                assert response_wr_cu_user.pop("last_name") == worker_report.company_user.user.last_name
            assert not response_wr_cu_user
            if response_worker_report_company := retrieve_response_instance(response_wr_cu, "company", dict):
                assert response_worker_report_company.pop("id") == worker_report.company_user.company.id
                assert response_worker_report_company.pop("title") == worker_report.company_user.company.title
            assert not response_worker_report_company
        assert not response_wr_cu
        if response_sts := retrieve_response_instance(response_worker_report, "schedule_time_slot", dict):
            assert response_sts.pop("id") == worker_report.schedule_time_slot.id
            assert response_sts.pop("reward") == worker_report.schedule_time_slot.reward
            if response_gp := retrieve_response_instance(response_sts, "geo_point", dict):
                assert response_gp.pop("id") == worker_report.schedule_time_slot.geo_point.id
                assert response_gp.pop("title") == worker_report.schedule_time_slot.geo_point.title
                assert response_gp.pop("lon") == worker_report.schedule_time_slot.geo_point.lon
                assert response_gp.pop("lat") == worker_report.schedule_time_slot.geo_point.lat
                assert response_gp.pop("city") == worker_report.schedule_time_slot.geo_point.city
                assert response_gp.pop("address") == worker_report.schedule_time_slot.geo_point.address
            assert not response_sts
        assert not response_sts
    assert not response_worker_report

    if response_prf := retrieve_response_instance(response_instance, "processed_report_form", dict):
        assert response_prf.pop("id") == processed_report_form.id
        assert response_prf.pop("fields_specs") == processed_report_form.fields_specs
        if response_ps := retrieve_response_instance(response_prf, "project_scheme", dict):
            assert response_ps.pop("id") == processed_report_form.project_scheme.id
            if response_project := retrieve_response_instance(response_ps, "project", dict):
                assert response_project.pop("id") == processed_report_form.project_scheme.project.id
                assert response_project.pop("title") == processed_report_form.project_scheme.project.title
            assert not response_project
        assert not response_ps
    assert not response_prf

    assert response_instance.pop("status") == ProcessedReportStatus.ACCEPTED.value
    assert response_instance.pop("json_fields") == json.loads(data["json_fields"])
    assert response_instance.pop("created_at")
    assert response_instance.pop("updated_at")
    assert response_instance.pop("accepted_at")
    assert response_instance.pop("updated_by") == {"user": {}, "company_user": {}}
    assert response_instance.pop("comment") == data["comment"]
    assert not response_instance
