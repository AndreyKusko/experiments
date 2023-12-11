import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated

from tests.utils import request_response_delete
from ma_saas.constants.company import CUR, NOT_ACCEPT_CUS
from clients.policies.interface import Policies
from tasks.models.schedule_time_slot import ScheduleTimeSlot

User = get_user_model()

__get_response = functools.partial(request_response_delete, path="/api/v1/schedule-time-slots/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("schedule_time_slot_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codes={NotAuthenticated.status_code})
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__owner__without_policy__fail(api_client, mock_policies_false, r_cu, get_schedule_time_slot_fi):
    instance = get_schedule_time_slot_fi(company=r_cu.company)
    assert __get_response(api_client, instance_id=instance.id, user=r_cu.user, status_codes=NotFound)
    assert ScheduleTimeSlot.objects.existing().filter(id=instance.id).exists()


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__with_policy__fail(
    api_client, mock_policy_true, get_cu_owner_fi, get_schedule_time_slot_fi, status
):
    r_cu = get_cu_owner_fi(status=status)

    mock_policy_true(r_cu.company)

    instance = get_schedule_time_slot_fi(company=r_cu.company)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__related_manager__with_policy__success(
    api_client, mock_policy_true, r_cu, get_schedule_time_slot_fi
):
    mock_policy_true(r_cu.company)

    instance = get_schedule_time_slot_fi(company=r_cu.company)
    assert __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    assert not ScheduleTimeSlot.objects.existing().filter(id=instance.id)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__related_manager__without_policy__success(
    api_client, mock_policies_false, r_cu, get_schedule_time_slot_fi
):
    instance = get_schedule_time_slot_fi(company=r_cu.company)
    assert __get_response(api_client, instance_id=instance.id, user=r_cu.user, status_codes=NotFound)
    assert ScheduleTimeSlot.objects.existing().filter(id=instance.id)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__different_company_user__with_policy__empty_response(
    api_client, mock_policy_true, get_cu_fi, get_schedule_time_slot_fi, r_cu
):
    instance = get_schedule_time_slot_fi()
    company = instance.project_scheme.project.company
    mock_policy_true(company)
    response = __get_response(api_client, user=r_cu.user, instance_id=instance.id, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}
