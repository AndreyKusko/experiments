import json
import typing as tp
import datetime as dt
from random import randrange
from typing import Callable

import pytest
from django.utils.crypto import get_random_string

from companies.models.company import Company
from ma_saas.constants.report import (
    WorkerReportStatus,
    ProcessedReportStatus,
    ProcessedReportFormFieldSpecKeys,
    ProcessedReportFormFieldSpecTypes,
)
from ma_saas.constants.system import TYPE
from reports.models.worker_report import WorkerReport
from companies.models.company_user import CompanyUser
from reports.models.processed_report import ProcessedReport
from projects.models.project_territory import ProjectTerritory
from reports.models.processed_report_form import ProcessedReportForm


@pytest.fixture
def new_processed_report_data_fi(
    get_cu_fi,
    get_worker_report_fi: Callable,
    get_project_territory_fi: Callable,
    get_processed_report_form_fi: Callable,
    get_processed_report_media_fields_fi,
    get_schedule_time_slot_fi,
    get_reservation_fi,
) -> Callable:
    def return_data(
        company: tp.Optional[Company] = None,
        company_user: tp.Optional[CompanyUser] = None,
        worker_report: tp.Optional[WorkerReport] = None,
        processed_report_form: tp.Optional[ProcessedReportForm] = None,
        project_territory: tp.Optional[ProjectTerritory] = None,
        comment: tp.Optional[str] = None,
        status: tp.Optional[int] = None,
        partner_status: tp.Optional[int] = None,
        json_fields: tp.Dict[str, tp.Any] = None,
        _is_relations_ids: bool = True,
    ) -> tp.Dict[str, tp.Any]:
        if not project_territory:
            if worker_report:
                project_territory = worker_report.schedule_time_slot.geo_point.project_territory
            elif processed_report_form:
                project_territory = get_project_territory_fi(
                    project=processed_report_form.project_scheme.project
                )
            elif company_user:
                project_territory = get_project_territory_fi(company=company_user.company)
            elif company:
                project_territory = get_project_territory_fi(company=company)
            else:
                project_territory = get_project_territory_fi()

        project = project_territory.project
        if not processed_report_form:
            processed_report_form = get_processed_report_form_fi(project=project)
        if not company_user:
            company_user = get_cu_fi(company=project.company)

        if not worker_report:
            schedule_time_slot = get_schedule_time_slot_fi(
                project_territory=project_territory, project_scheme=processed_report_form.project_scheme
            )
            reservation = get_reservation_fi(
                project_territory=project_territory, schedule_time_slot=schedule_time_slot
            )
            worker_report = get_worker_report_fi(
                project_territory_worker=reservation.project_territory_worker,
                schedule_time_slot=schedule_time_slot,
                status=WorkerReportStatus.ACCEPTED.value,
            )

        data = {
            "status": status or ProcessedReportStatus.ACCEPTED.value,
            "comment": comment or get_random_string(),
        }
        if partner_status:
            data["partner_status"] = partner_status
        # json_fields = json_fields or {
        #     "1": get_processed_report_media_fields_fi(fields_specs=processed_report_form.fields_specs)
        # }
        json_fields = json_fields or {}
        data["json_fields"] = json.dumps(json_fields)

        relation_data = {
            "processed_report_form": processed_report_form,
            "worker_report": worker_report,
            "company_user": company_user,  # we do not use company_user from front in model creating
        }
        if _is_relations_ids:
            relation_data = {k: v.id for k, v in relation_data.items()}
        data.update(relation_data)
        return data

    return return_data


@pytest.fixture
def get_processed_report_fi(new_processed_report_data_fi) -> Callable[..., ProcessedReport]:
    def get_or_create_instance(*args, **kwargs) -> ProcessedReport:
        data = new_processed_report_data_fi(*args, _is_relations_ids=False, **kwargs)
        data["json_fields"] = json.loads(data["json_fields"])
        instance = ProcessedReport.objects.create(**data)
        return instance

    return get_or_create_instance


@pytest.fixture
def processed_report_fi(get_processed_report_fi) -> ProcessedReport:
    return get_processed_report_fi()


@pytest.fixture
def generate_processed_report_field_fi() -> Callable:
    def form_data(
        field_spec: tp.Dict[str, tp.Any], values_qty: tp.Optional[int] = None
    ) -> tp.Union[tp.Dict[str, tp.List[str]], tp.List[tp.Union[str, int, float, tp.List]]]:
        field_spec_type = field_spec["type"]
        if field_spec_type == ProcessedReportFormFieldSpecTypes.MEDIA:
            return {
                ProcessedReportFormFieldSpecKeys.PHOTO: [get_random_string()],
                ProcessedReportFormFieldSpecKeys.VIDEO: [get_random_string()],
                ProcessedReportFormFieldSpecKeys.AUDIO: [get_random_string()],
            }

        if field_spec_type == ProcessedReportFormFieldSpecTypes.STR:
            if values_qty:
                return [get_random_string() for _ in range(values_qty)]
            return [get_random_string()]

        if field_spec_type == ProcessedReportFormFieldSpecTypes.INT:
            if values_qty:
                return [randrange(10) for _ in range(values_qty)]
            return [randrange(10)]

        if field_spec_type == ProcessedReportFormFieldSpecTypes.FLOAT:
            if values_qty:
                return [float(randrange(10)) for _ in range(values_qty)]
            return [float(randrange(10))]
        if field_spec_type == ProcessedReportFormFieldSpecTypes.CHECK_IN:
            return [float(randrange(10)), float(randrange(10))]

        if field_spec_type == ProcessedReportFormFieldSpecTypes.CHOICE:
            return [field_spec["data"][0]]

        if field_spec_type == ProcessedReportFormFieldSpecTypes.SELECT:
            if values_qty is not None:
                return [field_spec["data"][index] for index in range(values_qty)]
            return [field_spec["data"][0]]

        if field_spec_type == ProcessedReportFormFieldSpecTypes.DATETIME:
            return [dt.datetime.utcnow().strftime(field_spec["format"])]

        if field_spec_type in ProcessedReportFormFieldSpecTypes.GEO_POINT_ADDRESS:
            return [get_random_string()]

        if field_spec_type == ProcessedReportFormFieldSpecTypes.GEO_POINT_NAME:
            return [get_random_string()]

        return []

    return form_data


@pytest.fixture
def processed_report_media_field_fi() -> tp.Dict[str, tp.Dict[str, tp.List[str]]]:
    return {
        "values": {
            ProcessedReportFormFieldSpecKeys.PHOTO: [get_random_string()],
            ProcessedReportFormFieldSpecKeys.VIDEO: [get_random_string()],
            ProcessedReportFormFieldSpecKeys.AUDIO: [get_random_string()],
        }
    }


@pytest.fixture
def get_processed_report_media_fields_fi():
    def form_data(fields_specs):
        media_field = dict()
        for field_id, field_data in fields_specs.items():
            if field_data[TYPE] == ProcessedReportFormFieldSpecTypes.MEDIA:
                media_field = field_data
        photo_key = ProcessedReportFormFieldSpecKeys.PHOTO
        video_key = ProcessedReportFormFieldSpecKeys.VIDEO
        audio_key = ProcessedReportFormFieldSpecKeys.AUDIO
        return {
            "values": {
                photo_key: [get_random_string() for _ in range(media_field[photo_key] or 1)],
                video_key: [get_random_string() for _ in range(media_field[video_key] or 1)],
                audio_key: [get_random_string() for _ in range(media_field[audio_key] or 1)],
            }
        }

    return form_data
