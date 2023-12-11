import pytest

from geo_objects.models import GeoPoint
from clients.policies.interface import Policies
from tasks.models.schedule_time_slot import ScheduleTimeSlot
from projects.models.project_territory import ProjectTerritory
from tests.test_app_projects.test_project_territory.test_update import __get_response


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__geo_points__is_same_reward_update__success(
    api_client, monkeypatch, r_cu, get_project_territory_fi, get_geo_point_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_project_territory_fi(company=r_cu.company, reward=999)
    gp1 = get_geo_point_fi(project_territory=instance, reward=instance.reward)
    gp2 = get_geo_point_fi(project_territory=instance, reward=0)

    new_reward = 222
    data = {"reward": new_reward, "is_update_child_same_reward": True}
    response = __get_response(api_client, instance.id, data, user=r_cu.user)

    updated_instance = ProjectTerritory.objects.get(id=instance.id)
    updated_gp1 = GeoPoint.objects.get(id=gp1.id)
    updated_gp2 = GeoPoint.objects.get(id=gp2.id)

    assert updated_instance.reward == new_reward == response.data["reward"] == updated_gp1.reward
    assert updated_gp2.reward != new_reward


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__geo_points__is_not_same_reward_update__success(
    api_client, monkeypatch, r_cu, get_project_territory_fi, get_geo_point_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    old_reward = 999
    instance = get_project_territory_fi(company=r_cu.company, reward=old_reward)
    gp1 = get_geo_point_fi(project_territory=instance, reward=instance.reward)
    gp2 = get_geo_point_fi(project_territory=instance, reward=0)

    new_reward = 222
    data = {"reward": new_reward, "is_update_child_same_reward": False}
    response = __get_response(api_client, instance.id, data, user=r_cu.user)

    updated_instance = ProjectTerritory.objects.get(id=instance.id)
    updated_gp1 = GeoPoint.objects.get(id=gp1.id)
    updated_gp2 = GeoPoint.objects.get(id=gp2.id)

    assert updated_instance.reward == new_reward == response.data["reward"]
    assert updated_gp1.reward == old_reward
    assert updated_gp2.reward != new_reward


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__geo_points__without_is_same_reward_update__success(
    api_client, monkeypatch, r_cu, get_project_territory_fi, get_geo_point_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    old_reward = 999
    instance = get_project_territory_fi(company=r_cu.company, reward=old_reward)
    gp1 = get_geo_point_fi(project_territory=instance, reward=instance.reward)
    gp2 = get_geo_point_fi(project_territory=instance, reward=0)

    new_reward = 222
    data = {"reward": new_reward}
    response = __get_response(api_client, instance.id, data, user=r_cu.user)

    updated_instance = ProjectTerritory.objects.get(id=instance.id)
    updated_gp1 = GeoPoint.objects.get(id=gp1.id)
    updated_gp2 = GeoPoint.objects.get(id=gp2.id)

    assert updated_instance.reward == new_reward == response.data["reward"]
    assert updated_gp1.reward == old_reward
    assert updated_gp2.reward != new_reward


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__schedule_time_slots__is_same_reward_update__success(
    api_client, monkeypatch, r_cu, get_project_territory_fi, get_schedule_time_slot_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_project_territory_fi(company=r_cu.company, reward=999)
    sts1 = get_schedule_time_slot_fi(project_territory=instance, reward=instance.reward)
    sts2 = get_schedule_time_slot_fi(project_territory=instance, reward=0)

    new_reward = 222
    data = {"reward": new_reward, "is_update_child_same_reward": True}

    response = __get_response(api_client, instance.id, data, user=r_cu.user)

    updated_instance = ProjectTerritory.objects.get(id=instance.id)
    updated_sts1 = ScheduleTimeSlot.objects.get(id=sts1.id)
    updated_sts2 = ScheduleTimeSlot.objects.get(id=sts2.id)

    assert updated_instance.reward == new_reward == response.data["reward"] == updated_sts1.reward
    assert updated_sts2.reward != new_reward


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__schedule_time_slots__is_not_same_reward_update__success(
    api_client, monkeypatch, r_cu, get_project_territory_fi, get_schedule_time_slot_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    old_reward = 999
    instance = get_project_territory_fi(company=r_cu.company, reward=old_reward)
    sts1 = get_schedule_time_slot_fi(project_territory=instance, reward=instance.reward)
    sts2 = get_schedule_time_slot_fi(project_territory=instance, reward=0)

    new_reward = 222
    data = {"reward": new_reward, "is_update_child_same_reward": False}

    response = __get_response(api_client, instance.id, data, user=r_cu.user)

    updated_instance = ProjectTerritory.objects.get(id=instance.id)
    updated_sts1 = ScheduleTimeSlot.objects.get(id=sts1.id)
    updated_sts2 = ScheduleTimeSlot.objects.get(id=sts2.id)

    assert updated_instance.reward == new_reward == response.data["reward"]
    assert updated_sts1.reward == old_reward
    assert updated_sts2.reward != new_reward


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__schedule_time_slots__without_is_not_same_reward_update__success(
    api_client, monkeypatch, r_cu, get_project_territory_fi, get_schedule_time_slot_fi
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])
    old_reward = 999
    instance = get_project_territory_fi(company=r_cu.company, reward=old_reward)
    sts1 = get_schedule_time_slot_fi(project_territory=instance, reward=instance.reward)
    sts2 = get_schedule_time_slot_fi(project_territory=instance, reward=0)

    new_reward = 222
    data = {"reward": new_reward, "is_update_child_same_reward": False}

    response = __get_response(api_client, instance.id, data, user=r_cu.user)

    updated_instance = ProjectTerritory.objects.get(id=instance.id)
    updated_sts1 = ScheduleTimeSlot.objects.get(id=sts1.id)
    updated_sts2 = ScheduleTimeSlot.objects.get(id=sts2.id)

    assert updated_instance.reward == new_reward == response.data["reward"]
    assert updated_sts1.reward == old_reward
    assert updated_sts2.reward != new_reward
