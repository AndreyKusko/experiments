import json
import functools

import pytest
import requests
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, PermissionDenied

from tests.utils import request_response_create
from background.models import BackgroundTask
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from tests.mocked_instances import MockResponse
from ma_saas.constants.company import NOT_ACCEPT_CUS
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_MUST_BE_ACCEPT, COMPANY_OWNER_ONLY_ALLOWED
from ma_saas.constants.background_task import BackgroundTaskFileTypes as BTFT
from ma_saas.constants.background_task import BackgroundTaskParamsKeys as BTParamsKeys
from background.serializers.background_task import OUTPUT_TYPE_MUST_BE_INT
from background.serializers.validators.main import (
    EXTRA_KEYS_FAILS,
    MISSED_KEYS_FAILS,
    OUTPUT_FILE_TYPE_NOT_ALLOWED,
)
from background.tasks.for_export.transactions_receipts import export_transactions_receipts_task
from background.serializers.for_export.transactions_receipts import (
    ANOTHER_TRANSACTION_COMPANY_NOT_ALLOWED,
    ExportTransactionsReceiptsSerializer,
)
from tests.test_app_background.test_export.test_transactions_receipts.constants import (
    PATH,
    TASK_TYPE,
    MODEL_NAME,
)

User = get_user_model()

__get_response = functools.partial(request_response_create, path=PATH)


@pytest.mark.django_db(databases=["default", "billing"])
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(
    api_client,
    mock_policies_false,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_billing_transaction_for_export_transactions_receipts_test,
):
    monkeypatch.setattr(export_transactions_receipts_task, "delay", lambda *a, **k: None)
    __mocked_response = MockResponse(content=json.dumps({"inn": "123456789201", "id": 1, "ext_id": 1}))
    monkeypatch.setattr(requests, "request", lambda *a, **kw: __mocked_response)

    export_instance = get_billing_transaction_for_export_transactions_receipts_test(company=r_cu.company)
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()

    params = {
        BTParamsKeys.IDS: [export_instance.id],
        BTParamsKeys.OUTPUT_FILE_TYPE: BTFT.xlsx.value,
        BTParamsKeys.STRUCTURE: ["projects", "territories", "geo_objects", "reports"],
    }
    data = new_background_task_data(company_user=r_cu, params=params)
    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instance = BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE)
    assert len(created_instance) == 1
    assert response.data["id"] == created_instance.first().id


@pytest.mark.django_db(databases=["default", "billing"])
@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__success(
    api_client,
    monkeypatch,
    get_cu_owner_fi,
    new_background_task_data,
    get_billing_transaction_for_export_transactions_receipts_test,
    status,
):
    monkeypatch.setattr(export_transactions_receipts_task, "delay", lambda *a, **k: None)
    __mocked_response = MockResponse(content=json.dumps({"inn": "123456789201", "id": 1, "ext_id": 1}))
    monkeypatch.setattr(requests, "request", lambda *a, **kw: __mocked_response)
    r_cu = get_cu_owner_fi(status=status)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **k: True)

    export_instance = get_billing_transaction_for_export_transactions_receipts_test(company=r_cu.company)
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()

    params = {
        BTParamsKeys.IDS: [export_instance.id],
        BTParamsKeys.OUTPUT_FILE_TYPE: BTFT.xlsx.value,
        BTParamsKeys.STRUCTURE: ["projects", "territories", "geo_objects", "reports"],
    }
    data = new_background_task_data(company=r_cu.company, params=params)

    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.django_db(databases=["default", "billing"])
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
# def test__accepted_manager__with_policy__success(
def test__accepted_manager__with_policy__fail(
    api_client,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_billing_transaction_for_export_transactions_receipts_test,
):
    monkeypatch.setattr(export_transactions_receipts_task, "delay", lambda *a, **k: None)
    __mocked_response = MockResponse(content=json.dumps({"inn": "123456789201", "id": 1, "ext_id": 1}))
    monkeypatch.setattr(requests, "request", lambda *a, **kw: __mocked_response)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **k: True)

    export_instance = get_billing_transaction_for_export_transactions_receipts_test(company=r_cu.company)
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()

    params = {
        BTParamsKeys.IDS: [export_instance.id],
        BTParamsKeys.OUTPUT_FILE_TYPE: BTFT.xlsx.value,
        BTParamsKeys.STRUCTURE: ["projects", "territories", "geo_objects", "reports"],
    }
    data = new_background_task_data(company=r_cu.company, params=params)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": COMPANY_OWNER_ONLY_ALLOWED}
    # response = __get_response(api_client, data=data, user=r_cu.user)
    # created_instance = BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE)
    # assert len(created_instance) == 1
    # assert response.data['id'] == created_instance.first().id


@pytest.mark.django_db(databases=["default", "billing"])
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager__without_policy__fail(
    api_client,
    mock_policies_false,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_billing_transaction_for_export_transactions_receipts_test,
):
    monkeypatch.setattr(export_transactions_receipts_task, "delay", lambda *a, **k: None)
    __mocked_response = MockResponse(content=json.dumps({"inn": "123456789201", "id": 1, "ext_id": 1}))
    monkeypatch.setattr(requests, "request", lambda *a, **kw: __mocked_response)

    export_instance = get_billing_transaction_for_export_transactions_receipts_test(company=r_cu.company)
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()

    params = {
        BTParamsKeys.IDS: [export_instance.id],
        BTParamsKeys.OUTPUT_FILE_TYPE: BTFT.xlsx.value,
        BTParamsKeys.STRUCTURE: ["projects", "territories", "geo_objects", "reports"],
    }
    data = new_background_task_data(company=r_cu.company, params=params)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": COMPANY_OWNER_ONLY_ALLOWED}


@pytest.mark.django_db(databases=["default", "billing"])
@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_manager__with_policy__fail(
    api_client,
    monkeypatch,
    get_cu_manager_fi,
    new_background_task_data,
    get_billing_transaction_for_export_transactions_receipts_test,
    status,
):
    monkeypatch.setattr(export_transactions_receipts_task, "delay", lambda *a, **k: None)
    __return_content = json.dumps({"inn": "123456789201", "id": 1, "ext_id": 1})
    __mocked_response = MockResponse(content=__return_content)
    monkeypatch.setattr(requests, "request", lambda *a, **kw: __mocked_response)
    r_cu = get_cu_manager_fi(status=status)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **k: True)

    export_instance = get_billing_transaction_for_export_transactions_receipts_test(company=r_cu.company)
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()

    params = {
        BTParamsKeys.IDS: [export_instance.id],
        BTParamsKeys.OUTPUT_FILE_TYPE: BTFT.xlsx.value,
        BTParamsKeys.STRUCTURE: ["projects", "territories", "geo_objects", "reports"],
    }
    data = new_background_task_data(company=r_cu.company, params=params)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.django_db(databases=["default", "billing"])
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__another_company_user__fail(
    api_client,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_billing_transaction_for_export_transactions_receipts_test,
    get_company_fi,
):
    monkeypatch.setattr(export_transactions_receipts_task, "delay", lambda *a, **k: None)

    company = get_company_fi()
    export_instance = get_billing_transaction_for_export_transactions_receipts_test(company=r_cu.company)
    assert not BackgroundTask.objects.filter(company=company, task_type=TASK_TYPE).exists()

    params = {
        BTParamsKeys.IDS: [export_instance.id],
        BTParamsKeys.OUTPUT_FILE_TYPE: BTFT.xlsx.value,
        BTParamsKeys.STRUCTURE: ["projects", "territories", "geo_objects", "reports"],
    }
    data = new_background_task_data(company=company, params=params)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}


@pytest.mark.django_db(databases=["default", "billing"])
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__another_company_transaction__fail(
    api_client,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_billing_transaction_for_export_transactions_receipts_test,
    get_company_fi,
):
    monkeypatch.setattr(export_transactions_receipts_task, "delay", lambda *a, **k: None)

    company = get_company_fi()
    export_instance = get_billing_transaction_for_export_transactions_receipts_test(company=company)
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()

    params = {
        BTParamsKeys.IDS: [export_instance.id],
        BTParamsKeys.OUTPUT_FILE_TYPE: BTFT.xlsx.value,
        BTParamsKeys.STRUCTURE: ["projects", "territories", "geo_objects", "reports"],
    }
    data = new_background_task_data(company=r_cu.company, params=params)

    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == {
        "non_field_errors": [ANOTHER_TRANSACTION_COMPANY_NOT_ALLOWED.format(ids=export_instance.id)]
    }


@pytest.mark.django_db(databases=["default", "billing"])
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__extra_keys__fails(
    api_client,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_billing_transaction_for_export_transactions_receipts_test,
):
    monkeypatch.setattr(export_transactions_receipts_task, "delay", lambda *a, **k: None)

    company = r_cu.company
    export_instance = get_billing_transaction_for_export_transactions_receipts_test(company=company)
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()

    extra_key = "qwe"
    params = {
        BTParamsKeys.IDS: [export_instance.id],
        BTParamsKeys.OUTPUT_FILE_TYPE: BTFT.xlsx.value,
        BTParamsKeys.STRUCTURE: ["projects", "territories", "geo_objects", "reports"],
        extra_key: "qwe",
    }
    data = new_background_task_data(company=company, params=params)

    response = __get_response(api_client, data, r_cu.user, status_codes=ValidationError)
    assert response.data == {"params": [EXTRA_KEYS_FAILS.format(extra_keys=extra_key)]}


@pytest.mark.django_db(databases=["default", "billing"])
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "missed_key", [BTParamsKeys.IDS, BTParamsKeys.OUTPUT_FILE_TYPE, BTParamsKeys.STRUCTURE]
)
def test__missed_params_keys__fails(
    api_client,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_billing_transaction_for_export_transactions_receipts_test,
    missed_key: str,
):
    monkeypatch.setattr(export_transactions_receipts_task, "delay", lambda *a, **k: None)

    company = r_cu.company
    export_instance = get_billing_transaction_for_export_transactions_receipts_test(company=company)
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()

    params = {
        BTParamsKeys.IDS: [export_instance.id],
        BTParamsKeys.OUTPUT_FILE_TYPE: BTFT.xlsx.value,
        BTParamsKeys.STRUCTURE: ["projects", "territories", "geo_objects", "reports"],
    }
    params.pop(missed_key)
    data = new_background_task_data(company=company, params=params)

    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == {"params": [MISSED_KEYS_FAILS.format(missed_keys=missed_key)]}


@pytest.mark.django_db(databases=["default", "billing"])
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("output_file_type", "err_text"),
    [
        ("qwe", OUTPUT_TYPE_MUST_BE_INT),
        (
            BTFT.csv.value,
            OUTPUT_FILE_TYPE_NOT_ALLOWED.format(
                file_types=", ".join([str(v) for v in ExportTransactionsReceiptsSerializer._file_types]),
                requested_value=BTFT.csv.value,
            ),
        ),
    ],
)
def test__invalid_file_type__fails(
    api_client,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_billing_transaction_for_export_transactions_receipts_test,
    output_file_type,
    err_text: str,
):
    monkeypatch.setattr(export_transactions_receipts_task, "delay", lambda *a, **k: None)
    company = r_cu.company
    export_instance = get_billing_transaction_for_export_transactions_receipts_test(company=company)
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()

    params = {
        BTParamsKeys.IDS: [export_instance.id],
        BTParamsKeys.OUTPUT_FILE_TYPE: output_file_type,
        BTParamsKeys.STRUCTURE: ["projects", "territories", "geo_objects", "reports"],
    }
    data = new_background_task_data(company=company, params=params)

    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == {"params": [err_text]}


@pytest.mark.django_db(databases=["default", "billing"])
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__invalid_structure_data__fails(
    api_client,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_billing_transaction_for_export_transactions_receipts_test,
):
    monkeypatch.setattr(export_transactions_receipts_task, "delay", lambda *a, **k: None)

    company = r_cu.company
    export_instance = get_billing_transaction_for_export_transactions_receipts_test(company=company)
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()

    params = {
        BTParamsKeys.IDS: [export_instance.id],
        BTParamsKeys.OUTPUT_FILE_TYPE: BTFT.csv.value,
        BTParamsKeys.STRUCTURE: ["projects", "territories", "geo_objects", "qwe"],
    }
    data = new_background_task_data(company=company, params=params)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data


@pytest.mark.django_db(databases=["default", "billing"])
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("file_type", [BTFT.xlsx.value, BTFT.zip.value])
def test__response_data(
    api_client,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_billing_transaction_for_export_transactions_receipts_test,
    file_type: int,
):
    monkeypatch.setattr(export_transactions_receipts_task, "delay", lambda *a, **k: None)
    _mocked_response = MockResponse(content=json.dumps({"inn": "123456789201", "id": 1, "ext_id": 1}))
    monkeypatch.setattr(requests, "request", lambda *a, **kw: _mocked_response)

    company = r_cu.company
    export_instance = get_billing_transaction_for_export_transactions_receipts_test(company=company)
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()

    params = {
        BTParamsKeys.IDS: [export_instance.id],
        BTParamsKeys.OUTPUT_FILE_TYPE: file_type,
        BTParamsKeys.STRUCTURE: ["projects", "territories", "geo_objects", "reports"],
    }
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
