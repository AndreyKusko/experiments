import pytest
import requests
from django.utils.crypto import get_random_string

from tests.utils import get_random_int
from background.models import BackgroundTask
from tests.mocked_instances import MockResponse
from ma_saas.constants.system import VALUES, BASENAME
from clients.objects_store.interface import ObjectsStore
from ma_saas.constants.background_task import BackgroundTaskStatus
from clients.notifications.interfaces.sms import SendSMS
from background.tasks.for_import.company_files import import_company_files_task as _task
from tests.test_app_background.test_import.test_company_files.constants import MODEL_N_TYPE

ERROR_TXT = "Error text."


def raise_error():
    raise Exception(ERROR_TXT)


# @pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
# @pytest.mark.parametrize(
#     "file", [ pytest.lazy_fixture("company_files__file_fi")],
# )
# def test__with_project(
#         monkeypatch,
#         r_cu,
#         get_background_task_fi,
#         get_project_fi,
#         file,
# ):
#     filename = file.name.split("/")[-1]
#
#     monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(content=file.read()))
#     monkeypatch.setattr(requests, "post", MockResponse, raising=True)
#     monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)
#     monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: str(get_random_int()))
#
#     project = get_project_fi(company=r_cu.company)
#     params = {"project": project.id}
#     i_f = [{BASENAME: filename, VALUES: [get_random_string()]}]
#     instance = get_background_task_fi(company_user=r_cu, params=params, **MODEL_N_TYPE, input_files=i_f)
#     _task.run(background_task_id=instance.id)
#
#     updated_instance = BackgroundTask.objects.get(id=instance.id)
#     assert updated_instance.failures == [{"failures": [], "filename": filename, "fails_qty": 0}]
#     assert updated_instance.status == BackgroundTaskStatus.COMPLETED.value
#     assert updated_instance.result == [{"filename": filename, "success_qty": 9}]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("file", [pytest.lazy_fixture("company_files__file_fi")])
def test__without_project(monkeypatch, r_cu, get_background_task_fi, file):
    filename = file.name.split("/")[-1]

    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(content=file.read()))
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: str(get_random_int()))

    i_f = [{BASENAME: filename, VALUES: [get_random_string()]}]
    instance = get_background_task_fi(company_user=r_cu, **MODEL_N_TYPE, input_files=i_f)
    _task.run(background_task_id=instance.id)

    updated_instance = BackgroundTask.objects.get(id=instance.id)
    assert updated_instance.failures == [{"failures": [], "filename": filename, "fails_qty": 0}]
    assert updated_instance.status == BackgroundTaskStatus.COMPLETED.value
    assert updated_instance.result == [{"filename": filename, "success_qty": 9}]
