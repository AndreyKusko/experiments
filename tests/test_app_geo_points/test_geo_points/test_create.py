import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_create
from accounts.models import USER_IS_BLOCKED, NOT_TA_R_U__DELETED, NOT_TA_REQUESTING_USER_REASON
from geo_objects.models import GEO_POINT_ALREADY_EXISTS, GeoPoint
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from geo_objects.permissions import PT_NOT_FOUND
from projects.models.project import PROJECT_IS_DELETED
from companies.models.company import COMPANY_IS_DELETED, NOT_TA_COMPANY_REASON
from ma_saas.constants.system import Callable
from ma_saas.constants.company import NOT_ACCEPT_CUS
from projects.models.territory import NOT_TA_TERRITORY_IS_DELETED
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_REASON, NOT_TA_RCU_MUST_BE_ACCEPT, CompanyUser
from projects.models.project_territory import NOT_TA_PT_REASON

User = get_user_model()

__get_response = functools.partial(request_response_create, path="/api/v1/geo-points/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, {}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, new_geo_point_data):
    assert not GeoPoint.objects.filter(project_territory__project__company=r_cu.company).exists()
    data = new_geo_point_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instance = GeoPoint.objects.filter(project_territory__project__company=r_cu.company)
    assert len(created_instance) == 1
    assert response.data["id"] == created_instance.first().id


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted__owner__fail(api_client, monkeypatch, get_cu_owner_fi, new_geo_point_data, status):
    r_cu = get_cu_owner_fi(status=status)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    assert not GeoPoint.objects.filter(project_territory__project__company=r_cu.company).exists()
    data = new_geo_point_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}
    assert not GeoPoint.objects.filter(project_territory__project__company=r_cu.company).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__manager__with_policy__success(api_client, monkeypatch, r_cu, new_geo_point_data):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    assert not GeoPoint.objects.filter(project_territory__project__company=r_cu.company).exists()
    data = new_geo_point_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user)
    instances = GeoPoint.objects.filter(project_territory__project__company=r_cu.company)
    assert len(instances) == 1
    assert response.data["id"] == instances.first().id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__manager__without_policy__fail(api_client, mock_policies_false, r_cu, new_geo_point_data):
    assert not GeoPoint.objects.filter(project_territory__project__company=r_cu.company).exists()
    data = new_geo_point_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": PermissionDenied.default_detail}
    assert not GeoPoint.objects.filter(project_territory__project__company=r_cu.company).exists()


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_manager__with_policy__fail(
    api_client, monkeypatch, get_cu_manager_fi, new_geo_point_data, status
):
    r_cu = get_cu_manager_fi(status=status)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    assert not GeoPoint.objects.filter(project_territory__project__company=r_cu.company).exists()

    data = new_geo_point_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)

    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}
    assert not GeoPoint.objects.filter(project_territory__project__company=r_cu.company).exists()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__different_company_user__fail(api_client, monkeypatch, r_cu, new_geo_point_data):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    data = new_geo_point_data()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__duplicates__fail(api_client, monkeypatch, r_cu, new_geo_point_data, get_geo_point_fi):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    duplicate_instance = get_geo_point_fi(company=r_cu.company)
    data = new_geo_point_data(
        project_territory=duplicate_instance.project_territory,
        title=duplicate_instance.title,
        lat=duplicate_instance.lat,
        lon=duplicate_instance.lon,
    )
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == [GEO_POINT_ALREADY_EXISTS]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_company__fail(api_client, monkeypatch, r_cu, new_geo_point_data):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    data = new_geo_point_data(company=r_cu.company)
    r_cu.company.is_deleted = True
    r_cu.company.save()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": NOT_TA_RCU_REASON.format(reason=NOT_TA_COMPANY_REASON.format(reason=COMPANY_IS_DELETED))
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_pt__fail(api_client, monkeypatch, r_cu, new_geo_point_data, get_project_territory_fi):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    pt = get_project_territory_fi(company=r_cu.company)
    data = new_geo_point_data(project_territory=pt)
    pt.is_deleted = True
    pt.save()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": PT_NOT_FOUND}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_project__fail(api_client, monkeypatch, r_cu, new_geo_point_data: Callable, get_project_fi):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    project = get_project_fi(company=r_cu.company)
    data = new_geo_point_data(project=project)
    project.is_deleted = True
    project.save()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == {"project_territory": [NOT_TA_PT_REASON.format(reason=PROJECT_IS_DELETED)]}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_territory__fail(api_client, monkeypatch, r_cu, new_geo_point_data, get_territory_fi):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    territory = get_territory_fi(company=r_cu.company)
    data = new_geo_point_data(territory=territory)
    territory.is_deleted = True
    territory.save()
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == {
        "project_territory": [NOT_TA_PT_REASON.format(reason=NOT_TA_TERRITORY_IS_DELETED)]
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
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
    r_cu,
    new_project_scheme_data,
    new_geo_point_data,
    has_object_policy,
    is_user,
    field,
    err_text,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    data = new_geo_point_data(company=r_cu.company)
    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()
    else:
        setattr(r_cu, field, True)
        r_cu.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": err_text}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_cu, new_geo_point_data):
    assert not GeoPoint.objects.filter(project_territory__project__company=r_cu.company).exists()
    data = new_geo_point_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user)
    created_instance = GeoPoint.objects.filter(project_territory__project__company=r_cu.company).first()

    response_instance = response.data
    assert response_instance.pop("id") == created_instance.id
    assert response_instance.pop("title") == created_instance.title == data["title"]
    assert response_instance.pop("lat") == created_instance.lat == data["lat"]
    assert response_instance.pop("lon") == created_instance.lon == data["lon"]
    assert response_instance.pop("city") == created_instance.city == data["city"]
    assert response_instance.pop("address") == created_instance.address == data["address"]
    assert response_instance.pop("timezone_name") == created_instance.timezone_name
    assert response_instance.pop("additional") == created_instance.additional
    assert response_instance.pop("utc_offset") == created_instance.utc_offset
    assert response_instance.pop("reward") == created_instance.reward == data["reward"]
    assert response_instance.pop("is_active") == created_instance.is_active == data["is_active"]
    assert (
        response_instance.pop("project_territory__territory__title")
        == created_instance.project_territory.territory.title
    )
    assert (
        response_instance.pop("project_territory")
        == created_instance.project_territory.id
        == data["project_territory"]
    )
    assert not response_instance
