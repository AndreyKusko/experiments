import functools

import pytest
import requests
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, PermissionDenied

from tests.utils import get_random_int, request_response_create
from accounts.models import (
    USER_IS_BLOCKED,
    NOT_TA_R_U__DELETED,
    USER_EMAIL_NOT_VERIFIED,
    NOT_TA_REQUESTING_USER_REASON,
)
from background.models import BackgroundTask
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from tests.mocked_instances import MockResponse
from ma_saas.constants.system import FILES_REQUIRED, ALLOWED_FILES_FORMATS
from ma_saas.constants.company import NOT_ACCEPT_CUS_VALUES
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_MUST_BE_ACCEPT
from clients.objects_store.interface import ObjectsStore
from ma_saas.constants.background_task import BackgroundTaskStatus
from background.serializers.validators.main import USE_COMMON_ALLOWED_FILE_FORMATS
from background.tasks.for_import.company_workers import import_company_workers_task
from tests.test_app_background.test_import.test_company_workers.constants import PATH, TASK_TYPE, MODEL_NAME

User = get_user_model()

__get_response = functools.partial(request_response_create, path=PATH)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(
    api_client,
    mock_policies_false,
    monkeypatch,
    r_cu,
    new_background_task_data,
    workers__phone__xlsx_file_fi,
):
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(import_company_workers_task, "delay", lambda *a, **k: None)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: get_random_int())
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)

    data = new_background_task_data(
        company=r_cu.company,
    )
    data["files"] = [workers__phone__xlsx_file_fi]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instance = BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE)
    assert len(created_instance) == 1
    assert response.data["id"] == created_instance.first().id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS_VALUES)
def test__not_accepted_owner__success(
    api_client,
    monkeypatch,
    get_cu_owner_fi,
    new_background_task_data,
    workers__phone__xlsx_file_fi,
    status,
):
    r_cu = get_cu_owner_fi(status=status)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    data = new_background_task_data(
        company=r_cu.company,
    )
    data["files"] = [workers__phone__xlsx_file_fi]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager__with_policy__success(
    api_client,
    monkeypatch,
    r_cu,
    new_background_task_data,
    workers__phone__xlsx_file_fi,
):
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(import_company_workers_task, "delay", lambda *a, **k: None)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: get_random_int())
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    data = new_background_task_data(
        company=r_cu.company,
    )
    data["files"] = [workers__phone__xlsx_file_fi]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instance = BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE)
    assert len(created_instance) == 1
    assert response.data["id"] == created_instance.first().id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager__without_policy__fail(
    api_client,
    mock_policies_false,
    monkeypatch,
    r_cu,
    new_background_task_data,
    workers__phone__xlsx_file_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)

    data = new_background_task_data(
        company=r_cu.company,
    )
    data["files"] = [workers__phone__xlsx_file_fi]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PermissionDenied.default_detail}
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS_VALUES)
def test__not_accepted_manager__with_policy__fail(
    api_client,
    monkeypatch,
    get_cu_manager_fi,
    new_background_task_data,
    workers__phone__xlsx_file_fi,
    status,
):
    r_cu = get_cu_manager_fi(status=status)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    data = new_background_task_data(
        company=r_cu.company,
    )
    data["files"] = [workers__phone__xlsx_file_fi]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture("workers__phones__docx_file_fi"),
        pytest.lazy_fixture("workers__phone__txt_file_fi"),
    ],
)
def test__invalid_file_format__fail(
    api_client,
    monkeypatch,
    r_cu,
    new_background_task_data,
    file,
):
    filename = file.name.split("/")[-1]

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    company = r_cu.company
    data = new_background_task_data(company=company)
    data["files"] = [file]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == {"non_field_errors": [USE_COMMON_ALLOWED_FILE_FORMATS.format(filename=filename)]}
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__without_file__fail(api_client, monkeypatch, r_cu, new_background_task_data):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    data = new_background_task_data(company=r_cu.company)

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data["non_field_errors"][0] == FILES_REQUIRED
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__another_company_cu__not_saving(
    api_client,
    monkeypatch,
    r_cu,
    get_cu_fi,
    new_background_task_data,
    workers__phone__xlsx_file_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    a_cu = get_cu_fi()

    data = new_background_task_data(company=a_cu.company, company_user=a_cu)
    data["files"] = [workers__phone__xlsx_file_fi]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("user_attr", "value", "err_msg"),
    (
        ("is_deleted", True, NOT_TA_R_U__DELETED),
        (
            "is_blocked",
            True,
            NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_BLOCKED),
        ),
        ("is_verified_email", False, NOT_TA_REQUESTING_USER_REASON.format(reason=USER_EMAIL_NOT_VERIFIED)),
    ),
)
def test__not_active_user__fail(
    api_client,
    monkeypatch,
    r_cu,
    new_background_task_data,
    user_attr: str,
    value: bool,
    err_msg: str,
    workers__phone__xlsx_file_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    setattr(r_cu.user, user_attr, value)
    r_cu.user.save()
    data = new_background_task_data(
        company=r_cu.company,
    )
    data["files"] = [workers__phone__xlsx_file_fi]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": err_msg}
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture("workers__phone__xls_file_fi"),
        pytest.lazy_fixture("workers__phone__xlsx_file_fi"),
        pytest.lazy_fixture("workers__phone__first_name__last_name__xlsx_file_fi"),
        pytest.lazy_fixture("workers__phone__csv_file_fi"),
        pytest.lazy_fixture("workers__phone__first_name__last_name__csv_file_fi"),
    ],
)
def test__response_data(api_client, monkeypatch, r_cu, new_background_task_data, file):
    """Тестировать с разными типами файлов."""
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(import_company_workers_task, "delay", lambda *a, **k: None)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: get_random_int())
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    data = new_background_task_data(company=r_cu.company)
    data["files"] = [file]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user)

    response_instance = response.data
    created_instances = BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE)
    assert len(created_instances) == 1
    assert response_instance.pop("id") == created_instances.first().id
    assert response_instance.pop("company_user") == r_cu.id
    assert response_instance.pop("company") == r_cu.company.id
    assert response_instance.pop("model_name") == MODEL_NAME
    assert response_instance.pop("task_type") == TASK_TYPE
    assert response_instance.pop("status") == BackgroundTaskStatus.PENDING.value
    assert response_instance.pop("params") == {}
    assert response_instance.pop("created_at")
    assert response_instance.pop("updated_at")
    input_files = response_instance.pop("input_files")
    assert input_files
    assert len(input_files) == 1 and len(input_files[0]) == 2
    assert "import_workers" in input_files[0]["basename"] and input_files[0]["values"]

    assert not response_instance.pop("result")
    assert not response_instance.pop("output_files")
    assert not response_instance.pop("failures")

    assert not response_instance
