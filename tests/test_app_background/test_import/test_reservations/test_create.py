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
from tests.mocked_instances import MockResponse
from ma_saas.constants.system import ALLOWED_FILES_FORMATS
from ma_saas.constants.company import NOT_ACCEPT_CUS, NOT_ACCEPT_CUS_VALUES
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_MUST_BE_ACCEPT
from clients.objects_store.interface import ObjectsStore
from ma_saas.constants.background_task import BackgroundTaskStatus
from background.serializers.validators.main import FILE_FORMAT_ERR, USE_COMMON_ALLOWED_FILE_FORMATS
from background.tasks.for_import.reservations import import_reservations_task
from tests.test_app_background.test_import.test_reservations.constants import PATH, TASK_TYPE
from background.serializers.validators.for_import.reservations_instances import FileInstancesChecker

User = get_user_model()

__get_response = functools.partial(request_response_create, path=PATH)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture(
            "import_reservations__via_geo_point_and_project_scheme_with_time__with_user_phone__file_fi"
        ),
    ],
)
def test__accepted_owner__success(
    api_client,
    mock_policies_false,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_schedule_time_slot_fi,
    get_geo_point_fi,
    get_project_scheme_fi,
    file,
):
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(import_reservations_task, "delay", lambda *a, **k: None)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: get_random_int())

    gp = get_geo_point_fi(company=r_cu.company)
    monkeypatch.setattr(FileInstancesChecker, "set_geo_point", lambda *a, **kw: None)
    monkeypatch.setattr(FileInstancesChecker, "geo_points_ids", [gp.id])

    ps = get_project_scheme_fi(company=r_cu.company)
    monkeypatch.setattr(FileInstancesChecker, "set_project_scheme", lambda *a, **kw: None)
    monkeypatch.setattr(FileInstancesChecker, "project_schemes_ids", [ps.id])

    sts = get_schedule_time_slot_fi(company=r_cu.company)
    monkeypatch.setattr(FileInstancesChecker, "set_schedule_time_slot", lambda *a, **kw: None)
    monkeypatch.setattr(FileInstancesChecker, "schedule_time_slots_ids", [sts.id])

    data = new_background_task_data(company=r_cu.company)
    data["files"] = [file]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instance = BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE)
    assert len(created_instance) == 1
    assert response.data["id"] == created_instance.first().id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS_VALUES)
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture(
            "import_reservations__via_geo_point_and_project_scheme_with_time__with_user_phone__file_fi"
        ),
    ],
)
def test__not_accepted_owner__fail(
    api_client,
    monkeypatch,
    get_cu_owner_fi,
    new_background_task_data,
    file,
    status,
):
    r_cu = get_cu_owner_fi(status=status)
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(import_reservations_task, "delay", lambda *a, **k: None)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: get_random_int())
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    data = new_background_task_data(company=r_cu.company)
    data["files"] = [file]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture(
            "import_reservations__via_geo_point_and_project_scheme_with_time__with_user_phone__file_fi"
        ),
    ],
)
def test__accepted_manager_with_policy__success(
    api_client,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_schedule_time_slot_fi,
    get_geo_point_fi,
    get_project_scheme_fi,
    file,
):
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(import_reservations_task, "delay", lambda *a, **k: None)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: get_random_int())
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    gp = get_geo_point_fi(company=r_cu.company)
    monkeypatch.setattr(FileInstancesChecker, "set_geo_point", lambda *a, **kw: None)
    monkeypatch.setattr(FileInstancesChecker, "geo_points_ids", [gp.id])

    ps = get_project_scheme_fi(company=r_cu.company)
    monkeypatch.setattr(FileInstancesChecker, "set_project_scheme", lambda *a, **kw: None)
    monkeypatch.setattr(FileInstancesChecker, "project_schemes_ids", [ps.id])

    sts = get_schedule_time_slot_fi(company=r_cu.company)
    monkeypatch.setattr(FileInstancesChecker, "set_schedule_time_slot", lambda *a, **kw: None)
    monkeypatch.setattr(FileInstancesChecker, "schedule_time_slots_ids", [sts.id])

    data = new_background_task_data(company=r_cu.company)
    data["files"] = [file]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instance = BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE)
    assert len(created_instance) == 1
    assert response.data["id"]


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture(
            "import_reservations__via_geo_point_and_project_scheme_with_time__with_user_phone__file_fi"
        ),
    ],
)
def test__not__accepted_manager_with_policy__fail(
    api_client,
    monkeypatch,
    get_cu_manager_fi,
    new_background_task_data,
    get_schedule_time_slot_fi,
    get_geo_point_fi,
    get_project_scheme_fi,
    file,
    status,
):
    r_cu = get_cu_manager_fi(status=status)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    data = new_background_task_data(company=r_cu.company)
    data["files"] = [file]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture(
            "import_reservations__via_geo_point_and_project_scheme_with_time__with_user_phone__file_fi"
        ),
    ],
)
def test__accepted_manager_without_policy__fail(
    api_client,
    mock_policies_false,
    r_cu,
    new_background_task_data,
    get_schedule_time_slot_fi,
    get_geo_point_fi,
    get_project_scheme_fi,
    file,
):
    data = new_background_task_data(company=r_cu.company)
    data["files"] = [file]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PermissionDenied.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture("import_reservations__invalid_format__file_fi"),
    ],
)
def test__invalid_file_format__fail(
    api_client,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_project_territory_fi,
    workers__phones__docx_file_fi,
    file,
):
    filename = file.name.split("/")[-1]

    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(import_reservations_task, "delay", lambda *a, **k: None)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    data = new_background_task_data(company=r_cu.company)
    data["files"] = [file]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == {"non_field_errors": [USE_COMMON_ALLOWED_FILE_FORMATS.format(filename=filename)]}
    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture("import_reservations__via_schedule_time_slots_with_time__with_user_id__file_fi"),
        pytest.lazy_fixture(
            "import_reservations__via_schedule_time_slot__without_time__with_user_id__file_fi"
        ),
    ],
)
def test__with_user_id__success(
    api_client,
    mock_policies_false,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_schedule_time_slot_fi,
    get_geo_point_fi,
    get_project_scheme_fi,
    get_user_fi,
    file,
):
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(import_reservations_task, "delay", lambda *a, **k: None)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: get_random_int())

    user = get_user_fi()
    monkeypatch.setattr(FileInstancesChecker, "set_user", lambda *a, **kw: None)
    monkeypatch.setattr(FileInstancesChecker, "users_ids", [user.id])

    gp = get_geo_point_fi(company=r_cu.company)
    monkeypatch.setattr(FileInstancesChecker, "set_geo_point", lambda *a, **kw: None)
    monkeypatch.setattr(FileInstancesChecker, "geo_points_ids", [gp.id])

    ps = get_project_scheme_fi(company=r_cu.company)
    monkeypatch.setattr(FileInstancesChecker, "set_project_scheme", lambda *a, **kw: None)
    monkeypatch.setattr(FileInstancesChecker, "project_schemes_ids", [ps.id])

    sts = get_schedule_time_slot_fi(company=r_cu.company)
    monkeypatch.setattr(FileInstancesChecker, "set_schedule_time_slot", lambda *a, **kw: None)
    monkeypatch.setattr(FileInstancesChecker, "schedule_time_slots_ids", [sts.id])

    data = new_background_task_data(company=r_cu.company)
    data["files"] = [file]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instance = BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE)
    assert len(created_instance) == 1
    assert response.data["id"] == created_instance.first().id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture(
            "import_reservations__via_geo_point_and_project_scheme_with_time__with_user_phone__file_fi"
        ),
    ],
)
def test__user_with_phone__success(
    api_client,
    mock_policies_false,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_schedule_time_slot_fi,
    get_geo_point_fi,
    get_project_scheme_fi,
    file,
):
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(import_reservations_task, "delay", lambda *a, **k: None)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: get_random_int())

    gp = get_geo_point_fi(company=r_cu.company)
    monkeypatch.setattr(FileInstancesChecker, "set_geo_point", lambda *a, **kw: None)
    monkeypatch.setattr(FileInstancesChecker, "geo_points_ids", [gp.id])

    ps = get_project_scheme_fi(company=r_cu.company)
    monkeypatch.setattr(FileInstancesChecker, "set_project_scheme", lambda *a, **kw: None)
    monkeypatch.setattr(FileInstancesChecker, "project_schemes_ids", [ps.id])

    sts = get_schedule_time_slot_fi(company=r_cu.company)
    monkeypatch.setattr(FileInstancesChecker, "set_schedule_time_slot", lambda *a, **kw: None)
    monkeypatch.setattr(FileInstancesChecker, "schedule_time_slots_ids", [sts.id])

    data = new_background_task_data(company=r_cu.company)
    data["files"] = [file]

    assert not BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE).exists()
    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instance = BackgroundTask.objects.filter(company=r_cu.company, task_type=TASK_TYPE)
    assert len(created_instance) == 1
    assert response.data["id"] == created_instance.first().id


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
    get_project_territory_fi,
    user_attr: str,
    value: bool,
    err_msg: str,
    import_reservations__via_geo_point_and_project_scheme_with_time__with_user_phone__file_fi,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    setattr(r_cu.user, user_attr, value)
    r_cu.user.save()
    company = r_cu.company
    data = new_background_task_data(company=company)
    data["files"] = [
        import_reservations__via_geo_point_and_project_scheme_with_time__with_user_phone__file_fi
    ]
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data["detail"] == err_msg


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture(
            "import_reservations__via_geo_point_and_project_scheme_with_time__with_user_phone__file_fi"
        ),
    ],
)
def test__accepted_owner__success(
    api_client,
    mock_policies_false,
    monkeypatch,
    r_cu,
    new_background_task_data,
    get_schedule_time_slot_fi,
    get_geo_point_fi,
    get_project_scheme_fi,
    file,
):
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(import_reservations_task, "delay", lambda *a, **k: None)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: get_random_int())

    gp = get_geo_point_fi(company=r_cu.company)
    monkeypatch.setattr(FileInstancesChecker, "set_geo_point", lambda *a, **kw: None)
    monkeypatch.setattr(FileInstancesChecker, "geo_points_ids", [gp.id])

    ps = get_project_scheme_fi(company=r_cu.company)
    monkeypatch.setattr(FileInstancesChecker, "set_project_scheme", lambda *a, **kw: None)
    monkeypatch.setattr(FileInstancesChecker, "project_schemes_ids", [ps.id])

    sts = get_schedule_time_slot_fi(company=r_cu.company)
    monkeypatch.setattr(FileInstancesChecker, "set_schedule_time_slot", lambda *a, **kw: None)
    monkeypatch.setattr(FileInstancesChecker, "schedule_time_slots_ids", [sts.id])

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
    assert response_instance.pop("model_name") == "Reservation"
    assert response_instance.pop("task_type") == TASK_TYPE
    assert response_instance.pop("status") == BackgroundTaskStatus.PENDING.value
    assert response_instance.pop("created_at")
    assert response_instance.pop("updated_at")
    input_files = response_instance.pop("input_files")
    assert input_files
    assert len(input_files) == 1 and len(input_files[0]) == 2
    filename = "import_reservations__via_geo_point_and_project_scheme_with_time__with_user_phone.xlsx"
    assert input_files[0]["basename"] == filename and input_files[0]["values"]

    assert response_instance.pop("params") == dict()
    assert not response_instance.pop("result")
    assert not response_instance.pop("output_files")
    assert not response_instance.pop("failures")

    assert not response_instance
