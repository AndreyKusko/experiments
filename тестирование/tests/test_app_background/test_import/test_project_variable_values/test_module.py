import pytest
import requests
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from tests.utils import get_random_int
from background.models import BackgroundTask
from tests.mocked_instances import MockResponse
from ma_saas.constants.system import VALUES, BASENAME
from clients.objects_store.interface import ObjectsStore
from projects.models.project_variable import ProjectVariable
from ma_saas.constants.background_task import BackgroundTaskStatus
from background.tasks.for_import.project_variable_values import (
    RetrieveLineValues,
    CreateProjectVariableValuesFromFile,
)
from background.tasks.for_import.project_variable_values import import_project_variable_values_task as _task
from tests.test_app_background.test_import.test_project_variable_values.constants import MODEL_N_TYPE

ERROR_TXT = "Error text."

User = get_user_model()


def raise_error():
    raise Exception(ERROR_TXT)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture("project_variable_values__xls_file_fi"),
        pytest.lazy_fixture("project_variable_values__xlsx_file_fi"),
    ],
)
def test__all_fields_filled_data(monkeypatch, r_cu, get_background_task_fi, get_project_fi, file):
    filename = file.name.split("/")[-1]

    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(content=file.read()))
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: str(get_random_int()))
    # monkeypatch.setattr(
    #     CreateProjectVariableValuesFromFile, "check_variable_model_relation_valid", lambda *a, **kw: True
    # )
    # monkeypatch.setattr(
    #     CreateProjectVariableValuesFromFile, "get_company_file_value", lambda *a, **kw: get_random_string()
    # )

    @staticmethod
    def create_i(key, project, variable_kind):
        instance, _ = ProjectVariable.objects.get_or_create(key=key, project=project, kind=variable_kind)
        return instance

    monkeypatch.setattr(CreateProjectVariableValuesFromFile, "get_project_variable", create_i)
    monkeypatch.setattr(RetrieveLineValues, "get_company_file_value", lambda *a, **kw: get_random_string())
    monkeypatch.setattr(RetrieveLineValues, "check_variable_model_relation_valid", lambda *a, **kw: True)

    project = get_project_fi(company=r_cu.company)
    params = {"project": project.id}
    i_f = [{BASENAME: filename, VALUES: [get_random_string()]}]
    instance = get_background_task_fi(company_user=r_cu, params=params, **MODEL_N_TYPE, input_files=i_f)
    _task.run(background_task_id=instance.id)

    updated_instance = BackgroundTask.objects.get(id=instance.id)
    print("updated_instance.failures =", updated_instance.failures)
    assert updated_instance.failures == [{"failures": [], "filename": filename, "fails_qty": 0}]
    assert updated_instance.result == [{"filename": filename, "success_qty": 6}]
    assert updated_instance.status == BackgroundTaskStatus.COMPLETED.value


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture("project_variable_values__xls_file_fi"),
        pytest.lazy_fixture("project_variable_values__xlsx_file_fi"),
    ],
)
def test__relation_to_another_company_instance__fail(
    monkeypatch, r_cu, get_background_task_fi, get_project_fi, file
):
    """Тестируются и допустивые target_name и variable_kind"""
    filename = file.name.split("/")[-1]

    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(content=file.read()))
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: str(get_random_int()))
    monkeypatch.setattr(
        RetrieveLineValues, "check_variable_model_relation_valid", lambda *a, **kw: raise_error()
    )

    project = get_project_fi(company=r_cu.company)
    params = {"project": project.id}
    i_f = [{BASENAME: filename, VALUES: [get_random_string()]}]
    instance = get_background_task_fi(company_user=r_cu, params=params, **MODEL_N_TYPE, input_files=i_f)
    _task.run(background_task_id=instance.id)

    updated_instance = BackgroundTask.objects.get(id=instance.id)
    assert updated_instance.result == [{"filename": filename, "success_qty": 0}]
    assert updated_instance.failures == [{"failures": [], "filename": filename, "fails_qty": 6}]
    assert updated_instance.status == BackgroundTaskStatus.FAILED.value
