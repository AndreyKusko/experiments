import json
import typing as tp
from copy import deepcopy
from random import randrange
from typing import Callable

import pytest
from django.utils.crypto import get_random_string

from projects.models.project import Project
from companies.models.company import Company
from ma_saas.constants.report import ProcessedReportFormFieldSpecKeys
from projects.models.project_scheme import ProjectScheme
from reports.models.processed_report_form import ProcessedReportForm

is_deleted = {"is_deleted": False}
STR1 = {
    "name": "Название",
    "order": 1,
    "type": "str",
    "required": True,
    "many": True,
    "min": 1,
    "max": 3,
    **is_deleted,
}
STR2 = {"name": "Название", "order": 1, "type": "str", "required": False, "many": False, **is_deleted}
CHOICE1 = {
    "name": "Есть свет",
    "order": 1,
    "type": "choice",
    "data": ["поле 1", "поле 2"],
    "required": True,
    **is_deleted,
}
CHOICE2 = {
    "name": "Есть свет",
    "order": 1,
    "type": "choice",
    "data": ["поле 1", "поле 2"],
    "required": False,
    **is_deleted,
}
SELECT1 = {
    "name": "Условия",
    "order": 1,
    "type": "select",
    "data": ["поле 1", "поле 2", "поле 3"],
    "many": True,
    "min": 0,
    "max": 3,
    **is_deleted,
}
SELECT2 = {
    "name": "Условия",
    "order": 1,
    "type": "select",
    "data": ["поле 1", "поле 2", "поле 3"],
    "many": True,
    "min": 1,
    "max": 2,
    **is_deleted,
}
INT1 = {
    "name": "Количество",
    "order": 1,
    "type": "int",
    "required": True,
    "many": True,
    "min": 1,
    "max": 3,
    **is_deleted,
}
INT2 = {"name": "Количество", "order": 1, "type": "int", "required": False, "many": False, **is_deleted}
FLOAT1 = {
    "name": "Цена",
    "order": 1,
    "type": "float",
    "required": True,
    "many": True,
    "min": 1,
    "max": 3,
    **is_deleted,
}
FLOAT2 = {"name": "Цена", "order": 1, "type": "float", "required": False, "many": False, **is_deleted}
CHECK_IN1 = {"name": "Подтверждение точки", "type": "check_in", "order": 1, "required": True, **is_deleted}
CHECK_IN2 = {"name": "Подтверждение точки", "type": "check_in", "order": 1, "required": False, **is_deleted}
COORDINATE = {"name": "Координата", "type": "coordinate", "order": 1, "required": False, "many": True, **is_deleted}


class FrozenDict(dict):
    def __init__(self, *args, **kwargs):
        self._hash = None
        super(FrozenDict, self).__init__(*args, **kwargs)

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(tuple(sorted(self.items())))  # iteritems() on py2
        return self._hash

    def _immutable(self, *args, **kws):
        raise TypeError("cannot change object - object is immutable")

    # makes (deep)copy alot more efficient
    def __copy__(self):
        return self

    def __deepcopy__(self, memo=None):
        if memo is not None:
            memo[id(self)] = self
        return dict(self)

    __setitem__ = _immutable
    __delitem__ = _immutable
    pop = _immutable
    popitem = _immutable
    clear = _immutable
    update = _immutable
    setdefault = _immutable


MEDIA1 = FrozenDict(
    {
        "name": "Медиа",
        "order": 1,
        "type": "media",
        "required": True,
        ProcessedReportFormFieldSpecKeys.PHOTO: 1,
        ProcessedReportFormFieldSpecKeys.VIDEO: 1,
        ProcessedReportFormFieldSpecKeys.AUDIO: 1,
        **is_deleted,
    }
)
MEDIA2 = FrozenDict(
    {
        "name": "Медиа",
        "order": 1,
        "type": "media",
        "required": False,
        ProcessedReportFormFieldSpecKeys.PHOTO: 1,
        ProcessedReportFormFieldSpecKeys.VIDEO: 1,
        ProcessedReportFormFieldSpecKeys.AUDIO: 1,
        **is_deleted,
    }
)
GEO_POINT_NAME1 = {
    "name": "Название точки",
    "order": 1,
    "type": "geo_point_name",
    "required": True,
    **is_deleted,
}
GEO_POINT_NAME2 = {
    "name": "Название точки",
    "order": 1,
    "type": "geo_point_name",
    "required": False,
    **is_deleted,
}
GEO_POINT_ADDRESS1 = {
    "name": "Адрес гео точки",
    "order": 1,
    "type": "geo_point_address",
    "required": True,
    **is_deleted,
}
GEO_POINT_ADDRESS2 = {
    "name": "Адрес гео точки",
    "order": 1,
    "type": "geo_point_address",
    "required": False,
    **is_deleted,
}
created_at_type = {"order": 1, "type": "created_at_format"}
CREATED_AT_FORMAT1 = {"name": "Дата создания", **created_at_type, "format": "%Y-%m-%d", **is_deleted}
CREATED_AT_FORMAT2 = {"name": "Время создания", **created_at_type, "format": "%H:%M:%S", **is_deleted}
CREATED_AT_FORMAT3 = {
    "name": "Дата-время создания",
    **created_at_type,
    "format": "%Y-%m-%d %H:%M:%S",
    **is_deleted,
}
approved_at_type = {"order": 1, "type": "approved_at_format"}
APPROVED_AT_FORMAT1 = {"name": "Дата подтверждения", **approved_at_type, "format": "%Y-%m-%d", **is_deleted}
APPROVED_AT_FORMAT2 = {"name": "Время подтверждения", **approved_at_type, "format": "%H:%M:%S", **is_deleted}
APPROVED_AT_FORMAT3 = {
    "name": "Дата-время подтверждения",
    **approved_at_type,
    "format": "%Y-%m-%d %H:%M:%S",
    **is_deleted,
}
datetime_type = {"order": 1, "type": "datetime"}
DATETIME1 = {"name": "Дата", **datetime_type, "format": "%Y-%m-%d", "required": True, **is_deleted}
DATETIME2 = {"name": "Время", **datetime_type, "format": "%H:%M:%S", "required": True, **is_deleted}
DATETIME3 = {
    "name": "Дата-время not req",
    **datetime_type,
    "format": "%Y-%m-%d %H:%M:%S",
    "required": True,
    **is_deleted,
}
DATETIME4 = {
    "name": "Дата-время req",
    **datetime_type,
    "format": "%Y-%m-%d %H:%M:%S",
    "required": False,
    **is_deleted,
}
SIMPLE_REQUIRED_FIELDS = [
    STR1,
    INT1,
    FLOAT1,
    CHECK_IN1,
    CHOICE1,
    DATETIME1,
    DATETIME2,
    DATETIME3,
    GEO_POINT_NAME1,
    GEO_POINT_ADDRESS1,
    MEDIA1,
]
SIMPLE_NOT_REQUIRED_FIELDS = [
    STR2,
    INT2,
    FLOAT2,
    CHECK_IN2,
    CHOICE2,
    DATETIME4,
    GEO_POINT_NAME2,
    GEO_POINT_ADDRESS2,
    MEDIA2,
]
SELECT_FIELDS = [SELECT1, SELECT2]
CREATED_AT_FIELDS = [CREATED_AT_FORMAT1, CREATED_AT_FORMAT2, CREATED_AT_FORMAT3]
APPROVED_AT_FIELDS = [APPROVED_AT_FORMAT1, APPROVED_AT_FORMAT2, APPROVED_AT_FORMAT3]
AUTO_FIELDS = CREATED_AT_FIELDS + APPROVED_AT_FIELDS
UNIQUE_TYPE_FIELDS = [
    # MEDIA,
    CHECK_IN1,
    CHECK_IN2,
    GEO_POINT_NAME1,
    GEO_POINT_NAME2,
    GEO_POINT_ADDRESS1,
    GEO_POINT_ADDRESS2,
    GEO_POINT_NAME1,
    GEO_POINT_NAME2,
] + AUTO_FIELDS
ALL_FIELDS_SPECS_LIST = (
    SIMPLE_REQUIRED_FIELDS + SIMPLE_NOT_REQUIRED_FIELDS + SELECT_FIELDS + UNIQUE_TYPE_FIELDS
)
ALL_FIELDS_WITH_ID = {field_id: field for field_id, field in enumerate(ALL_FIELDS_SPECS_LIST)}


@pytest.fixture
def updated_processed_report_form_fields_specs_data_fi() -> Callable:
    def return_data(fields_specs: tp.Dict[int, tp.Dict[str, tp.Any]]) -> tp.Dict[int, tp.Dict[str, tp.Any]]:
        copy_fields_specs = deepcopy(fields_specs)
        for spec_data in copy_fields_specs.values():
            spec_data["name"] = get_random_string()
            spec_data["order"] = randrange(10)
            min_ = randrange(10)
            if spec_data.get("many"):
                spec_data["min"] = min_
                spec_data["max"] = min_ + randrange(10)
            for key in (
                ProcessedReportFormFieldSpecKeys.PHOTO,
                ProcessedReportFormFieldSpecKeys.VIDEO,
                ProcessedReportFormFieldSpecKeys.AUDIO,
            ):
                if spec_data.get(key):
                    spec_data[key] = randrange(100)
        return fields_specs

    return return_data


@pytest.fixture
def new_processed_report_form_data(get_project_scheme_fi) -> Callable:
    def return_data(
        fields_specs: tp.Dict[int, tp.Dict[str, tp.Any]] = None,
        project_scheme: tp.Optional[ProjectScheme] = None,
        project: tp.Optional[Project] = None,
        company: tp.Optional[Company] = None,
        _is_relations_ids: bool = True,
    ) -> tp.Dict[str, tp.Any]:
        if not project_scheme:
            if project:
                project_scheme = get_project_scheme_fi(project=project)
            elif company:
                project_scheme = get_project_scheme_fi(company=company)
            else:
                project_scheme = get_project_scheme_fi()

        fields_specs = fields_specs or {}
        data = {"fields_specs": json.dumps(fields_specs)}
        relation_data = {"project_scheme": project_scheme}
        if _is_relations_ids:
            relation_data = {k: v.id for k, v in relation_data.items()}
        data.update(relation_data)
        return data

    return return_data


@pytest.fixture
def get_processed_report_form_fi(
    new_processed_report_form_data: Callable,
) -> Callable[..., ProcessedReportForm]:
    def get_or_create_instance(*args, **kwargs) -> ProcessedReportForm:
        data = new_processed_report_form_data(*args, _is_relations_ids=False, **kwargs)
        data["fields_specs"] = json.loads(data["fields_specs"])
        instance = ProcessedReportForm.objects.create(**data)
        return instance

    return get_or_create_instance


@pytest.fixture
def processed_report_form_fi(get_processed_report_form_fi) -> ProcessedReportForm:
    return get_processed_report_form_fi()
