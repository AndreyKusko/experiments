import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_update
from accounts.models import USER_IS_BLOCKED, USER_IS_DELETED, NOT_TA_REQUESTING_USER_REASON
from geo_objects.models import GeoPoint
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from companies.models.company import COMPANY_IS_DELETED, NOT_TA_COMPANY_REASON
from ma_saas.constants.company import NOT_ACCEPT_CUS
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_REASON, NOT_TA_RCU_MUST_BE_ACCEPT, CompanyUser

User = get_user_model()

__get_response = functools.partial(request_response_update, path="/api/v1/geo-points/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, {}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(
    api_client, mock_policies_false, r_cu, get_geo_point_fi, new_geo_point_data
):
    instance = get_geo_point_fi(company=r_cu.company)
    data = new_geo_point_data(project_territory=instance.project_territory)
    response = __get_response(api_client, instance.id, data=data, user=r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__fail(
    api_client, monkeypatch, get_cu_owner_fi, get_geo_point_fi, new_geo_point_data, status
):
    r_cu = get_cu_owner_fi(status=status)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    instance = get_geo_point_fi(company=r_cu.company)
    data = new_geo_point_data(project_territory=instance.project_territory)
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager__with_policy__success(
    api_client, monkeypatch, r_cu, get_geo_point_fi, new_geo_point_data
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    instance = get_geo_point_fi(company=r_cu.company)
    data = new_geo_point_data(project_territory=instance.project_territory)
    response = __get_response(api_client, instance.id, data=data, user=r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_manager__with_policy__fail(
    api_client, monkeypatch, get_cu_manager_fi, get_geo_point_fi, new_geo_point_data, status
):
    r_cu = get_cu_manager_fi(status=status)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    instance = get_geo_point_fi(company=r_cu.company)
    data = new_geo_point_data(project_territory=instance.project_territory)
    response = __get_response(api_client, instance.id, data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__accepted_manager__without_policy__fail(
    api_client, monkeypatch, r_cu, get_geo_point_fi, new_geo_point_data
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])

    instance = get_geo_point_fi(company=r_cu.company)
    data = new_geo_point_data(project_territory=instance.project_territory)
    response = __get_response(
        api_client, instance.id, data=data, user=r_cu.user, status_codes=PermissionDenied
    )
    assert response.data == {"detail": PermissionDenied.default_detail}


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__related_worker__with_policy__success(
    api_client, monkeypatch, pt_worker, get_geo_point_fi, new_geo_point_data
):
    r_cu, pt = pt_worker.company_user, pt_worker.project_territory
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    instance = get_geo_point_fi(project_territory=pt)
    data = new_geo_point_data(project_territory=instance.project_territory)
    response = __get_response(api_client, instance.id, data=data, user=r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__not_related_worker__with_policy__success(
    api_client, monkeypatch, pt_worker, get_geo_point_fi, new_geo_point_data
):
    r_cu, pt = pt_worker.company_user, pt_worker.project_territory

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    instance = get_geo_point_fi(company=r_cu.company)
    data = new_geo_point_data(project_territory=instance.project_territory)
    response = __get_response(api_client, instance.id, data=data, user=r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_related_worker__with_policy__fail(
    api_client, monkeypatch, get_cu_worker_fi, get_pt_worker_fi, get_geo_point_fi, new_geo_point_data, status
):
    r_cu = get_cu_worker_fi(status=status)
    pt_worker = get_pt_worker_fi(company_user=r_cu)
    pt = pt_worker.project_territory

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    instance = get_geo_point_fi(project_territory=pt)
    data = new_geo_point_data(project_territory=pt)
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__accepted_worker__without_policy__fail(
    api_client, monkeypatch, pt_worker, get_geo_point_fi, new_geo_point_data
):
    r_cu, pt = pt_worker.company_user, pt_worker.project_territory

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])

    instance = get_geo_point_fi(project_territory=pt)
    data = new_geo_point_data(project_territory=pt)
    response = __get_response(
        api_client, instance.id, data=data, user=r_cu.user, status_codes=PermissionDenied
    )
    assert response.data == {"detail": PermissionDenied.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(api_client, monkeypatch, r_cu, get_geo_point_fi, new_geo_point_data):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    instance = get_geo_point_fi(company=r_cu.company)
    data = new_geo_point_data(
        project_territory=instance.project_territory,
        lat=33.7522200,
        lon=33.6155600,
        city="Тула",
        address="Россия, Тула, улица ленина, дом 1",
        reward=1,
        is_active=False,
    )

    response = __get_response(api_client, instance.id, data, r_cu.user)
    updated_instance = GeoPoint.objects.get(id=instance.id)
    response_instance = response.data

    assert response_instance.pop("id") == updated_instance.id
    assert response_instance.pop("title") == updated_instance.title == data["title"] != instance.title
    assert response_instance.pop("lat") == updated_instance.lat == data["lat"] != instance.lat
    assert response_instance.pop("lon") == updated_instance.lon == data["lon"] != instance.lon
    assert (
        response_instance.pop("utc_offset")
        == updated_instance.utc_offset
        == f"+{float(data['utc_offset'])}"
        == instance.utc_offset
    )
    assert response_instance.pop("city") == updated_instance.city == data["city"] != instance.city
    assert response_instance.pop("address") == updated_instance.address == data["address"] != instance.address
    assert response_instance.pop("timezone_name") == updated_instance.timezone_name == instance.timezone_name
    assert response_instance.pop("additional") == updated_instance.additional == instance.additional
    assert response_instance.pop("reward") == updated_instance.reward == data["reward"] != instance.reward
    assert response_instance.pop("is_active") == updated_instance.is_active == data["is_active"]

    assert updated_instance.is_active != instance.is_active
    assert (
        response_instance.pop("project_territory__territory__title")
        == updated_instance.project_territory.territory.title
        == instance.project_territory.territory.title
    )

    assert (
        response_instance.pop("project_territory")
        == updated_instance.project_territory.id
        == data["project_territory"]
        == instance.project_territory.id
    )
    assert not response_instance


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__pt_not_updating(
    api_client, monkeypatch, r_cu, get_geo_point_fi, get_project_territory_fi, new_geo_point_data
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    instance = get_geo_point_fi(company=r_cu.company)
    new_pt = get_project_territory_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, {"project_territory": new_pt.id}, r_cu.user)
    updated_instance = GeoPoint.objects.get(id=instance.id)
    response_instance = response.data

    assert (
        response_instance.pop("project_territory")
        == updated_instance.project_territory.id
        == instance.project_territory.id
        != new_pt
    )


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__different_company_user__fail(api_client, new_geo_point_data, get_geo_point_fi, r_cu):
    instance = get_geo_point_fi()
    data = new_geo_point_data()
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__duplicates__fail(api_client, monkeypatch, r_cu, new_geo_point_data, get_geo_point_fi):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    duplicate_instance = get_geo_point_fi(company=r_cu.company)
    instance = get_geo_point_fi(project_territory=duplicate_instance.project_territory)
    data = new_geo_point_data(
        project_territory=duplicate_instance.project_territory,
        title=duplicate_instance.title,
        lat=duplicate_instance.lat,
        lon=duplicate_instance.lon,
    )
    assert __get_response(api_client, instance.id, data, r_cu.user, status_codes=ValidationError)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("is_user", "field", "err_text"),
    (
        (True, "is_blocked", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_BLOCKED)),
        (True, "is_deleted", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_DELETED)),
        (False, "is_deleted", REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY),
    ),
)
@pytest.mark.parametrize("has_object_policy", [True, False])
def test__not_ta__cu__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_geo_point_fi,
    new_geo_point_data,
    has_object_policy,
    is_user,
    field,
    err_text,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()
    else:
        setattr(r_cu, field, True)
        r_cu.save()

    instance = get_geo_point_fi(company=r_cu.company)
    data = new_geo_point_data(project_territory=instance.project_territory)

    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": err_text}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_company__fail(api_client, r_cu, new_geo_point_data, get_geo_point_fi):
    instance = get_geo_point_fi(company=r_cu.company)
    data = new_geo_point_data(project_territory=instance.project_territory)
    r_cu.company.is_deleted = True
    r_cu.company.save()
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": NOT_TA_RCU_REASON.format(reason=NOT_TA_COMPANY_REASON.format(reason=COMPANY_IS_DELETED))
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_pt__fail(
    api_client, monkeypatch, r_cu, new_geo_point_data, get_geo_point_fi, get_project_territory_fi
):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    pt = get_project_territory_fi(company=r_cu.company)
    instance = get_geo_point_fi(project_territory=pt)
    data = new_geo_point_data(project_territory=pt)
    del data["project_territory"]
    pt.is_deleted = True
    pt.save()

    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_project__fail(
    api_client, monkeypatch, r_cu, new_geo_point_data, get_project_fi, get_geo_point_fi
):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    project = get_project_fi(company=r_cu.company)
    instance = get_geo_point_fi(project=project)
    data = new_geo_point_data(project_territory=instance.project_territory)
    project.is_deleted = True
    project.save()
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_territory__fail(
    api_client, monkeypatch, r_cu, new_geo_point_data, get_territory_fi, get_geo_point_fi
):
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    territory = get_territory_fi(company=r_cu.company)
    instance = get_geo_point_fi(territory=territory)
    data = new_geo_point_data(project_territory=instance.project_territory)
    territory.is_deleted = True
    territory.save()
    response = __get_response(api_client, instance.id, data, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}
