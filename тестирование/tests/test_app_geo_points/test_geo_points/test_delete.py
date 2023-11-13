import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated

from tests.utils import request_response_delete
from geo_objects.models import GeoPoint
from ma_saas.constants.company import NOT_ACCEPT_CUS
from clients.policies.interface import Policies

User = get_user_model()

__get_response = functools.partial(request_response_delete, path="/api/v1/geo-points/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("geo_point_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codes={NotAuthenticated.status_code})
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, get_geo_point_fi):
    instance = get_geo_point_fi(company=r_cu.company)
    assert __get_response(api_client, instance.id, user=r_cu.user)
    assert GeoPoint.objects.filter(id=instance.id).exists()
    assert not GeoPoint.objects.filter(id=instance.id).existing().exists()


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__fail(api_client, monkeypatch, get_cu_owner_fi, get_geo_point_fi, status):
    r_cu = get_cu_owner_fi(status=status.value)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    instance = get_geo_point_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}
    assert GeoPoint.objects.existing().filter(id=instance.id).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_worker_fi")])
def test__worker__with_policy__success(api_client, monkeypatch, r_cu, get_geo_point_fi):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    instance = get_geo_point_fi(company=r_cu.company)
    assert __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    assert not GeoPoint.objects.existing().filter(id=instance.id).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager__with_policy__success(api_client, monkeypatch, r_cu, get_geo_point_fi):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    instance = get_geo_point_fi(company=r_cu.company)
    assert __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    assert GeoPoint.objects.filter(id=instance.id).exists()
    assert not GeoPoint.objects.filter(id=instance.id).existing().exists()


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_manager__with_policy__fail(
    api_client, monkeypatch, get_cu_manager_fi, get_geo_point_fi, status
):
    r_cu = get_cu_manager_fi(status=status)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    instance = get_geo_point_fi(company=r_cu.company)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}
    assert GeoPoint.objects.existing().filter(id=instance.id).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager__without_policy__fail(api_client, mock_policies_false, r_cu, get_geo_point_fi):
    instance = get_geo_point_fi(company=r_cu.company)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}
    assert GeoPoint.objects.filter(id=instance.id).existing().exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__different_company_user__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_geo_point_fi,
):
    instance = get_geo_point_fi()
    monkeypatch.setattr(
        Policies, "get_target_policies", lambda *a, **kw: [instance.project_territory.project.company.id]
    )
    response = __get_response(api_client, instance.id, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}
