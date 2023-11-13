import pytest
from rest_framework.exceptions import PermissionDenied

from accounts.models import USER_IS_BLOCKED, NOT_TA_R_U__DELETED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from projects.models.project import PROJECT_IS_DELETED
from ma_saas.constants.system import Callable
from ma_saas.constants.project import NOT_ACTIVE_PROJECT_STATUS_VALUES
from clients.policies.interface import Policies
from companies.models.company_user import CompanyUser
from projects.models.project_territory import NOT_TA_PT_REASON
from reports.permissions.worker_report import GEO_POINT_PROJECT_STATUS_MUST_BE_ACTIVE
from projects.models.contractor_project_territory_worker import NOT_TA_REQUESTING_PT_WORKER_REASON
from tests.test_app_reports.test_worker_reports.test_create.test_common import __get_response


@pytest.mark.parametrize("project_status", NOT_ACTIVE_PROJECT_STATUS_VALUES)
def test__not_active_project__fail(
    api_client,
    get_pt_worker_fi,
    get_reservation_fi: Callable,
    get_project_fi: Callable,
    new_worker_report_data,
    get_schedule_time_slot_fi,
    project_status,
):
    project = get_project_fi(status=project_status)
    requesting_pt_worker = get_pt_worker_fi(project=project)
    schedule_time_slot = get_schedule_time_slot_fi(project_territory=requesting_pt_worker.project_territory)
    get_reservation_fi(project_territory_worker=requesting_pt_worker, schedule_time_slot=schedule_time_slot)

    data = new_worker_report_data(schedule_time_slot=schedule_time_slot)
    response = __get_response(
        api_client, data, requesting_pt_worker.company_user.user, status_codes=PermissionDenied
    )
    assert response.data == {"detail": GEO_POINT_PROJECT_STATUS_MUST_BE_ACTIVE}


@pytest.mark.parametrize(
    ("is_user", "field", "err_text"),
    (
        (True, "is_blocked", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_BLOCKED)),
        (True, "is_deleted", NOT_TA_R_U__DELETED),
        (False, "is_deleted", REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY),
    ),
)
@pytest.mark.parametrize("has_object_policy", [True, False])
def test__not_ta__cu__fail(
    api_client,
    monkeypatch,
    get_schedule_time_slot_fi,
    get_pt_worker_fi,
    get_reservation_fi,
    new_worker_report_data,
    has_object_policy,
    is_user,
    field,
    err_text,
):
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    requesting_pt_worker = get_pt_worker_fi()
    r_cu = requesting_pt_worker.company_user
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    schedule_time_slot = get_schedule_time_slot_fi(project_territory=requesting_pt_worker.project_territory)
    get_reservation_fi(project_territory_worker=requesting_pt_worker, schedule_time_slot=schedule_time_slot)
    data = new_worker_report_data(schedule_time_slot=schedule_time_slot)

    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()

    else:
        setattr(r_cu, field, True)
        r_cu.save()

    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": err_text}


def test__deleted_project__fail(
    api_client, get_pt_worker_fi, get_schedule_time_slot_fi, get_reservation_fi, new_worker_report_data
):
    pt_worker = get_pt_worker_fi()
    schedule_time_slot = get_schedule_time_slot_fi(project_territory=pt_worker.project_territory)
    get_reservation_fi(project_territory_worker=pt_worker, schedule_time_slot=schedule_time_slot)
    data = new_worker_report_data(schedule_time_slot=schedule_time_slot)

    pt_worker.project_territory.project.is_deleted = True
    pt_worker.project_territory.project.save()

    response = __get_response(api_client, data, pt_worker.company_user.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": NOT_TA_REQUESTING_PT_WORKER_REASON.format(
            reason=NOT_TA_PT_REASON.format(reason=PROJECT_IS_DELETED)
        )
    }
