import pytest
import requests
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from tests.utils import get_random_int
from background.models import BackgroundTask
from tests.mocked_instances import MockResponse
from ma_saas.utils.read_file import ReadFile
from ma_saas.constants.system import VALUES, BASENAME
from companies.models.company_user import CompanyUser
from clients.objects_store.interface import ObjectsStore
from ma_saas.constants.background_task import BackgroundTaskStatus
from clients.notifications.interfaces.sms import SendSMS
from background.tasks.for_import.company_workers import import_company_workers_task as _task
from projects.models.contractor_project_territory_worker import ContractorProjectTerritoryWorker
from tests.test_app_background.test_import.test_company_workers.constants import MODEL_N_TYPE

ERROR_TXT = "Error text."

User = get_user_model()

FILE_PHONES = ["79091110001", "79091110002"]


def raise_error():
    raise Exception(ERROR_TXT)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture("workers__phone__csv_file_fi"),
        pytest.lazy_fixture("workers__phone__xlsx_file_fi"),
        pytest.lazy_fixture("workers__phone__xls_file_fi"),
    ],
)
def test__file_with_phones_only_instance_data(
    monkeypatch, r_cu, get_background_task_fi, get_project_territory_fi, file
):
    filename = file.name.split("/")[-1]

    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(content=file.read()))
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: str(get_random_int()))

    delete_users = User.objects.filter(phone__in=FILE_PHONES)
    CompanyUser.objects.filter(user__in=delete_users).delete()
    delete_users.delete()
    assert not User.objects.filter(phone__in=FILE_PHONES).exists()

    i_f = [{BASENAME: filename, VALUES: [get_random_string()]}]
    instance = get_background_task_fi(company_user=r_cu, **MODEL_N_TYPE, input_files=i_f)
    _task.run(background_task_id=instance.id)

    updated_instance = BackgroundTask.objects.get(id=instance.id)
    assert updated_instance.failures == [{"failures": [], "filename": filename, "fails_qty": 0}]
    assert updated_instance.status == BackgroundTaskStatus.COMPLETED.value
    assert updated_instance.result == [{"filename": filename, "success_qty": 2}]
    assert User.objects.filter(phone__in=FILE_PHONES).count() == 2


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture("workers__phone__first_name__last_name__csv_file_fi"),
        pytest.lazy_fixture("workers__phone__first_name__last_name__xlsx_file_fi"),
    ],
)
def test__file_with_phones__first_name__last__name__instance_data(
    monkeypatch,
    r_cu,
    get_background_task_fi,
    get_project_territory_fi,
    file,
):
    filename = file.name.split("/")[-1]

    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(content=file.read()))
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: str(get_random_int()))

    delete_users = User.objects.filter(phone__in=FILE_PHONES)
    CompanyUser.objects.filter(user__in=delete_users).delete()
    delete_users.delete()
    assert not User.objects.filter(phone__in=FILE_PHONES).exists()

    i_f = [{BASENAME: filename, VALUES: [get_random_string()]}]
    instance = get_background_task_fi(company_user=r_cu, **MODEL_N_TYPE, input_files=i_f)
    _task.run(background_task_id=instance.id)

    updated_instance = BackgroundTask.objects.get(id=instance.id)
    assert updated_instance.failures == [{"failures": [], "filename": filename, "fails_qty": 0}]
    assert updated_instance.status == BackgroundTaskStatus.COMPLETED.value
    assert updated_instance.result == [{"filename": filename, "success_qty": 2}]
    assert User.objects.filter(phone__in=FILE_PHONES).count() == 2


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture("workers__phone__csv_file_fi"),
        pytest.lazy_fixture("workers__phone__xlsx_file_fi"),
        pytest.lazy_fixture("workers__phone__xls_file_fi"),
    ],
)
def test__raised_error_written_data(
    monkeypatch, r_cu, get_background_task_fi, get_project_territory_fi, file
):
    filename = file.name.split("/")[-1]

    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(content=file.read()))
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)
    monkeypatch.setattr(ReadFile, "__init__", lambda *args, **kwargs: raise_error())

    delete_users = User.objects.filter(phone__in=FILE_PHONES)
    CompanyUser.objects.filter(user__in=delete_users).delete()
    delete_users.delete()
    assert not User.objects.filter(phone__in=FILE_PHONES).exists()

    i_f = [{BASENAME: filename, VALUES: [get_random_string()]}]
    instance = get_background_task_fi(company_user=r_cu, **MODEL_N_TYPE, input_files=i_f)
    _task.run(background_task_id=instance.id)

    updated_instance = BackgroundTask.objects.get(id=instance.id)
    assert updated_instance.result == [{"filename": filename, "success_qty": 0}]
    assert updated_instance.failures == [{"filename": filename, "fails_qty": 1, "failures": ["Error text."]}]
    assert updated_instance.status == BackgroundTaskStatus.FAILED.value
    assert User.objects.filter(phone__in=FILE_PHONES).count() == 0
