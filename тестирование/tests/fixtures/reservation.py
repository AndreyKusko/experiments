import typing as tp
import datetime as dt
from typing import Callable

import pytest

from ma_saas.utils import system
from geo_objects.models import GeoPoint
from tasks.models.utils import get_active_till_data, get_active_since_data
from projects.models.project import Project
from companies.models.company import Company
from tasks.models.reservation import Reservation
from tasks.models.schedule_time_slot import ScheduleTimeSlot
from projects.models.project_territory import ProjectTerritory
from projects.models.contractor_project_territory_worker import ContractorProjectTerritoryWorker


@pytest.fixture
def new_reservation_data(get_pt_worker_fi, get_geo_point_fi: Callable) -> Callable:
    def return_data(
        company: tp.Optional[Company] = None,
        project: tp.Optional[Project] = None,
        project_territory: tp.Optional[ProjectTerritory] = None,
        project_territory_worker: tp.Optional[ContractorProjectTerritoryWorker] = None,
        geo_point: tp.Optional[GeoPoint] = None,
        schedule_time_slot: tp.Optional[ScheduleTimeSlot] = None,
        active_since_local=None,
        active_till_local=None,
        _is_relations_ids: bool = True,
        **kwargs,
    ) -> tp.Dict[str, tp.Any]:

        if not geo_point:
            if schedule_time_slot:
                geo_point = schedule_time_slot.geo_point
            elif project_territory_worker:
                geo_point = get_geo_point_fi(project_territory=project_territory_worker.project_territory)
            elif project_territory:
                geo_point = get_geo_point_fi(project_territory=project_territory)
            elif project:
                geo_point = get_geo_point_fi(project=project)
            elif company:
                geo_point = get_geo_point_fi(company=company)
            else:
                geo_point = get_geo_point_fi()
        if not project_territory_worker:
            project_territory_worker = get_pt_worker_fi(project_territory=geo_point.project_territory)

        data = {}
        now = system.get_now()
        if not active_since_local:
            active_since_local = now + dt.timedelta(hours=float(geo_point.utc_offset))

        if not active_till_local:
            active_till_local = (
                now + dt.timedelta(hours=float(geo_point.utc_offset)) + dt.timedelta(days=1, hours=1)
            )
        date_data = {"active_since_local": active_since_local, "active_till_local": active_till_local}
        date_data["active_since"] = get_active_since_data(
            geo_point.utc_offset, active_since_local, _is_allow_past=True
        )
        date_data["active_till"] = get_active_till_data(
            geo_point.utc_offset, active_till_local, _is_allow_past=True
        )
        if not date_data:
            date_data = {k: str(v) for k, v in date_data.items()}

        relation_data = {"geo_point": geo_point}
        if project_territory_worker:
            relation_data["project_territory_worker"] = project_territory_worker
        if schedule_time_slot:
            relation_data["schedule_time_slot"] = schedule_time_slot
        if _is_relations_ids:
            relation_data = {k: v.id for k, v in relation_data.items()}

        return {**data, **date_data, **relation_data}

    return return_data


@pytest.fixture
def get_reservation_fi(new_reservation_data: Callable) -> Callable[..., Reservation]:
    def get_or_create_instance(*args, **kwargs) -> Reservation:
        data = new_reservation_data(_is_relations_ids=False, *args, **kwargs)
        instance = Reservation.objects.create(**data)
        return instance

    return get_or_create_instance


@pytest.fixture
def reservation_fi(get_reservation_fi) -> Reservation:
    return get_reservation_fi()
