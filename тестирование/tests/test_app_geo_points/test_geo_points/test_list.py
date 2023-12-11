import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated

from tests.utils import request_response_list
from ma_saas.constants.company import NOT_ACCEPT_CUS
from clients.policies.interface import Policies

User = get_user_model()

__get_response = functools.partial(request_response_list, path="/api/v1/geo-points/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("qty", (3,))
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, get_geo_point_fi, qty):
    [get_geo_point_fi(company=r_cu.company) for _ in range(qty)]
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == qty


@pytest.mark.parametrize("qty", (3,))
@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__fail(api_client, monkeypatch, get_cu_owner_fi, get_geo_point_fi, status, qty):
    r_cu = get_cu_owner_fi(status=status)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    [get_geo_point_fi(company=r_cu.company) for _ in range(qty)]
    response = __get_response(api_client, user=r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("qty", (3,))
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager__with_policy__success(
    api_client, monkeypatch, get_geo_point_fi, r_cu, qty, get_project_territory_fi
):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    pt = get_project_territory_fi(company=r_cu.company)
    [get_geo_point_fi(project_territory=pt) for _ in range(qty)]
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == qty


@pytest.mark.parametrize("qty", (3,))
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager__without_policy__fail(
    api_client, mock_policies_false, get_geo_point_fi, r_cu, qty, get_project_territory_fi
):
    pt = get_project_territory_fi(company=r_cu.company)
    [get_geo_point_fi(project_territory=pt) for _ in range(qty)]
    response = __get_response(api_client, user=r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("qty", (3,))
def test__not_accepted_manager__with_policy__fail(
    api_client, monkeypatch, get_geo_point_fi, get_cu_manager_fi, qty, get_project_territory_fi
):
    r_cu = get_cu_manager_fi()
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    pt = get_project_territory_fi(company=r_cu.company)
    [get_geo_point_fi(project_territory=pt) for _ in range(qty)]
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == qty


@pytest.mark.parametrize("qty", (3,))
@pytest.mark.parametrize("is_policy", [True, False])
@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__accepted_related_worker__success(
    api_client, monkeypatch, get_geo_point_fi, qty, pt_worker, is_policy
):
    r_cu, pt = pt_worker.company_user, pt_worker.project_territory
    if is_policy:
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    else:
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])

    [get_geo_point_fi(project_territory=pt) for _ in range(qty)]
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == qty


@pytest.mark.parametrize("is_policy", [True, False])
@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_related_worker__fail(
    api_client, monkeypatch, get_geo_point_fi, get_cu_worker_fi, get_pt_worker_fi, is_policy, status
):
    r_cu = get_cu_worker_fi(status=status)
    pt_worker = get_pt_worker_fi(company_user=r_cu)
    pt = pt_worker.project_territory
    if is_policy:
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    else:
        monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])

    get_geo_point_fi(project_territory=pt)
    response = __get_response(api_client, user=r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("is_policy", [True, False])
@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__not_related__accepted_worker__with_policy__sucsess(
    api_client, monkeypatch, get_geo_point_fi, pt_worker, is_policy
):
    r_cu, pt = pt_worker.company_user, pt_worker.project_territory
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    instance = get_geo_point_fi(company=r_cu.company)
    response = __get_response(api_client, user=r_cu.user)
    assert len(response.data) == 1
    assert response.data[0]["id"] == instance.id


@pytest.mark.parametrize("is_policy", [True, False])
@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__not_related__accepted_related_worker__without_policy__fail(
    api_client, monkeypatch, get_geo_point_fi, pt_worker, is_policy
):
    r_cu, pt = pt_worker.company_user, pt_worker.project_territory
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])
    get_geo_point_fi(company=r_cu.company)
    response = __get_response(api_client, user=r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__different_company_user__empty_response(
    api_client, monkeypatch, r_cu, new_geo_point_data, get_geo_point_fi
):
    geo_point = get_geo_point_fi()
    monkeypatch.setattr(
        Policies, "get_target_policies", lambda *a, **kw: [geo_point.project_territory.project.company.id]
    )
    response = __get_response(api_client, user=r_cu.user)
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(api_client, mock_policies_false, r_cu, get_geo_point_fi):
    instance = get_geo_point_fi(company=r_cu.company)
    response = __get_response(api_client, user=r_cu.user)
    response_instance = response.data[0]
    assert response_instance.pop("id") == instance.id
    assert response_instance.pop("title") == instance.title
    assert response_instance.pop("lat") == instance.lat
    assert response_instance.pop("lon") == instance.lon
    assert response_instance.pop("city") == instance.city
    assert response_instance.pop("address") == instance.address
    assert response_instance.pop("timezone_name") == instance.timezone_name
    assert response_instance.pop("additional") == instance.additional
    assert response_instance.pop("utc_offset") == instance.utc_offset
    assert response_instance.pop("reward") == instance.reward
    assert response_instance.pop("is_active") == instance.is_active
    assert (
        response_instance.pop("project_territory__territory__title")
        == instance.project_territory.territory.title
    )
    assert response_instance.pop("project_territory") == instance.project_territory.id
    assert not response_instance
