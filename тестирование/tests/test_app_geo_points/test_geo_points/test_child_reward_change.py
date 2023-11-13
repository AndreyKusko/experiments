import pytest

from geo_objects.models import GeoPoint
from clients.policies.interface import Policies
from tasks.models.schedule_time_slot import ScheduleTimeSlot

from .test_update import __get_response


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__schedule_time_slots__is_update_child_same_reward(
    api_client, monkeypatch, r_cu, get_geo_point_fi, get_schedule_time_slot_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    old_reward = 999
    instance = get_geo_point_fi(company=r_cu.company, reward=old_reward)
    sts1 = get_schedule_time_slot_fi(geo_point=instance, reward=instance.reward)
    sts2 = get_schedule_time_slot_fi(geo_point=instance, reward=0)

    new_reward = 222
    data = {"reward": new_reward, "is_update_child_same_reward": True}
    response = __get_response(api_client, instance.id, data, user=r_cu.user)

    updated_instance = GeoPoint.objects.get(id=instance.id)
    updated_sts1 = ScheduleTimeSlot.objects.get(id=sts1.id)
    updated_sts2 = ScheduleTimeSlot.objects.get(id=sts2.id)

    assert updated_instance.reward == new_reward == response.data["reward"]
    assert updated_sts1.reward == new_reward
    assert updated_sts2.reward != new_reward


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__schedule_time_slots__is_not_update_childrens_same_reward(
    api_client, monkeypatch, r_cu, get_geo_point_fi, get_schedule_time_slot_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    old_reward = 999
    instance = get_geo_point_fi(company=r_cu.company, reward=old_reward)
    sts1 = get_schedule_time_slot_fi(geo_point=instance, reward=instance.reward)
    sts2 = get_schedule_time_slot_fi(geo_point=instance, reward=0)

    new_reward = 222
    data = {"reward": new_reward, "is_update_child_same_reward": False}
    response = __get_response(api_client, instance.id, data, user=r_cu.user)

    updated_instance = GeoPoint.objects.get(id=instance.id)
    updated_sts1 = ScheduleTimeSlot.objects.get(id=sts1.id)
    updated_sts2 = ScheduleTimeSlot.objects.get(id=sts2.id)

    assert updated_instance.reward == new_reward == response.data["reward"]
    assert updated_sts1.reward == old_reward
    assert updated_sts2.reward != new_reward


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__schedule_time_slots__without_is_update_child_same_reward(
    api_client, monkeypatch, r_cu, get_geo_point_fi, get_schedule_time_slot_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    old_reward = 999
    instance = get_geo_point_fi(company=r_cu.company, reward=old_reward)
    sts1 = get_schedule_time_slot_fi(geo_point=instance, reward=instance.reward)
    sts2 = get_schedule_time_slot_fi(geo_point=instance, reward=0)

    new_reward = 222
    data = {"reward": new_reward}
    response = __get_response(api_client, instance.id, data, user=r_cu.user)

    updated_instance = GeoPoint.objects.get(id=instance.id)
    updated_sts1 = ScheduleTimeSlot.objects.get(id=sts1.id)
    updated_sts2 = ScheduleTimeSlot.objects.get(id=sts2.id)

    assert updated_instance.reward == new_reward == response.data["reward"]
    assert updated_sts1.reward == old_reward
    assert updated_sts2.reward != new_reward
