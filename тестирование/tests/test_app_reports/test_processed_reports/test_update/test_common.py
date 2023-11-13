import json
import datetime as dt
import functools
from copy import deepcopy

import pytest
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework.exceptions import NotFound, ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_update, retrieve_response_instance
from ma_saas.utils import system
from pg_logger.models import PgLog
from ma_saas.constants.report import (
    FINAL_PROCESSED_REPORT_STATUS_VALUES,
    WorkerReportStatus,
    ProcessedReportStatus,
    ProcessedReportPartnerStatus,
    ProcessedReportFormFieldSpecTypes,
)
from ma_saas.constants.system import DATETIME_FORMAT, PgLogLVL
from ma_saas.constants.company import CUR, ROLES, NOT_ACCEPT_CUS
from clients.policies.interface import Policies
from reports.models.processed_report import PROCESSED_REPORT_JSON_FIELDS_KEYS_INVALID, ProcessedReport
from reports.serializers.processed_report import ProcessedReportSerializer
from tests.fixtures.processed_report_form import STR1, MEDIA1, MEDIA2, ALL_FIELDS_SPECS_LIST
from reports.validators.processed_report_model import (
    VALIDATION_ERROR_PROCESSED_REPORT_FIELDS_DO_NOT_BELONG_PRF,
)
from reports.validators.processed_report_serializer import FORBIDDEN_TO_CHANGE_IF_PARTNER_STATUS_ACCEPT
from tests.test_app_reports.test_processed_reports.constants import PROCESSED_REPORTS_PATH

User = get_user_model()

__get_response = functools.partial(request_response_update, path=PROCESSED_REPORTS_PATH)


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("processed_report_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, {}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__contractor_all_fields_at_once__success(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    generate_processed_report_field_fi,
    get_processed_report_fi,
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
    instance_fields = dict()
    for field_id, field_spec in clean_fields.items():
        instance_fields[field_id] = {"values": generate_processed_report_field_fi(field_spec=field_spec)}

    instance = get_processed_report_fi(
        company_user=r_cu, project_territory=pt, processed_report_form=prf, json_fields=instance_fields
    )

    new_json_fields = dict()
    for field_id, field_spec in clean_fields.items():
        new_json_fields[field_id] = {"values": generate_processed_report_field_fi(field_spec=field_spec)}

    data = {"json_fields": json.dumps(new_json_fields)}
    response = __get_response(api_client, instance.id, data, r_cu.user)

    assert response.data["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__contractor_update__if__partner_status_accepted__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    generate_processed_report_field_fi,
    get_processed_report_fi,
    get_project_territory_fi,
):
    pt = get_project_territory_fi(company=r_cu.company)

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
    processed_report_form = get_processed_report_form_fi(project=pt.project, fields_specs=clean_fields)

    instance_fields = dict()
    for field_id, field_spec in clean_fields.items():
        instance_fields[field_id] = {"values": generate_processed_report_field_fi(field_spec=field_spec)}

    instance = get_processed_report_fi(
        company_user=r_cu,
        project_territory=pt,
        processed_report_form=processed_report_form,
        json_fields=instance_fields,
        partner_status=ProcessedReportPartnerStatus.ACCEPTED.value,
    )
    data = {"status": ProcessedReportStatus.CREATED.value}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    assert response.data == [FORBIDDEN_TO_CHANGE_IF_PARTNER_STATUS_ACCEPT]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test_related__manager_status_update__success(api_client, monkeypatch, r_cu, get_processed_report_fi):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_processed_report_fi(company_user=r_cu)
    response = __get_response(api_client, instance_id=instance.id, data={}, user=r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__any__manager_status_update__with_policy__success(
    api_client, monkeypatch, get_processed_report_fi, r_cu
):

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_processed_report_fi(company_user=r_cu)
    response = __get_response(api_client, instance_id=instance.id, data={}, user=r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__any_manager_status_update__without_policy__fail(
    api_client, mock_policies_false, r_cu, get_processed_report_fi
):
    instance = get_processed_report_fi(company_user=r_cu)
    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("role", ROLES)
def test__client__fail(api_client, mock_policies_false, get_processed_report_fi, get_cu_fi, role):
    r_cu = get_cu_fi(role=role)
    instance = get_processed_report_fi()
    response = __get_response(api_client, instance.id, {}, user=r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__contractor_not_accepted_manager__fail(
    api_client,
    monkeypatch,
    get_processed_report_fi,
    get_project_territory_fi,
    get_cu_fi,
    status,
):
    r_cu = get_cu_fi(status=status, role=CUR.PROJECT_MANAGER)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    instance = get_processed_report_fi(company_user=r_cu, project_territory=pt)
    response = __get_response(api_client, instance.id, {}, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, get_processed_report_fi):
    instance = get_processed_report_fi(company=r_cu.company)
    response = __get_response(api_client, instance_id=instance.id, data={}, user=r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager__make_status_declined_at_updating__success(
    api_client, monkeypatch, r_cu, get_processed_report_fi, get_project_territory_fi
):

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    instance = get_processed_report_fi(company_user=r_cu, project_territory=pt)
    assert instance.status != ProcessedReportStatus.DECLINED.value
    # assert instance.accepted_at is None
    now = system.get_now()
    assert instance.accepted_at - now < dt.timedelta(seconds=2)

    data = {"status": ProcessedReportStatus.DECLINED.value}
    response = __get_response(api_client, instance.id, data, r_cu.user)
    updated_instance = ProcessedReport.objects.get(id=instance.id)
    assert updated_instance.status == ProcessedReportStatus.DECLINED.value
    # now = system.get_now()
    assert updated_instance.accepted_at - now < dt.timedelta(seconds=2)
    assert response.data["accepted_at"] == updated_instance.accepted_at.strftime(DATETIME_FORMAT)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__contractor_updated_by_company_user__data(
    api_client, monkeypatch, r_cu, get_processed_report_fi, get_project_territory_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    instance = get_processed_report_fi(
        company_user=r_cu, project_territory=pt, status=ProcessedReportStatus.CREATED.value
    )
    model_name = ProcessedReport._meta.concrete_model.__name__
    assert not PgLog.objects.filter(model_name=model_name, model_id=instance.id).exists()

    data = {"status": ProcessedReportStatus.DECLINED.value}
    response = __get_response(api_client, instance.id, data, r_cu.user)
    assert PgLog.objects.filter(model_name=model_name, model_id=instance.id).exists()
    response_instance = response.data
    if response_updated_by := retrieve_response_instance(response_instance, "updated_by", dict):
        if response_updated_by_user := retrieve_response_instance(response_updated_by, "user", dict):
            assert response_updated_by_user.pop("id") == r_cu.user.id
            assert response_updated_by_user.pop("first_name") == r_cu.user.first_name
            assert response_updated_by_user.pop("middle_name") == r_cu.user.middle_name
            assert response_updated_by_user.pop("last_name") == r_cu.user.last_name
            assert response_updated_by_user.pop("email") == r_cu.user.email
        assert not response_updated_by_user
        if response_updated_by_cu := retrieve_response_instance(response_updated_by, "company_user", dict):
            assert response_updated_by_cu.pop("id") == r_cu.id
        assert not response_updated_by_cu
    assert not response_updated_by


def test__contractor_updated_by_admin__data(
    api_client, monkeypatch, get_user_fi, get_processed_report_fi, get_worker_report_fi
):
    instance = get_processed_report_fi()
    project_scheme = instance.processed_report_form.project_scheme
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [project_scheme.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    r_u = get_user_fi()
    r_u.is_superuser = True
    r_u.save()

    model_name = ProcessedReport._meta.concrete_model.__name__
    assert not PgLog.objects.filter(model_name=model_name, model_id=instance.id).exists()

    PgLog.objects.create(
        level=PgLogLVL.info.value,
        user=r_u,
        model_name=model_name,
        model_id=instance.id,
        message="",
        params={},
    )
    serialised_instance = ProcessedReportSerializer(instance=instance).data
    if serialised_instance_updated_by := retrieve_response_instance(serialised_instance, "updated_by", dict):
        if serialised_instance_updated_by_user := retrieve_response_instance(
            serialised_instance_updated_by, "user", dict
        ):
            assert serialised_instance_updated_by_user.pop("id") == r_u.id
            assert serialised_instance_updated_by_user.pop("first_name") == r_u.first_name
            assert serialised_instance_updated_by_user.pop("middle_name") == r_u.middle_name
            assert serialised_instance_updated_by_user.pop("last_name") == r_u.last_name
            assert serialised_instance_updated_by_user.pop("email") == r_u.email
        assert not serialised_instance_updated_by_user

        if serialised_instance_updated_by_cu := retrieve_response_instance(
            serialised_instance_updated_by, "company_user", dict
        ):
            assert serialised_instance_updated_by_cu == {}
        assert not serialised_instance_updated_by_cu


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__more_than_single_media_field__success(
    api_client,
    monkeypatch,
    r_cu,
    get_worker_report_fi,
    get_schedule_time_slot_fi,
    get_reservation_fi,
    get_processed_report_form_fi,
    get_processed_report_fi,
    get_project_territory_fi,
    processed_report_media_field_fi,
):

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [pt.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    schedule_time_slot = get_schedule_time_slot_fi(project_territory=pt)
    reservation = get_reservation_fi(schedule_time_slot=schedule_time_slot)
    worker_report = get_worker_report_fi(
        project_territory_worker=reservation.project_territory_worker,
        schedule_time_slot=schedule_time_slot,
        status=WorkerReportStatus.ACCEPTED.value,
    )
    media_id1, media_id2 = "1", "2"
    fields_specs = {media_id1: MEDIA1, media_id2: MEDIA2}
    processed_report_form = get_processed_report_form_fi(project=pt.project, fields_specs=fields_specs)

    instance = get_processed_report_fi(
        company_user=r_cu,
        project_territory=pt,
        worker_report=worker_report,
        processed_report_form=processed_report_form,
        json_fields={media_id1: processed_report_media_field_fi},
    )

    new_fields = {media_id1: processed_report_media_field_fi, media_id2: processed_report_media_field_fi}
    data = {"json_fields": json.dumps(dict(new_fields))}
    response = __get_response(api_client, instance.id, data, user=r_cu.user)
    updated_instance = ProcessedReport.objects.get(id=instance.id)
    assert response.data
    assert response.data["json_fields"] == updated_instance.json_fields


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__remove_not_required_media_field__success(
    api_client,
    monkeypatch,
    r_cu,
    get_worker_report_fi,
    get_schedule_time_slot_fi,
    get_reservation_fi,
    get_project_territory_fi,
    get_processed_report_form_fi,
    get_processed_report_fi,
    processed_report_media_field_fi,
):
    pt = get_project_territory_fi(company=r_cu.company)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [pt.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    schedule_time_slot = get_schedule_time_slot_fi(project_territory=pt)
    reservation = get_reservation_fi(schedule_time_slot=schedule_time_slot)
    worker_report = get_worker_report_fi(
        project_territory_worker=reservation.project_territory_worker,
        schedule_time_slot=schedule_time_slot,
        status=WorkerReportStatus.ACCEPTED.value,
    )
    media_id1, media_id2 = "1", "2"
    fields_specs = {media_id1: MEDIA1, media_id2: MEDIA2}
    prf = get_processed_report_form_fi(project=pt.project, fields_specs=fields_specs)

    instance_fields = {media_id1: processed_report_media_field_fi, media_id2: processed_report_media_field_fi}
    instance = get_processed_report_fi(
        company_user=r_cu,
        project_territory=pt,
        worker_report=worker_report,
        processed_report_form=prf,
        json_fields=instance_fields,
    )

    new_fields = {media_id1: processed_report_media_field_fi}
    data = {"json_fields": json.dumps(new_fields)}
    response = __get_response(api_client, instance.id, data, user=r_cu.user)
    updated_instance = ProcessedReport.objects.get(id=instance.id)
    assert response.data
    assert response.data["json_fields"] == updated_instance.json_fields


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__without_deleted_field__success(
    api_client,
    monkeypatch,
    r_cu,
    get_worker_report_fi,
    get_schedule_time_slot_fi,
    get_reservation_fi,
    get_processed_report_form_fi,
    get_processed_report_fi,
    processed_report_media_field_fi,
    generate_processed_report_field_fi,
    get_project_territory_fi,
):
    pt = get_project_territory_fi(company=r_cu.company)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [pt.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    schedule_time_slot = get_schedule_time_slot_fi(project_territory=pt)
    reservation = get_reservation_fi(schedule_time_slot=schedule_time_slot)
    worker_report = get_worker_report_fi(
        project_territory_worker=reservation.project_territory_worker,
        schedule_time_slot=schedule_time_slot,
        status=WorkerReportStatus.ACCEPTED.value,
    )
    deleted_field, deleted_field_id = STR1, "2"
    fields_specs = {"1": MEDIA1, deleted_field_id: deleted_field}
    processed_report_form = get_processed_report_form_fi(project=pt.project, fields_specs=fields_specs)

    f_values = dict(field_spec=deleted_field, values_qty=deleted_field.get("min"))
    media_field_id = "1"
    instance_fields = {
        media_field_id: processed_report_media_field_fi,
        deleted_field_id: {"values": generate_processed_report_field_fi(**f_values)},
    }
    instance = get_processed_report_fi(
        company_user=r_cu,
        project_territory=pt,
        worker_report=worker_report,
        processed_report_form=processed_report_form,
        json_fields=instance_fields,
    )
    processed_report_form.fields_specs[deleted_field_id]["is_deleted"] = True
    processed_report_form.save()

    new_fields = {media_field_id: processed_report_media_field_fi}
    data = {"json_fields": json.dumps(new_fields)}
    response = __get_response(api_client, instance.id, data, user=r_cu.user)
    updated_instance = ProcessedReport.objects.get(id=instance.id)
    assert response.data
    assert response.data["json_fields"] == updated_instance.json_fields


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__with_deleted_field__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_worker_report_fi,
    get_processed_report_form_fi,
    get_processed_report_fi,
    processed_report_media_field_fi,
    generate_processed_report_field_fi,
    get_schedule_time_slot_fi,
    get_reservation_fi,
    get_project_territory_fi,
):
    pt = get_project_territory_fi(company=r_cu.company)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [pt.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    schedule_time_slot = get_schedule_time_slot_fi(project_territory=pt)
    reservation = get_reservation_fi(schedule_time_slot=schedule_time_slot)
    worker_report = get_worker_report_fi(
        project_territory_worker=reservation.project_territory_worker,
        schedule_time_slot=schedule_time_slot,
        status=WorkerReportStatus.ACCEPTED.value,
    )
    deleted_field = deepcopy(STR1)
    deleted_field_id = "2"
    fields_specs = {"1": MEDIA1, deleted_field_id: deleted_field}
    processed_report_form = get_processed_report_form_fi(project=pt.project, fields_specs=fields_specs)

    f_values = dict(field_spec=deleted_field, values_qty=deleted_field.get("min"))
    instance_fields = {
        "1": processed_report_media_field_fi,
        deleted_field_id: {"values": generate_processed_report_field_fi(**f_values)},
    }
    instance = get_processed_report_fi(
        company_user=r_cu,
        project_territory=pt,
        worker_report=worker_report,
        processed_report_form=processed_report_form,
        json_fields=instance_fields,
    )
    processed_report_form.fields_specs[deleted_field_id]["is_deleted"] = True
    processed_report_form.save()

    new_fields_dump = json.dumps(instance_fields)
    data = {"json_fields": new_fields_dump}
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    assert response.data[0] == PROCESSED_REPORT_JSON_FIELDS_KEYS_INVALID.format(
        reason=VALIDATION_ERROR_PROCESSED_REPORT_FIELDS_DO_NOT_BELONG_PRF.format(
            fields_ids={deleted_field_id}
        )
    )


# @pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
# def test__change_json_fields_id_not_status_created__fail(
#     api_client,
#     monkeypatch,
#     r_cu,
#     get_processed_report_form_fi,
#     get_project_territory_fi,
#     generate_processed_report_field_fi,
#     get_processed_report_fi,
# ):
#     pt = get_project_territory_fi(company=r_cu.company)
#     monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
#     monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [pt.id])
#     monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
#
#     clean_fields = dict()
#     existed_unique_fields = set()
#     for index, field in enumerate(ALL_FIELDS_SPECS_LIST):
#         if field["type"] in ProcessedReportFormFieldSpecTypes.unique_by_type:
#             if field["type"] in existed_unique_fields:
#                 continue
#             else:
#                 existed_unique_fields.add(field["type"])
#         clean_fields[index] = field
#     prf = get_processed_report_form_fi(project=pt.project, fields_specs=clean_fields)
#
#     instance_fields = dict()
#     for field_id, field_spec in clean_fields.items():
#         instance_fields[field_id] = {"values": generate_processed_report_field_fi(field_spec=field_spec)}
#
#     instance = get_processed_report_fi(
#         company_user=r_cu, project_territory=pt, processed_report_form=prf, json_fields=instance_fields
#     )
#
#     new_json_fields = dict()
#     for field_id, field_spec in clean_fields.items():
#         new_json_fields[field_id] = {"values": generate_processed_report_field_fi(field_spec=field_spec)}
#     data = {"json_fields": json.dumps(new_json_fields)}
#     response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
#     assert response.data[0] == CHANGE_PROCESSED_REPORT_JSON_FIELDS_IF_NOT_STATUS_CREATED


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
# @pytest.mark.parametrize("status", [s for s in ProcessedReportStatus if s != ProcessedReportStatus.CREATED])
@pytest.mark.parametrize("status", [s for s in ProcessedReportStatus])
# def test__change_json_fields_id_not_status_created__fail(
def test__change_json_fields_id__any_status__success(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_fi,
    get_project_territory_fi,
    get_processed_report_form_fi,
    get_processed_report_media_fields_fi,
    status,
):
    pt = get_project_territory_fi(company=r_cu.company)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [pt.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    prf = get_processed_report_form_fi(project=pt.project, fields_specs={1: MEDIA1})
    json_fields = {"1": get_processed_report_media_fields_fi(fields_specs=prf.fields_specs)}
    instance = get_processed_report_fi(
        company_user=r_cu,
        processed_report_form=prf,
        project_territory=pt,
        status=status,
        json_fields=json_fields,
    )

    json_fields = instance.json_fields
    json_fields["1"]["audio"] = [get_random_string()]
    data = {"json_fields": json.dumps(instance.json_fields)}
    # response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)
    response = __get_response(api_client, instance.id, data, r_cu.user)
    # assert response.data == [CHANGE_PROCESSED_REPORT_JSON_FIELDS_IF_NOT_STATUS_CREATED]
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__company_user_filed_do_not_update(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_fi,
    get_project_territory_fi,
    get_cu_fi,
):
    pt = get_project_territory_fi(company=r_cu.company)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [pt.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_processed_report_fi(company_user=r_cu, project_territory=pt)
    data = {"company_user": get_cu_fi().id}
    response = __get_response(api_client, instance.id, data, r_cu.user)
    assert response.data["id"] == instance.id
    assert response.data["company_user"]["id"] == r_cu.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__response_data(
    api_client,
    monkeypatch,
    r_cu,
    get_processed_report_form_fi,
    generate_processed_report_field_fi,
    get_processed_report_fi,
    get_project_territory_fi,
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

    instance_fields = dict()
    for field_id, field_spec in clean_fields.items():
        instance_fields[field_id] = {"values": generate_processed_report_field_fi(field_spec=field_spec)}

    instance = get_processed_report_fi(
        company_user=r_cu, project_territory=pt, processed_report_form=prf, json_fields=instance_fields
    )

    new_json_fields = dict()
    for field_id, field_spec in clean_fields.items():
        new_json_fields[f"{field_id}"] = {"values": generate_processed_report_field_fi(field_spec=field_spec)}
    new_comment = get_random_string()
    data = {"json_fields": json.dumps(new_json_fields), "comment": new_comment}
    response = __get_response(api_client, instance.id, data, user=r_cu.user)
    response_instance = response.data
    response_id = response_instance.pop("id")
    assert response_id
    updated_instance = ProcessedReport.objects.get(id=response_id)
    assert updated_instance.created_at != updated_instance.updated_at != updated_instance.accepted_at
    assert (
        updated_instance.updated_at
        != updated_instance.worker_report.updated_at
        != updated_instance.worker_report.created_at
    )
    if response_prf := retrieve_response_instance(response_instance, "processed_report_form", dict):
        assert response_prf.pop("id") == prf.id
        assert response_prf.pop("fields_specs") == prf.fields_specs
        if response_project_scheme := retrieve_response_instance(response_prf, "project_scheme", dict):
            assert response_project_scheme.pop("id") == prf.project_scheme.id
            if response_project := retrieve_response_instance(response_project_scheme, "project", dict):
                assert response_project.pop("id") == prf.project_scheme.project.id
                assert response_project.pop("title") == prf.project_scheme.project.title
            assert not response_project
        assert not response_project_scheme
    assert not response_prf

    if response_wr := retrieve_response_instance(response_instance, "worker_report", dict):
        assert response_wr.pop("id") == instance.worker_report.id
        if response_wr_cu := retrieve_response_instance(response_wr, "company_user", dict):
            assert response_wr_cu.pop("id") == instance.worker_report.company_user.id
            if response_wr_user := retrieve_response_instance(response_wr_cu, "user", dict):
                assert response_wr_user.pop("id") == instance.worker_report.company_user.user.id
                assert (
                    response_wr_user.pop("first_name") == instance.worker_report.company_user.user.first_name
                )
                assert (
                    response_wr_user.pop("middle_name")
                    == instance.worker_report.company_user.user.middle_name
                )
                assert response_wr_user.pop("last_name") == instance.worker_report.company_user.user.last_name
                assert response_wr_user.pop("email") == instance.worker_report.company_user.user.email
                assert response_wr_user.pop("phone") == instance.worker_report.company_user.user.phone
            assert not response_wr_user
            if response_wr_company := retrieve_response_instance(response_wr_cu, "company", dict):
                assert response_wr_company.pop("id") == instance.worker_report.company_user.company.id
                assert response_wr_company.pop("title") == instance.worker_report.company_user.company.title
            assert not response_wr_company
        assert not response_wr_cu
        if response_sts := retrieve_response_instance(response_wr, "schedule_time_slot", dict):
            assert response_sts.pop("id") == instance.worker_report.schedule_time_slot.id
            assert response_sts.pop("reward") == instance.worker_report.schedule_time_slot.reward
            if response_gp := retrieve_response_instance(response_sts, "geo_point", dict):
                assert response_gp.pop("id") == instance.worker_report.schedule_time_slot.geo_point.id
                assert response_gp.pop("lon") == instance.worker_report.schedule_time_slot.geo_point.lon
                assert response_gp.pop("lat") == instance.worker_report.schedule_time_slot.geo_point.lat
                assert response_gp.pop("city") == instance.worker_report.schedule_time_slot.geo_point.city
                assert (
                    response_gp.pop("address") == instance.worker_report.schedule_time_slot.geo_point.address
                )
                assert response_gp.pop("title") == instance.worker_report.schedule_time_slot.geo_point.title
            assert not response_gp
        assert not response_sts
    assert not response_wr

    if response_company_user := retrieve_response_instance(response_instance, "company_user", dict):
        assert response_company_user.pop("id") == instance.company_user.id
        if response_company_user_user := retrieve_response_instance(response_company_user, "user", dict):
            assert response_company_user_user.pop("id") == instance.company_user.user.id
            assert response_company_user_user.pop("first_name") == instance.company_user.user.first_name
            assert response_company_user_user.pop("middle_name") == instance.company_user.user.middle_name
            assert response_company_user_user.pop("last_name") == instance.company_user.user.last_name
            assert response_company_user_user.pop("email") == instance.company_user.user.email
            assert response_company_user_user.pop("phone") == instance.company_user.user.phone
        assert not response_company_user_user
        if response_cu_company := retrieve_response_instance(response_company_user, "company", dict):
            assert response_cu_company.pop("id") == instance.company_user.company.id
            assert response_cu_company.pop("title") == instance.company_user.company.title
        assert not response_cu_company
    assert not response_company_user

    assert response_instance.pop("status") == ProcessedReportStatus.ACCEPTED.value
    assert response_instance.pop("json_fields") == updated_instance.json_fields
    response_create_at = response_instance.pop("created_at")
    response_updated_at = response_instance.pop("updated_at")
    assert response_create_at
    assert response_updated_at
    assert response_create_at != response_updated_at
    # assert not response_instance.pop("accepted_at")
    assert response_instance.pop("accepted_at")
    if response_updated_by := retrieve_response_instance(response_instance, "updated_by", dict):
        assert response_updated_by.pop("user")
        assert response_updated_by.pop("company_user")
    assert not response_updated_by
    assert response_instance.pop("comment") == new_comment
