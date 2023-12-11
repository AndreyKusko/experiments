import json
import typing as tp
from typing import Callable

import pytest
from django.utils.crypto import get_random_string

from geo_objects.models import GeoPoint
from projects.models.project import Project
from companies.models.company import Company
from projects.models.territory import Territory
from projects.models.project_territory import ProjectTerritory


@pytest.fixture
def new_geo_point_data(
    get_company_fi, get_project_territory_fi: Callable, get_territory_fi: Callable, get_project_fi
) -> Callable:
    def return_data(
        company: tp.Optional[Company] = None,
        project: tp.Optional[Project] = None,
        territory: tp.Optional[Project] = None,
        project_territory: tp.Optional[Territory] = None,
        title: tp.Optional[str] = None,
        lat: tp.Optional[float] = 55.7522200,
        lon: tp.Optional[float] = 37.6155600,
        address: tp.Optional[str] = "Россия, г. Москва, Тверская площадь, дом 1",
        city: tp.Optional[str] = "",
        reward: tp.Optional[int] = 111,
        additional: tp.Optional[tp.Dict[str, tp.Any]] = None,
        utc_offset: int = 3.0,
        is_active: bool = True,
    ) -> tp.Dict[str, tp.Any]:
        title = title or get_random_string()
        lat = lat or float(1)
        lon = lon or float(1)
        address = address or "г. Москва, улица Краснопресненская, дом 16"

        if not project_territory:
            if not company:
                if project:
                    company = project.company
                elif territory:
                    company = territory.company
                else:
                    company = get_company_fi()
            project_territory = get_project_territory_fi(
                company=company,
                project=project or get_project_fi(company=company),
                territory=territory or get_territory_fi(company=company),
            )
        data = {
            "project_territory": project_territory.id,
            "title": title,
            "is_active": is_active,
            "reward": reward,
            "lat": lat,
            "lon": lon,
            "address": address,
            "city": city or "Москва",
            "utc_offset": utc_offset,
        }
        if additional:
            data["additional"] = additional
        if additional == "":
            data["additional"] = None
        return data

    return return_data


@pytest.fixture
def get_geo_point_fi(new_geo_point_data: Callable) -> Callable:
    def create_instance(*args, **kwargs) -> GeoPoint:
        data = new_geo_point_data(*args, **kwargs)
        data["project_territory"] = ProjectTerritory.objects.get(id=data["project_territory"])
        if additional := data.get("additional"):
            data["additional"] = json.loads(additional)
        instance = GeoPoint.objects.create(**data)
        return instance

    return create_instance


@pytest.fixture
def geo_point_fi(get_geo_point_fi: Callable) -> GeoPoint:
    return get_geo_point_fi()
