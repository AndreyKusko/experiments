import pytest
import requests
from rest_framework.status import HTTP_202_ACCEPTED, HTTP_400_BAD_REQUEST

from background.models import BackgroundTask
from tests.mocked_instances import MockResponse
from clients.objects_store.interface import LOAD_OBJ_ERROR_400
from ma_saas.constants.background_task import BackgroundTaskStatus
from ma_saas.constants.background_task import BackgroundTaskFileTypes as BTFT
from ma_saas.constants.background_task import BackgroundTaskParamsKeys as BTParamsKeys
from background.tasks.for_export.schedule_time_slots import export_schedule_time_slots_task
from tests.test_app_background.test_export.test_schedule_time_slots.constants import MODEL_N_TYPE

_task = export_schedule_time_slots_task


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("file_type", [BTFT.xlsx.value])
def test__owner_export_processed_reports__output_files(
    monkeypatch, r_cu, get_background_task_fi, get_schedule_time_slot_fi, file_type
):
    __return_data = {"result": {"objstore_id": "234"}}
    __mock_response = MockResponse(status_code=HTTP_202_ACCEPTED, data=__return_data)
    monkeypatch.setattr(requests, "post", lambda *a, **kw: __mock_response)

    export_instance = get_schedule_time_slot_fi(company=r_cu.company)
    params = {BTParamsKeys.IDS: [export_instance.id], BTParamsKeys.OUTPUT_FILE_TYPE: file_type}
    instance = get_background_task_fi(company_user=r_cu, params=params, **MODEL_N_TYPE, output_files=[])
    _task.run(background_task_id=instance.id)

    updated_instance = BackgroundTask.objects.get(id=instance.id)
    assert not any([updated_instance.failures, updated_instance.result, updated_instance.input_files])
    assert len(updated_instance.output_files) == 1
    assert updated_instance.status == BackgroundTaskStatus.COMPLETED.value


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("file_type", [BTFT.xlsx.value])
def test__request_microservice__failures(
    monkeypatch, r_cu, get_background_task_fi, get_schedule_time_slot_fi, file_type
):
    __mock_response = MockResponse(status_code=HTTP_400_BAD_REQUEST, text="Текст ошибки")
    monkeypatch.setattr(requests, "post", lambda *a, **kw: __mock_response)

    export_instance = get_schedule_time_slot_fi(company=r_cu.company)
    params = {BTParamsKeys.IDS: [export_instance.id], BTParamsKeys.OUTPUT_FILE_TYPE: file_type}
    instance = get_background_task_fi(company_user=r_cu, params=params, **MODEL_N_TYPE, output_files=[])
    _task.run(background_task_id=instance.id)

    updated_instance = BackgroundTask.objects.get(id=instance.id)
    assert not any([updated_instance.input_files, updated_instance.output_files, updated_instance.result])
    assert updated_instance.failures == [LOAD_OBJ_ERROR_400]
