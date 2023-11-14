import functools

import pytest
import requests
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied

from tests.utils import get_random_int, request_response_create
from accounts.models import ValidationError
from background.models import BackgroundTask
from background.constants import ImportProjectVariableValuesHeaders
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from tests.mocked_instances import MockResponse
from ma_saas.constants.system import VALUES, BASENAME, FILES_REQUIRED, Callable
from ma_saas.constants.company import NOT_ACCEPT_CUS_VALUES
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_MUST_BE_ACCEPT
from clients.objects_store.interface import ObjectsStore
from ma_saas.constants.background_task import BackgroundTaskType, BackgroundTaskStatus
from background.serializers.validators.main import MISSED_REQUIRED_FILE_HEADERS
from projects.models.project_variable_value import ProjectVariableValue
from background.tasks.for_import.project_variable_values import import_project_variable_values_task
from tests.test_app_background.test_import.test_project_variable_values.constants import (
    PATH,
    TASK_TYPE,
    MODEL_NAME,
)

User = get_user_model()

__get_response = functools.partial(request_response_create, path=PATH)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(
    api_client,
    mock_policies_false,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_project_fi,
    project_variable_values__xlsx_file_fi,
):
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(import_project_variable_values_task, "delay", lambda *a, **k: None)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: get_random_int())
    company = r_cu.company
    project = get_project_fi(company=company)
    data = new_background_task_data(company=company, params={"project": project.id})

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    data["files"] = [project_variable_values__xlsx_file_fi]
    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instance = BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE)
    assert len(created_instance) == 1
    assert response.data["id"] == created_instance.first().id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS_VALUES)
def test__not_accepted_owner__fail(
    api_client,
    monkeypatch,
    get_cu_owner_fi,
    new_background_task_data: Callable,
    get_project_fi,
    status,
    project_variable_values__xlsx_file_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu = get_cu_owner_fi(status=status)
    project = get_project_fi(company=r_cu.company)
    data = new_background_task_data(company=r_cu.company, company_user=r_cu, params={"project": project.id})
    data["files"] = [project_variable_values__xlsx_file_fi]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager__with_policy__success(
    api_client,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_project_fi,
    project_variable_values__xlsx_file_fi,
):
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(import_project_variable_values_task, "delay", lambda *a, **k: None)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: get_random_int())
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    company = r_cu.company
    project = get_project_fi(company=company)
    data = new_background_task_data(company=company, params={"project": project.id})
    data["files"] = [project_variable_values__xlsx_file_fi]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instance = BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE)
    assert len(created_instance) == 1
    assert response.data["id"] == created_instance.first().id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS_VALUES)
def test__not_accepted_manager__with_policy__fail(
    api_client,
    monkeypatch,
    get_cu_manager_fi,
    new_background_task_data,
    get_project_fi,
    project_variable_values__xlsx_file_fi,
    status,
):
    r_cu = get_cu_manager_fi(status=status)
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(import_project_variable_values_task, "delay", lambda *a, **k: None)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: get_random_int())
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    company = r_cu.company
    project = get_project_fi(company=company)
    data = new_background_task_data(company=company, params={"project": project.id})

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    data["files"] = [project_variable_values__xlsx_file_fi]
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager__without_policy__success(
    api_client,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_project_fi,
    project_variable_values__xlsx_file_fi,
):
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(import_project_variable_values_task, "delay", lambda *a, **k: None)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: get_random_int())
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)

    company = r_cu.company
    project = get_project_fi(company=company)
    data = new_background_task_data(company=company, params={"project": project.id})

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    data["files"] = [project_variable_values__xlsx_file_fi]
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PermissionDenied.default_detail}
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture("project_variable_values__missed_required_header__xlsx_file_fi"),
    ],
)
def test__missed_required_header(
    api_client, monkeypatch, r_cu, new_background_task_data: Callable, get_project_fi, file
):
    filename = file.name.split("/")[-1]

    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(import_project_variable_values_task, "delay", lambda *a, **k: None)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    project = get_project_fi(company=r_cu.company)
    data = new_background_task_data(company=r_cu.company, params={"project": project.id})
    data["files"] = [file]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == {
        "non_field_errors": [
            MISSED_REQUIRED_FILE_HEADERS.format(
                filename=filename,
                missed_required_headers=", ".join([ImportProjectVariableValuesHeaders.VALUE]),
            )
        ]
    }
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__without_file__fail(api_client, monkeypatch, r_cu, new_background_task_data, get_project_fi):
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(import_project_variable_values_task, "delay", lambda *a, **k: None)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    project = get_project_fi(company=r_cu.company)
    data = new_background_task_data(company=r_cu.company, params={"project": project.id})

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == {"non_field_errors": [FILES_REQUIRED]}
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__another_company__cu__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_cu_fi,
    new_background_task_data,
    get_project_fi,
    project_variable_values__xlsx_file_fi,
):
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(import_project_variable_values_task, "delay", lambda *a, **k: None)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: get_random_int())
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    a_cu = get_cu_fi()
    project = get_project_fi(company=r_cu.company)
    data = new_background_task_data(company=a_cu.company, company_user=a_cu, params={"project": project.id})
    data["files"] = [project_variable_values__xlsx_file_fi]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("file", "file_name"),
    [
        (pytest.lazy_fixture("project_variable_values__xlsx_file_fi"), "import_project_variable_values.xlsx"),
        (pytest.lazy_fixture("project_variable_values__xls_file_fi"), "import_project_variable_values.xls"),
    ],
)
def test__response_data(
    api_client,
    monkeypatch,
    r_cu,
    new_background_task_data: Callable,
    get_project_fi,
    file,
    file_name,
):
    """Тестировать с разными типами файлов."""
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(import_project_variable_values_task, "delay", lambda *a, **k: None)
    file_id = get_random_int()
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: file_id)

    project = get_project_fi(company=r_cu.company)
    data = new_background_task_data(company=r_cu.company, params={"project": project.id})
    data["files"] = [file]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user)
    response_instance = response.data
    response_instance_id = response_instance.pop("id")
    assert response_instance_id
    created_instance = BackgroundTask.objects.get(id=response_instance_id)
    assert response_instance.pop("company") == created_instance.company_id == r_cu.company.id
    assert response_instance.pop("company_user") == created_instance.company_user_id == r_cu.id
    assert created_instance.model_name == response_instance.pop("model_name") == MODEL_NAME
    assert created_instance.task_type == response_instance.pop("task_type") == TASK_TYPE
    assert response_instance.pop("params") == created_instance.params == {"project": project.id}
    assert response_instance.pop("failures") == created_instance.failures == []
    assert response_instance.pop("status") == created_instance.status == BackgroundTaskStatus.PENDING.value
    assert created_instance.input_files == response_instance.pop("input_files")
    assert created_instance.input_files == [{BASENAME: file_name, VALUES: [file_id]}]
    assert response_instance.pop("result") == created_instance.result == []
    assert response_instance.pop("output_files") == created_instance.output_files == []
    assert response_instance.pop("created_at")
    assert response_instance.pop("updated_at")

    assert not response_instance
