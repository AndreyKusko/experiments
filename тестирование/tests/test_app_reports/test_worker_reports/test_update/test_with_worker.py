import json

import pytest
from rest_framework import status as status_code
from django.utils.crypto import get_random_string
from rest_framework.exceptions import PermissionDenied

from ma_saas.constants.report import WorkerReportStatus as WRS
from ma_saas.constants.report import ProcessedReportFormFieldSpecKeys
from ma_saas.constants.system import TYPE, VALUES, BASENAME, Callable
from ma_saas.constants.company import NOT_ACCEPT_CUS
from reports.models.worker_report import WorkerReport
from companies.models.company_user import CUS_MUST_BE_ACCEPT, NOT_TA_COMPANY_USER_REASON
from reports.permissions.worker_report import (
    WORKER_REPORT_STATUS_MUST_BE_PENDING,
    WORKER_NOT_ALLOWED_TO_UPDATE_REPORT_REWARD,
)
from projects.models.contractor_project_territory_worker import NOT_TA_REQUESTING_PT_WORKER_REASON
from tests.test_app_reports.test_worker_reports.test_update.test_common import __get_response


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_worker__fail(
    api_client,
    mock_policies_false,
    get_cu_worker_fi,
    get_pt_worker_fi,
    get_reservation_fi: Callable,
    get_schedule_time_slot_fi: Callable,
    get_worker_report_fi: Callable,
    status,
):
    r_cu = get_cu_worker_fi(status=status.value)
    requesting_pt_worker = get_pt_worker_fi(company_user=r_cu)
    schedule_time_slot = get_schedule_time_slot_fi(project_territory=requesting_pt_worker.project_territory)
    get_reservation_fi(project_territory_worker=requesting_pt_worker, schedule_time_slot=schedule_time_slot)

    instance = get_worker_report_fi(
        project_territory_worker=requesting_pt_worker, schedule_time_slot=schedule_time_slot
    )
    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=PermissionDenied)
    assert response.data["detail"] == NOT_TA_REQUESTING_PT_WORKER_REASON.format(
        reason=NOT_TA_COMPANY_USER_REASON.format(reason=CUS_MUST_BE_ACCEPT)
    )


@pytest.mark.parametrize("status", [status.value for status in WRS if status != WRS.PENDING])
def test__related_via_reservation_model_owner__update_with_not_pending_status__fail(
    api_client,
    mock_policies_false,
    get_reservation_fi,
    get_cu_worker_fi,
    get_pt_worker_fi,
    get_schedule_time_slot_fi,
    get_worker_report_fi: Callable,
    status,
):
    r_cu = get_cu_worker_fi()
    requesting_pt_worker = get_pt_worker_fi(company_user=r_cu)
    schedule_time_slot = get_schedule_time_slot_fi(project_territory=requesting_pt_worker.project_territory)
    reservation = get_reservation_fi(
        project_territory_worker=requesting_pt_worker, schedule_time_slot=schedule_time_slot
    )

    instance = get_worker_report_fi(
        project_territory_worker=requesting_pt_worker, schedule_time_slot=schedule_time_slot, status=status
    )
    response = __get_response(
        api_client,
        instance.id,
        {},
        reservation.project_territory_worker.company_user.user,
        status_codes=PermissionDenied,
    )
    assert response.data["detail"] == WORKER_REPORT_STATUS_MUST_BE_PENDING


def test__related_via_reservation__model_owner__model_with_pending_status__status_change__success(
    api_client,
    mock_policies_false,
    get_reservation_fi,
    get_cu_worker_fi,
    get_schedule_time_slot_fi,
    get_pt_worker_fi,
    get_worker_report_fi,
):
    r_cu = get_cu_worker_fi()
    requesting_pt_worker = get_pt_worker_fi(company_user=r_cu)
    schedule_time_slot = get_schedule_time_slot_fi(project_territory=requesting_pt_worker.project_territory)
    reservation = get_reservation_fi(
        project_territory_worker=requesting_pt_worker, schedule_time_slot=schedule_time_slot
    )

    instance = get_worker_report_fi(
        project_territory_worker=requesting_pt_worker,
        schedule_time_slot=schedule_time_slot,
        status=WRS.PENDING.value,
    )
    target_status = WRS.LOADED.value
    response = __get_response(
        api_client,
        instance.id,
        {"status": target_status},
        reservation.project_territory_worker.company_user.user,
    )
    assert response.data
    assert response.data["id"] == instance.id
    updated_instance = WorkerReport.objects.get(id=instance.id)
    assert response.data["status"] == updated_instance.status == target_status


@pytest.mark.parametrize(
    "type_",
    (
        ProcessedReportFormFieldSpecKeys.VIDEO,
        ProcessedReportFormFieldSpecKeys.PHOTO,
        ProcessedReportFormFieldSpecKeys.AUDIO,
    ),
)
@pytest.mark.parametrize("is_update_values", (True, False))
@pytest.mark.parametrize("is_update_basename", (True, False))
def test__related_via_reservation__model_owner__update_media_fields__success(
    api_client,
    mock_policies_false,
    get_reservation_fi: Callable,
    get_worker_report_fi: Callable,
    get_cu_worker_fi,
    get_pt_worker_fi,
    get_schedule_time_slot_fi: Callable,
    type_: str,
    is_update_values: bool,
    is_update_basename: bool,
):
    if not is_update_values and not is_update_basename:
        return

    r_cu = get_cu_worker_fi()
    requesting_pt_worker = get_pt_worker_fi(company_user=r_cu)
    schedule_time_slot = get_schedule_time_slot_fi(project_territory=requesting_pt_worker.project_territory)
    reservation = get_reservation_fi(
        project_territory_worker=requesting_pt_worker, schedule_time_slot=schedule_time_slot
    )

    instance = get_worker_report_fi(
        project_territory_worker=requesting_pt_worker,
        schedule_time_slot=schedule_time_slot,
        status=WRS.PENDING.value,
    )
    new_json_fields = list()
    for json_field in instance.json_fields:
        if json_field[TYPE] in type_:
            if is_update_values:
                json_field[VALUES] = [get_random_string()]
            if is_update_basename:
                json_field[BASENAME] = get_random_string()
        new_json_fields.append(json_field)
    response = __get_response(
        api_client,
        data={"json_fields": json.dumps(new_json_fields)},
        instance_id=instance.id,
        user=reservation.project_territory_worker.company_user.user,
        status_codes=status_code.HTTP_200_OK,
    )
    assert response.data
    assert response.data["id"] == instance.id

    assert response.data["json_fields"] == new_json_fields


def test__related_via_reservation__model_owner__update_reward__fail(
    api_client,
    mock_policies_false,
    get_reservation_fi: Callable,
    get_worker_report_fi,
    get_cu_worker_fi,
    get_pt_worker_fi,
    get_schedule_time_slot_fi: Callable,
):

    r_cu = get_cu_worker_fi()
    requesting_pt_worker = get_pt_worker_fi(company_user=r_cu)
    schedule_time_slot = get_schedule_time_slot_fi(project_territory=requesting_pt_worker.project_territory)
    get_reservation_fi(project_territory_worker=requesting_pt_worker, schedule_time_slot=schedule_time_slot)

    instance = get_worker_report_fi(
        project_territory_worker=requesting_pt_worker,
        schedule_time_slot=schedule_time_slot,
        status=WRS.PENDING.value,
    )
    response = __get_response(
        api_client, instance.id, {"reward": 2}, r_cu.user, status_codes=PermissionDenied
    )
    assert response.data["detail"] == WORKER_NOT_ALLOWED_TO_UPDATE_REPORT_REWARD
