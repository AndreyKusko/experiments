import pytest
import requests
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from tests.utils import get_random_int
from ma_saas.utils import queryset
from background.models import BackgroundTask
from ma_saas.utils.queryset import get_existing_obj_or_404
from tests.mocked_instances import MockResponse
from ma_saas.constants.system import VALUES, BASENAME
from tasks.models.reservation import Reservation
from ma_saas.constants.company import CUS
from companies.models.company_user import CompanyUser
from clients.objects_store.interface import ObjectsStore
from ma_saas.constants.background_task import BackgroundTaskStatus
from clients.notifications.interfaces.sms import SendSMS
from background.tasks.for_import.reservations import CreateReservationsFromFile
from background.tasks.for_import.reservations import import_reservations_task as _task
from companies.serializers.utils.company_user_invite import InviteUserUtils
from projects.models.contractor_project_territory_worker import ContractorProjectTerritoryWorker
from tests.test_app_background.test_import.test_reservations.constants import MODEL_N_TYPE

ERROR_TXT = "Error text."

User = get_user_model()


def raise_error():
    raise Exception(ERROR_TXT)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture(
            "import_reservations__via_geo_point_and_project_scheme_with_time__with_user_phone__file_fi"
        ),
        pytest.lazy_fixture(
            "import_reservations__via_schedule_time_slot__without_time__with_user_id__file_fi"
        ),
        pytest.lazy_fixture("import_reservations__via_schedule_time_slots_with_time__with_user_id__file_fi"),
    ],
)
def test__file_with_phones_only__instance_data(
    monkeypatch,
    mock_datetime_to_noon,
    r_cu,
    get_background_task_fi,
    get_project_fi,
    get_schedule_time_slot_fi,
    get_pt_worker_fi,
    get_geo_point_fi,
    file,
):
    filename = file.name.split("/")[-1]

    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(content=file.read()))
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: str(get_random_int()))

    input_files = [{BASENAME: filename, VALUES: [get_random_string()]}]
    instance = get_background_task_fi(company_user=r_cu, **MODEL_N_TYPE, input_files=input_files)

    sts = get_schedule_time_slot_fi(company=r_cu.company)
    monkeypatch.setattr(CreateReservationsFromFile, "_retrieve_schedule_time_slot", lambda *a, **kw: sts)
    monkeypatch.setattr(CreateReservationsFromFile, "_retrieve_geo_point", lambda *a, **kw: sts.geo_point)

    ptw = get_pt_worker_fi(project_territory=sts.geo_point.project_territory)
    monkeypatch.setattr(CreateReservationsFromFile, "_get_project_territory_worker", lambda *a, **kw: ptw)

    _task.run(background_task_id=instance.id)

    updated_instance = BackgroundTask.objects.get(id=instance.id)
    assert updated_instance.failures == [{"failures": [], "filename": filename, "fails_qty": 0}]
    assert updated_instance.status == BackgroundTaskStatus.COMPLETED.value
    assert updated_instance.result == [{"filename": filename, "success_qty": 1}]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture(
            "import_reservations__via_geo_point_and_project_scheme_with_time__with_user_phone__file_fi"
        ),
    ],
)
def test__if_not_related_geo_point__fail(
    monkeypatch,
    mock_datetime_to_noon,
    r_cu,
    get_background_task_fi,
    get_project_fi,
    get_schedule_time_slot_fi,
    get_pt_worker_fi,
    file,
):
    filename = file.name.split("/")[-1]

    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(content=file.read()))
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: str(get_random_int()))

    input_files = [{BASENAME: filename, VALUES: [get_random_string()]}]
    instance = get_background_task_fi(company_user=r_cu, **MODEL_N_TYPE, input_files=input_files)

    sts = get_schedule_time_slot_fi(company=r_cu.company)
    monkeypatch.setattr(CreateReservationsFromFile, "_retrieve_schedule_time_slot", lambda *a, **kw: sts)

    ptw = get_pt_worker_fi(company=r_cu.company)
    monkeypatch.setattr(CreateReservationsFromFile, "_get_project_territory_worker", lambda *a, **kw: ptw)

    _task.run(background_task_id=instance.id)

    updated_instance = BackgroundTask.objects.get(id=instance.id)
    assert updated_instance.failures == [{"failures": [], "filename": filename, "fails_qty": 1}]
    assert updated_instance.status == BackgroundTaskStatus.FAILED.value
    assert updated_instance.result == [{"filename": filename, "success_qty": 0}]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture(
            "import_reservations__via_schedule_time_slot__without_time__with_user_id__file_fi"
        ),
        pytest.lazy_fixture("import_reservations__via_schedule_time_slots_with_time__with_user_id__file_fi"),
    ],
)
def test__not_related_schedule_time_slot__fail(
    monkeypatch,
    mock_datetime_to_noon,
    r_cu,
    get_background_task_fi,
    get_project_fi,
    get_pt_worker_fi,
    get_geo_point_fi,
    file,
):
    filename = file.name.split("/")[-1]

    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(content=file.read()))
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: str(get_random_int()))

    input_files = [{BASENAME: filename, VALUES: [get_random_string()]}]
    instance = get_background_task_fi(company_user=r_cu, **MODEL_N_TYPE, input_files=input_files)

    gp = get_geo_point_fi(company=r_cu.company)
    monkeypatch.setattr(CreateReservationsFromFile, "_retrieve_geo_point", lambda *a, **kw: gp)

    ptw = get_pt_worker_fi(project_territory=gp.project_territory)
    monkeypatch.setattr(CreateReservationsFromFile, "_get_project_territory_worker", lambda *a, **kw: ptw)

    _task.run(background_task_id=instance.id)

    updated_instance = BackgroundTask.objects.get(id=instance.id)
    assert updated_instance.failures == [{"failures": [], "filename": filename, "fails_qty": 1}]
    assert updated_instance.status == BackgroundTaskStatus.FAILED.value
    assert updated_instance.result == [{"filename": filename, "success_qty": 0}]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "file",
    [
        pytest.lazy_fixture(
            "import_reservations__via_schedule_time_slot__without_time__with_user_id__file_fi"
        ),
        pytest.lazy_fixture("import_reservations__via_schedule_time_slots_with_time__with_user_id__file_fi"),
    ],
)
def test__not_related_project_territory_worker__fail(
    monkeypatch,
    mock_datetime_to_noon,
    r_cu,
    get_background_task_fi,
    get_project_fi,
    get_schedule_time_slot_fi,
    get_pt_worker_fi,
    file,
):
    filename = file.name.split("/")[-1]

    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(content=file.read()))
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: str(get_random_int()))

    i_f = [{BASENAME: filename, VALUES: [get_random_string()]}]
    instance = get_background_task_fi(company_user=r_cu, **MODEL_N_TYPE, input_files=i_f)

    sts = get_schedule_time_slot_fi(company=r_cu.company)
    monkeypatch.setattr(CreateReservationsFromFile, "_retrieve_schedule_time_slot", lambda *a, **kw: sts)

    monkeypatch.setattr(CreateReservationsFromFile, "_retrieve_geo_point", lambda *a, **kw: sts.geo_point)

    _task.run(background_task_id=instance.id)

    updated_instance = BackgroundTask.objects.get(id=instance.id)
    assert updated_instance.failures == [{"failures": [], "filename": filename, "fails_qty": 1}]
    assert updated_instance.status == BackgroundTaskStatus.FAILED.value
    assert updated_instance.result == [{"filename": filename, "success_qty": 0}]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "file",
    [pytest.lazy_fixture("import_reservations__via_schedule_time_slots_with_time__with_user_id__file_fi")],
)
@pytest.mark.parametrize("status", CUS.values)
def test__related_to_company_user__u_id__success(
    mocker,
    monkeypatch,
    mock_datetime_to_noon,
    r_cu,
    get_background_task_fi,
    get_project_fi,
    get_schedule_time_slot_fi,
    status,
    get_cu_fi,
    get_pt_worker_fi,
    file,
):
    filename = file.name.split("/")[-1]

    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(content=file.read()))
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: str(get_random_int()))

    i_f = [{BASENAME: filename, VALUES: [get_random_string()]}]
    instance = get_background_task_fi(company_user=r_cu, **MODEL_N_TYPE, input_files=i_f)

    sts = get_schedule_time_slot_fi(company=r_cu.company)
    monkeypatch.setattr(CreateReservationsFromFile, "_retrieve_schedule_time_slot", lambda *a, **kw: sts)
    monkeypatch.setattr(CreateReservationsFromFile, "_retrieve_geo_point", lambda *a, **kw: sts.geo_point)

    existing_cu = get_cu_fi(company=r_cu.company, status=status)
    if status != CUS.INVITE.value:
        assert existing_cu.status != CUS.INVITE.value
    assert not ContractorProjectTerritoryWorker.objects.filter(company_user=existing_cu)
    assert not Reservation.objects.filter(project_territory_worker__company_user=existing_cu).exists()
    monkeypatch.setattr(InviteUserUtils, "get_or_create_user", lambda *a, **kw: existing_cu.user)

    mocker.patch("ma_saas.utils.queryset.get_existing_obj_or_404", return_value=existing_cu.user)

    _task.run(background_task_id=instance.id)

    updated_instance = BackgroundTask.objects.get(id=instance.id)
    assert updated_instance.failures == [{"failures": [], "filename": filename, "fails_qty": 0}]
    assert updated_instance.status == BackgroundTaskStatus.COMPLETED.value
    assert updated_instance.result == [{"filename": filename, "success_qty": 1}]

    updated_cu = CompanyUser.objects.get(id=existing_cu.id)
    if status != CUS.ACCEPT.value:
        assert updated_cu.status == CUS.INVITE.value
    else:
        assert updated_cu.status == CUS.ACCEPT.value

    ptw = ContractorProjectTerritoryWorker.objects.filter(company_user=existing_cu)
    assert ptw.count() == 1


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "file",
    [pytest.lazy_fixture("import_reservations__via_schedule_time_slots_with_time__with_user_id__file_fi")],
)
@pytest.mark.parametrize("status", CUS.values)
def test__related_to_project_territory__u_id__success(
    monkeypatch,
    mocker,
    mock_datetime_to_noon,
    r_cu,
    get_background_task_fi,
    get_project_fi,
    get_schedule_time_slot_fi,
    status,
    get_cu_worker_fi,
    get_pt_worker_fi,
    file,
):
    filename = file.name.split("/")[-1]

    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(content=file.read()))
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: str(get_random_int()))

    i_f = [{BASENAME: filename, VALUES: [get_random_string()]}]
    instance = get_background_task_fi(company_user=r_cu, **MODEL_N_TYPE, input_files=i_f)

    sts = get_schedule_time_slot_fi(company=r_cu.company)
    monkeypatch.setattr(CreateReservationsFromFile, "_retrieve_schedule_time_slot", lambda *a, **kw: sts)

    monkeypatch.setattr(CreateReservationsFromFile, "_retrieve_geo_point", lambda *a, **kw: sts.geo_point)

    existing_cu = get_cu_worker_fi(company=r_cu.company, status=status)
    if status != CUS.INVITE.value:
        assert existing_cu.status != CUS.INVITE.value

    ptw = get_pt_worker_fi(company_user=existing_cu, project_territory=sts.geo_point.project_territory)
    assert not Reservation.objects.filter(project_territory_worker=ptw).exists()
    mocker.patch("ma_saas.utils.queryset.get_existing_obj_or_404", return_value=ptw.company_user.user)
    _task.run(background_task_id=instance.id)

    updated_instance = BackgroundTask.objects.get(id=instance.id)
    assert updated_instance.failures == [{"failures": [], "filename": filename, "fails_qty": 0}]
    assert updated_instance.status == BackgroundTaskStatus.COMPLETED.value
    assert updated_instance.result == [{"filename": filename, "success_qty": 1}]

    updated_cu = CompanyUser.objects.get(id=existing_cu.id)
    if status != CUS.ACCEPT.value:
        assert updated_cu.status == CUS.INVITE.value
    else:
        assert updated_cu.status == CUS.ACCEPT.value
    assert Reservation.objects.filter(project_territory_worker=ptw).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    "file",
    [pytest.lazy_fixture("import_reservations__via_schedule_time_slots_with_time__with_user_id__file_fi")],
)
def test__not_related_to_company__u_id__success(
    mocker,
    monkeypatch,
    mock_datetime_to_noon,
    r_cu,
    get_background_task_fi,
    get_project_fi,
    get_schedule_time_slot_fi,
    get_user_fi,
    get_pt_worker_fi,
    file,
):
    filename = file.name.split("/")[-1]

    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse(content=file.read()))
    monkeypatch.setattr(requests, "post", MockResponse, raising=True)
    monkeypatch.setattr(SendSMS, "send_sms", lambda *args, **kwargs: None)
    monkeypatch.setattr(ObjectsStore, "upload_file", lambda *a, **kw: str(get_random_int()))

    i_f = [{BASENAME: filename, VALUES: [get_random_string()]}]
    instance = get_background_task_fi(company_user=r_cu, **MODEL_N_TYPE, input_files=i_f)

    sts = get_schedule_time_slot_fi(company=r_cu.company)
    monkeypatch.setattr(CreateReservationsFromFile, "_retrieve_schedule_time_slot", lambda *a, **kw: sts)

    monkeypatch.setattr(CreateReservationsFromFile, "_retrieve_geo_point", lambda *a, **kw: sts.geo_point)

    user = get_user_fi()
    assert not CompanyUser.objects.filter(user=user).exists()
    assert not ContractorProjectTerritoryWorker.objects.filter(company_user__user=user).exists()
    assert not Reservation.objects.filter(project_territory_worker__company_user__user=user).exists()

    mocker.patch("ma_saas.utils.queryset.get_existing_obj_or_404", return_value=user)

    _task.run(background_task_id=instance.id)

    updated_instance = BackgroundTask.objects.get(id=instance.id)
    assert updated_instance.failures == [{"failures": [], "filename": filename, "fails_qty": 0}]
    assert updated_instance.status == BackgroundTaskStatus.COMPLETED.value
    assert updated_instance.result == [{"filename": filename, "success_qty": 1}]

    updated_cu = CompanyUser.objects.filter(user=user)
    assert updated_cu
    assert updated_cu.first().status == CUS.INVITE.value
    assert ContractorProjectTerritoryWorker.objects.filter(company_user__user=user).count() == 1
    assert Reservation.objects.filter(project_territory_worker__company_user__user=user).count() == 1
