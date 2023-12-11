import json
from typing import Callable

import pytest
import requests
from rest_framework.status import HTTP_202_ACCEPTED, HTTP_400_BAD_REQUEST

from tests.utils import get_random_int
from background.models import BackgroundTask
from tests.mocked_instances import MockResponse
from companies.models.company_user import CompanyUser
from clients.objects_store.interface import LOAD_OBJ_ERROR_400
from ma_saas.constants.background_task import BackgroundTaskStatus
from ma_saas.constants.background_task import BackgroundTaskFileTypes as BTFT
from ma_saas.constants.background_task import BackgroundTaskParamsKeys as BTParamsKeys
from background.tasks.for_export.transactions_receipts import export_transactions_receipts_task
from background.serializers.instances.worker_reports_transaction import WorkerReportsTransactionsSerializer
from tests.test_app_background.test_export.test_transactions_receipts.constants import MODEL_N_TYPE

_task = export_transactions_receipts_task


@pytest.mark.django_db(databases=["default", "billing"])
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("file_type", [BTFT.zip.value, BTFT.xlsx.value])
@pytest.mark.parametrize(
    "file",
    [pytest.lazy_fixture("transaction_receipt__jpg_file_fi")],
)
def test__contractor_output_files(
    monkeypatch,
    r_cu: CompanyUser,
    get_background_task_fi: Callable,
    get_billing_transaction_for_export_transactions_receipts_test: Callable,
    get_company_fi,
    file,
    file_type: int,
):
    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(content=file.read()))

    __return_data = {"result": {"objstore_id": "234"}}
    __mock_response = MockResponse(status_code=HTTP_202_ACCEPTED, data=__return_data)
    monkeypatch.setattr(requests, "post", lambda *a, **kw: __mock_response)

    _mocked_response = MockResponse(content=json.dumps({"inn": "123456789201", "id": 1, "ext_id": 1}))
    monkeypatch.setattr(requests, "request", lambda *a, **kw: _mocked_response)

    company = r_cu.company
    export_instance = get_billing_transaction_for_export_transactions_receipts_test(company=company)

    params = {
        BTParamsKeys.IDS: [export_instance.id],
        BTParamsKeys.OUTPUT_FILE_TYPE: file_type,
        BTParamsKeys.STRUCTURE: ["projects", "territories", "geo_objects", "reports"],
    }
    instance = get_background_task_fi(company_user=r_cu, params=params, **MODEL_N_TYPE, output_files=[])
    _task.run(background_task_id=instance.id)
    updated_instance = BackgroundTask.objects.get(id=instance.id)
    assert not any([updated_instance.failures, updated_instance.result, updated_instance.input_files])
    assert len(updated_instance.output_files) == 1
    assert updated_instance.status == BackgroundTaskStatus.COMPLETED.value


@pytest.mark.django_db(databases=["default", "billing"])
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("file_type", [BTFT.xlsx.value])
def test__request_microservice__failures(
    monkeypatch,
    r_cu,
    get_background_task_fi,
    get_billing_transaction_for_export_transactions_receipts_test,
    file_type,
):
    __mock_response = MockResponse(status_code=HTTP_400_BAD_REQUEST, text="Текст ошибки")
    monkeypatch.setattr(requests, "post", lambda *a, **kw: __mock_response)
    monkeypatch.setattr(WorkerReportsTransactionsSerializer, "get_inn", lambda *a, **kw: get_random_int())

    company = r_cu.company
    export_instance = get_billing_transaction_for_export_transactions_receipts_test(company=company)

    params = {
        BTParamsKeys.IDS: [export_instance.id],
        BTParamsKeys.OUTPUT_FILE_TYPE: file_type,
        BTParamsKeys.STRUCTURE: ["projects", "territories", "geo_objects", "reports"],
    }
    instance = get_background_task_fi(company_user=r_cu, params=params, **MODEL_N_TYPE, output_files=[])
    _task.run(background_task_id=instance.id)

    updated_instance = BackgroundTask.objects.get(id=instance.id)
    assert not any([updated_instance.input_files, updated_instance.output_files, updated_instance.result])
    print("updated_instance.failures =", updated_instance.failures)
    print("[LOAD_OBJ_ERROR_400] =", [LOAD_OBJ_ERROR_400])
    assert updated_instance.failures == [LOAD_OBJ_ERROR_400]
