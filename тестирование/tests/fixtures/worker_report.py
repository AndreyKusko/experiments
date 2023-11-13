import json
import typing as tp
from random import randrange
from typing import Callable

import pytest
from django.utils.crypto import get_random_string

from companies.models.company import Company
from ma_saas.constants.report import WorkerReportStatus, ProcessedReportFormFieldSpecKeys
from ma_saas.constants.system import TYPE, VALUES, BASENAME
from tasks.models.reservation import Reservation
from reports.models.worker_report import WorkerReport
from companies.models.company_user import CompanyUser
from projects.models.project_scheme import ProjectScheme
from tasks.models.schedule_time_slot import ScheduleTimeSlot
from projects.models.project_territory import ProjectTerritory
from projects.models.contractor_project_territory_worker import ContractorProjectTerritoryWorker


@pytest.fixture
def new_worker_report_data(
    get_company_fi: Callable,
    get_project_scheme_fi: Callable,
    get_pt_worker_fi,
    get_project_territory_fi: Callable,
    get_schedule_time_slot_fi: Callable,
    get_reservation_fi: Callable,
) -> Callable:
    def return_data(
        company: tp.Optional[Company] = None,
        project_territory: tp.Optional[ProjectTerritory] = None,
        schedule_time_slot: tp.Optional[ScheduleTimeSlot] = None,
        company_user: tp.Optional[CompanyUser] = None,
        project_territory_worker: tp.Optional[ContractorProjectTerritoryWorker] = None,
        project_scheme: tp.Optional[ProjectScheme] = None,
        reward: tp.Optional[int] = None,
        status: tp.Optional[int] = None,
        json_fields: tp.Dict[str, tp.Any] = None,
        comment: tp.Optional[str] = "",
        is_create=True,
        _is_relations_ids: bool = True,
        **kwargs,
    ) -> tp.Dict[str, tp.Any]:

        if not project_territory:
            if project_territory_worker:
                project_territory = project_territory_worker.project_territory
            elif schedule_time_slot:
                project_territory = schedule_time_slot.geo_point.project_territory
            elif company_user:
                project_territory = get_project_territory_fi(company=company_user.company)
            elif company:
                project_territory = get_project_territory_fi(company=company)
            else:
                project_territory = get_project_territory_fi()

        if not project_territory_worker:
            if company_user:
                project_territory_worker = get_pt_worker_fi(
                    company_user=company_user, project_territory=project_territory
                )
            else:
                project_territory_worker = get_pt_worker_fi(project_territory=project_territory)

        if not project_scheme:
            if schedule_time_slot:
                project_scheme = schedule_time_slot.project_scheme
            else:
                project_scheme = get_project_scheme_fi(project=project_territory.project)

        if not schedule_time_slot:
            schedule_time_slot = get_schedule_time_slot_fi(
                project_territory=project_territory, project_scheme=project_scheme
            )

        data = {
            "status": status or WorkerReportStatus.LOADED.value,
            "reward": reward or randrange(100),
            "comment": comment,
            **kwargs,
        }

        if not _is_relations_ids:
            if not Reservation.objects.filter(
                project_territory_worker=project_territory_worker, schedule_time_slot=schedule_time_slot
            ).exists():
                get_reservation_fi(
                    project_territory_worker=project_territory_worker, schedule_time_slot=schedule_time_slot
                )

        relation_data = {
            "company_user": project_territory_worker.company_user,
            "schedule_time_slot": schedule_time_slot,
            "project_scheme": project_scheme,
        }
        if _is_relations_ids:
            relation_data = {k: v.id for k, v in relation_data.items()}
            data.update(relation_data)

        if not json_fields:
            # здесь медиа поле в виде, когда данные первый раз посылаются на сервак,
            # возвращаюются в таком виде, только каждому медиаполю добавлятся еще и object_id

            json_fields = [
                {TYPE: "price", VALUES: [randrange(100)]},
                {TYPE: ProcessedReportFormFieldSpecKeys.PHOTO, BASENAME: "123123123.png"},
                {TYPE: ProcessedReportFormFieldSpecKeys.VIDEO, BASENAME: "123123124.png"},
                {TYPE: ProcessedReportFormFieldSpecKeys.AUDIO, BASENAME: "123123125.png"},
            ]
            if not is_create:
                for field in json_fields:
                    field[VALUES] = [get_random_string()]
        data["json_fields"] = json.dumps(json_fields)
        return {**data, **relation_data}

    return return_data


@pytest.fixture
def get_worker_report_fi(new_worker_report_data: Callable) -> Callable[..., WorkerReport]:
    def get_or_create_instance(*args, **kwargs) -> WorkerReport:

        data = new_worker_report_data(_is_relations_ids=False, *args, **kwargs)
        json_fields = json.loads(data["json_fields"])
        for json_field in json_fields:
            if json_field[TYPE] in ProcessedReportFormFieldSpecKeys.media and not json_field.get(VALUES):
                json_field[VALUES] = [get_random_string()]

        data["json_fields"] = json_fields

        created_instance = WorkerReport.objects.create(**data)
        instance = WorkerReport.objects.get(id=created_instance.id)

        return instance

    return get_or_create_instance


@pytest.fixture
def worker_report_fi(get_worker_report_fi) -> WorkerReport:
    return get_worker_report_fi()
