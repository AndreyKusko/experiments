import typing as tp
import datetime as dt
from typing import Callable

import pytest

from ma_saas.utils import system
from geo_objects.models import GeoPoint
from tasks.models.utils import get_active_till_data, get_active_since_data
from projects.models.project import Project
from companies.models.company import Company
from projects.models.project_scheme import ProjectScheme
from tasks.models.schedule_time_slot import ScheduleTimeSlot
from projects.models.project_territory import ProjectTerritory


@pytest.fixture
def new_schedule_time_slot_data(get_geo_point_fi, get_project_scheme_fi) -> Callable:
    def return_data(
        company: tp.Optional[Company] = None,
        project: tp.Optional[Project] = None,
        geo_point: tp.Optional[GeoPoint] = None,
        project_scheme: tp.Optional[ProjectScheme] = None,
        project_territory: tp.Optional[ProjectTerritory] = None,
        reward: tp.Optional[int] = 0,
        active_since_date_local=None,
        active_since_time_local=None,
        active_till_date_local=None,
        active_till_time_local=None,
        max_reports_qty: int = 1,
        is_allow_create_reports: bool = True,
        _is_relations_ids: bool = True,
    ) -> tp.Dict[str, tp.Any]:
        if not geo_point:
            if project_territory:
                geo_point = get_geo_point_fi(project_territory=project_territory)
            elif project_scheme:
                geo_point = get_geo_point_fi(project=project_scheme.project)
            elif project:
                geo_point = get_geo_point_fi(project=project)
            elif company:
                geo_point = get_geo_point_fi(company=company)
            else:
                geo_point = get_geo_point_fi()

        if not project_scheme:
            if geo_point:
                project_scheme = get_project_scheme_fi(project=geo_point.project_territory.project)
            elif project_territory:
                project_scheme = get_project_scheme_fi(project=project_territory.project)
            elif project:
                project_scheme = get_project_scheme_fi(project=project)
            elif company:
                project_scheme = get_project_scheme_fi(company=company)
            else:
                project_scheme = get_project_scheme_fi()

        data = {
            "reward": reward,
            "max_reports_qty": max_reports_qty,
            "is_allow_create_reports": is_allow_create_reports,
        }

        relation_data = {"geo_point": geo_point, "project_scheme": project_scheme}
        if _is_relations_ids:
            relation_data = {k: v.id for k, v in relation_data.items()}
        now = system.get_now()
        if not active_since_date_local and not active_since_time_local:
            active_since_local = now + dt.timedelta(hours=float(geo_point.utc_offset))
            active_since_date_local = active_since_local.date()
            active_since_time_local = active_since_local.time()
        if not active_till_date_local and not active_till_time_local:
            active_till_local = (
                now + dt.timedelta(seconds=2) + dt.timedelta(hours=float(geo_point.utc_offset))
            )
            active_till_date_local = active_till_local.date()
            active_till_time_local = active_till_local.time()

        date_data = {
            "active_since_date_local": active_since_date_local,
            "active_since_time_local": active_since_time_local,
            "active_till_date_local": active_till_date_local,
            "active_till_time_local": active_till_time_local,
        }
        # date_data["active_since"] = get_active_since_data(
        #     geo_point.utc_offset, date_data["active_since_local"], _is_allow_past=True
        # )
        # date_data["active_till"] = get_active_till_data(
        #     geo_point.utc_offset, date_data["active_till_local"], _is_allow_past=True
        # )
        if not date_data:
            date_data = {k: str(v) for k, v in date_data.items()}

        return {**data, **relation_data, **date_data}

    return return_data


@pytest.fixture
def get_schedule_time_slot_fi(new_schedule_time_slot_data: Callable) -> Callable[..., ScheduleTimeSlot]:
    def create_instance(*args, **kwargs) -> ScheduleTimeSlot:
        data = new_schedule_time_slot_data(_is_relations_ids=False, *args, **kwargs)
        instance = ScheduleTimeSlot.objects.create(**data)
        return instance

    return create_instance


@pytest.fixture
def schedule_time_slot_fi(get_schedule_time_slot_fi: Callable) -> ScheduleTimeSlot:
    return get_schedule_time_slot_fi()
