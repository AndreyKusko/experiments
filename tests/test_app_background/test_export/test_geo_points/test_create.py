import typing as tp
import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, PermissionDenied

from tests.utils import request_response_create
from background.models import BackgroundTask
from ma_saas.constants.company import NOT_ACCEPT_CUS
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_MUST_BE_ACCEPT
from ma_saas.constants.background_task import BackgroundTaskFileTypes as BTFT
from ma_saas.constants.background_task import BackgroundTaskParamsKeys as BTParamsKeys
from background.serializers.background_task import OUTPUT_TYPE_MUST_BE_INT
from background.serializers.validators.main import (
    EXTRA_KEYS_FAILS,
    IDS_MUST_BE_LIST,
    MISSED_KEYS_FAILS,
    IDS_VALUE_MUST_BE_INT,
    OUTPUT_FILE_TYPE_NOT_ALLOWED,
)
from background.tasks.for_export.geo_points import export_geo_points_task
from background.serializers.for_export.geo_points import ExportGeoPointsSerializer
from tests.test_app_background.test_export.test_geo_points.constants import PATH, TASK_TYPE, MODEL_NAME

User = get_user_model()

__get_response = functools.partial(request_response_create, path=PATH)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(
    api_client, mock_policies_false, monkeypatch, r_cu, new_background_task_data, get_geo_point_fi
):
    monkeypatch.setattr(export_geo_points_task, "delay", lambda *a, **k: None)

    export_instance = get_geo_point_fi(company=r_cu.company)
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()

    params = {BTParamsKeys.IDS: [export_instance.id], BTParamsKeys.OUTPUT_FILE_TYPE: BTFT.xlsx.value}
    data = new_background_task_data(company=r_cu.company, params=params)

    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instance = BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE)
    assert len(created_instance) == 1
    assert response.data["id"] == created_instance.first().id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__fail(
    api_client, monkeypatch, get_cu_owner_fi, new_background_task_data, get_geo_point_fi, status
):
    monkeypatch.setattr(export_geo_points_task, "delay", lambda *a, **k: None)
    r_cu = get_cu_owner_fi(status=status)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **k: True)

    export_instance = get_geo_point_fi(company=r_cu.company)
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()

    params = {BTParamsKeys.IDS: [export_instance.id], BTParamsKeys.OUTPUT_FILE_TYPE: BTFT.xlsx.value}
    data = new_background_task_data(company=r_cu.company, params=params)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager_with_policy__success(
    api_client, monkeypatch, r_cu, new_background_task_data, get_geo_point_fi
):
    monkeypatch.setattr(export_geo_points_task, "delay", lambda *a, **k: None)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **k: True)

    export_instance = get_geo_point_fi(company=r_cu.company)
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()

    params = {BTParamsKeys.IDS: [export_instance.id], BTParamsKeys.OUTPUT_FILE_TYPE: BTFT.xlsx.value}
    data = new_background_task_data(company=r_cu.company, params=params)

    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instance = BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE)
    assert len(created_instance) == 1
    assert response.data["id"] == created_instance.first().id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_manager_with_policy__fail(
    api_client, monkeypatch, get_cu_manager_fi, new_background_task_data, get_geo_point_fi, status
):
    monkeypatch.setattr(export_geo_points_task, "delay", lambda *a, **k: None)
    r_cu = get_cu_manager_fi(status=status)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **k: True)

    export_instance = get_geo_point_fi(company=r_cu.company)
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()

    params = {BTParamsKeys.IDS: [export_instance.id], BTParamsKeys.OUTPUT_FILE_TYPE: BTFT.xlsx.value}
    data = new_background_task_data(company=r_cu.company, params=params)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager_without_policy__fail(
    api_client, mock_policies_false, monkeypatch, r_cu, new_background_task_data, get_geo_point_fi
):
    monkeypatch.setattr(export_geo_points_task, "delay", lambda *a, **k: None)

    export_instance = get_geo_point_fi(company=r_cu.company)
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()

    params = {BTParamsKeys.IDS: [export_instance.id], BTParamsKeys.OUTPUT_FILE_TYPE: BTFT.xlsx.value}
    data = new_background_task_data(company=r_cu.company, params=params)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PermissionDenied.default_detail}
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__another_company__fail(
    api_client,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_geo_point_fi,
):
    monkeypatch.setattr(export_geo_points_task, "delay", lambda *a, **k: None)

    export_instance = get_geo_point_fi()
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()

    params = {BTParamsKeys.IDS: [export_instance.id], BTParamsKeys.OUTPUT_FILE_TYPE: BTFT.xlsx.value}
    data = new_background_task_data(company=r_cu.company, params=params)

    assert __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__extra_keys__fails(api_client, monkeypatch, r_cu, new_background_task_data, get_geo_point_fi):
    monkeypatch.setattr(export_geo_points_task, "delay", lambda *a, **k: None)
    extra_key = "qwe"
    export_instance = get_geo_point_fi(company=r_cu.company)
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()

    params = {
        BTParamsKeys.IDS: [export_instance.id],
        BTParamsKeys.OUTPUT_FILE_TYPE: BTFT.xlsx.value,
        extra_key: "qwe",
    }
    data = new_background_task_data(company=r_cu.company, params=params)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == {"params": [EXTRA_KEYS_FAILS.format(extra_keys=", ".join([extra_key]))]}
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("missed_key", [BTParamsKeys.IDS, BTParamsKeys.OUTPUT_FILE_TYPE])
def test__missed_keys__fails(
    api_client, monkeypatch, r_cu, new_background_task_data, get_geo_point_fi, missed_key: str
):
    monkeypatch.setattr(export_geo_points_task, "delay", lambda *a, **k: None)

    export_instance = get_geo_point_fi(company=r_cu.company)
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()

    params = {BTParamsKeys.IDS: [export_instance.id], BTParamsKeys.OUTPUT_FILE_TYPE: BTFT.xlsx.value}
    params.pop(missed_key)
    data = new_background_task_data(company=r_cu.company, params=params)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == {"params": [MISSED_KEYS_FAILS.format(missed_keys=missed_key)]}
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("output_file_type", "err_text"),
    [
        ("qwe", OUTPUT_TYPE_MUST_BE_INT),
        (
            BTFT.zip.value,
            OUTPUT_FILE_TYPE_NOT_ALLOWED.format(
                file_types=", ".join([str(v) for v in ExportGeoPointsSerializer._file_types]),
                requested_value=BTFT.zip.value,
            ),
        ),
        (
            BTFT.csv.value,
            OUTPUT_FILE_TYPE_NOT_ALLOWED.format(
                file_types=", ".join([str(v) for v in ExportGeoPointsSerializer._file_types]),
                requested_value=BTFT.csv.value,
            ),
        ),
    ],
)
def test__invalid_output_file_type__fails(
    api_client,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_geo_point_fi,
    output_file_type,
    err_text,
):
    monkeypatch.setattr(export_geo_points_task, "delay", lambda *a, **k: None)

    export_instance = get_geo_point_fi(company=r_cu.company)
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()

    params = {BTParamsKeys.IDS: [export_instance.id], BTParamsKeys.OUTPUT_FILE_TYPE: output_file_type}
    data = new_background_task_data(company=r_cu.company, params=params)

    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == {"params": [err_text]}
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("ids_values", "err_text"),
    (
        ({1: 1}, IDS_MUST_BE_LIST),
        ("123", IDS_MUST_BE_LIST),
        (1, IDS_MUST_BE_LIST),
        ([1, "qwe"], IDS_VALUE_MUST_BE_INT.format(value="qwe")),
        (["qwe"], IDS_VALUE_MUST_BE_INT.format(value="qwe")),
        ([{1: 2}], IDS_VALUE_MUST_BE_INT.format(value={"1": 2})),
    ),
)
def test__not_int_output_type__fails(
    api_client,
    monkeypatch,
    r_cu,
    new_background_task_data,
    ids_values: tp.Any,
    err_text: str,
):
    monkeypatch.setattr(export_geo_points_task, "delay", lambda *a, **k: None)

    params = {BTParamsKeys.IDS: ids_values, BTParamsKeys.OUTPUT_FILE_TYPE: BTFT.xlsx.value}
    data = new_background_task_data(company=r_cu.company, params=params)

    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == {"params": [err_text]}
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("file_type", [BTFT.xlsx.value])
def test__response_data(
    api_client,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_geo_point_fi,
    file_type: int,
):
    monkeypatch.setattr(export_geo_points_task, "delay", lambda *a, **k: None)
    export_instance = get_geo_point_fi(company=r_cu.company)
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()

    params = {BTParamsKeys.IDS: [export_instance.id], BTParamsKeys.OUTPUT_FILE_TYPE: file_type}
    data = new_background_task_data(company=r_cu.company, params=params)

    response = __get_response(api_client, data=data, user=r_cu.user)
    response_instance = response.data

    created_instance = BackgroundTask.objects.get(id=response_instance.pop("id"))

    assert response_instance.pop("params") == created_instance.params == params
    assert response_instance.pop("input_files") == created_instance.input_files
    assert response_instance.pop("result") == created_instance.result
    assert len(created_instance.failures) == 0
    assert response_instance.pop("failures") == created_instance.failures

    assert response_instance.pop("model_name") == created_instance.model_name
    assert created_instance.model_name == MODEL_NAME

    assert response_instance.pop("task_type") == created_instance.task_type
    assert created_instance.task_type == TASK_TYPE

    assert not response_instance.pop("output_files")
    assert not created_instance.output_files

    assert response_instance.pop("company") == created_instance.company.id
    assert response_instance.pop("company_user") == created_instance.company_user.id
    assert response_instance.pop("status") == created_instance.status
    assert response_instance.pop("created_at")
    assert response_instance.pop("updated_at")
    assert not response_instance
