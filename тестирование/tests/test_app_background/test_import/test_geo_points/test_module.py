import pytest
import requests
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework.status import HTTP_202_ACCEPTED

from background.models import BackgroundTask
from geo_objects.models import GeoPoint
from tests.mocked_instances import MockResponse
from ma_saas.constants.system import VALUES, BASENAME
from ma_saas.constants.background_task import BackgroundTaskStatus
from background.tasks.for_import.geo_points import import_geo_points_task as _task
from tests.test_app_background.test_import.test_geo_points.constants import MODEL_N_TYPE

ERROR_TXT = "Error text."

User = get_user_model()


def raise_error():
    raise Exception(ERROR_TXT)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("file", [pytest.lazy_fixture("geo_points__xlsx_file_fi")])
def test__all_fields_filled_data(
    monkeypatch, r_cu, get_background_task_fi, get_project_fi, get_territory_fi, file
):
    filename = file.name.split("/")[-1]

    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(content=file.read()))
    data = {"result": {"objstore_id": get_random_string()}}
    post_mock = MockResponse(status_code=HTTP_202_ACCEPTED, data=data)
    monkeypatch.setattr(requests, "post", lambda *a, **kw: post_mock, raising=True)

    delete_gp = GeoPoint.objects.filter(lat__in=(45.2376, 45.2386)).filter(lon__in=(37.2236, 37.2246))
    delete_gp.delete()

    get_territory_fi(company=r_cu.company, title="Москва")
    get_territory_fi(company=r_cu.company, title="Голестан")
    project = get_project_fi(company=r_cu.company)
    params = {"project": project.id}
    i_f = [{BASENAME: filename, VALUES: [get_random_string()]}]
    instance = get_background_task_fi(company_user=r_cu, params=params, **MODEL_N_TYPE, input_files=i_f)
    _task.run(background_task_id=instance.id)

    updated_instance = BackgroundTask.objects.get(id=instance.id)
    assert updated_instance.result == [{"filename": filename, "success_qty": 0}]
    assert updated_instance.failures == [{"failures": [], "filename": filename, "fails_qty": 2}]
    assert updated_instance.status == BackgroundTaskStatus.FAILED.value


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("file", [pytest.lazy_fixture("geo_points_lost_req_field__xlsx_file_fi")])
def test__lost_required_field_instance_data(
    monkeypatch, r_cu, get_background_task_fi, get_project_fi, get_territory_fi, file
):
    filename = file.name.split("/")[-1]

    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(content=file.read()))
    data = {"result": {"objstore_id": get_random_string()}}
    post_mock = MockResponse(status_code=HTTP_202_ACCEPTED, data=data)
    monkeypatch.setattr(requests, "post", lambda *a, **kw: post_mock, raising=True)

    get_territory_fi(company=r_cu.company, title="Москва")
    get_territory_fi(company=r_cu.company, title="Голестан")
    project = get_project_fi(company=r_cu.company)
    i_f = [{BASENAME: filename, VALUES: [get_random_string()]}]
    params = {"project": project.id}
    instance = get_background_task_fi(company_user=r_cu, params=params, input_files=i_f, **MODEL_N_TYPE)
    _task.run(background_task_id=instance.id)

    updated_instance = BackgroundTask.objects.get(id=instance.id)
    assert updated_instance.result == [{"filename": filename, "success_qty": 0}]
    assert updated_instance.failures == [{"failures": [], "filename": filename, "fails_qty": 3}]
    assert updated_instance.status == BackgroundTaskStatus.FAILED.value
