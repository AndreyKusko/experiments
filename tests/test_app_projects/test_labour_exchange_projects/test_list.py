import functools

import pytest
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework.exceptions import NotAuthenticated

from tests.utils import request_response_list, retrieve_response_instance
from ma_saas.constants.system import TITLE
from ma_saas.constants.project import (
    NOT_ACTIVE_PROJECT_STATUS,
    PROJECT_JOB_APPLICATION_ACTIVE_STATUS,
    PROJECT_JOB_APPLICATION_NOT_ACTIVE_STATUS,
)

User = get_user_model()

__get_response = functools.partial(request_response_list, path="/api/v1/labour-exchange-projects/")


def test__anonymous_user__fail(api_client, get_project_fi, get_project_scheme_fi):
    response = __get_response(api_client, status_codes=NotAuthenticated)
    project = get_project_fi()
    get_project_scheme_fi(project=project, is_labour_exchange=True)
    assert response.data == {"detail": NotAuthenticated.default_detail}


def _response_instances_ids(response_data):
    return {ri["id"] for ri in response_data}


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__authenticated_user__success(api_client, r_u, get_project_fi, get_project_scheme_fi):
    project = get_project_fi()
    get_project_scheme_fi(project=project, is_labour_exchange=True)
    response = __get_response(api_client, user=r_u)
    assert project.id in _response_instances_ids(response.data)


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__projects_display(api_client, r_u, get_project_fi, get_project_scheme_fi, get_geo_point_fi):
    project1 = get_project_fi()
    get_project_scheme_fi(project=project1, is_labour_exchange=True)
    project2 = get_project_fi()
    get_project_scheme_fi(project=project2, is_labour_exchange=True)
    project3 = get_project_fi()
    get_project_scheme_fi(project=project3, is_labour_exchange=False)

    get_geo_point_fi(project=project1, city=get_random_string())
    get_geo_point_fi(project=project2, city=get_random_string())
    get_geo_point_fi(project=project3, city=get_random_string())

    response = __get_response(api_client, user=r_u)
    response_ids = _response_instances_ids(response.data)
    assert project1.id in response_ids
    assert project2.id in response_ids
    assert project3.id not in response_ids


def test__related_pt_worker_do_not_display(
    api_client, get_project_fi, get_project_scheme_fi, get_pt_worker_fi, get_geo_point_fi
):
    project = get_project_fi()
    get_project_scheme_fi(project=project, is_labour_exchange=True)
    pt_worker = get_pt_worker_fi(project=project)
    get_geo_point_fi(project=project, city=pt_worker.company_user.user.city)
    response = __get_response(api_client, user=pt_worker.company_user.user)
    assert project.id not in _response_instances_ids(response.data)


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
@pytest.mark.parametrize("status", PROJECT_JOB_APPLICATION_ACTIVE_STATUS)
def test__user_with__application__active_status__do_not_display(
    api_client,
    r_u,
    get_project_fi,
    get_project_scheme_fi,
    get_geo_point_fi,
    get_project_job_application_fi,
    status,
):
    project = get_project_fi()
    get_project_scheme_fi(project=project, is_labour_exchange=True)
    get_geo_point_fi(project=project, city=r_u.city)

    get_project_job_application_fi(project=project, user=r_u, status=status)
    response = __get_response(api_client, user=r_u)
    assert project.id not in _response_instances_ids(response.data)


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
@pytest.mark.parametrize("status", PROJECT_JOB_APPLICATION_NOT_ACTIVE_STATUS)
def test__user_with__application__active_not_status__display(
    api_client,
    r_u,
    get_project_fi,
    get_project_scheme_fi,
    get_project_job_application_fi,
    get_geo_point_fi,
    status,
):
    project = get_project_fi()
    get_project_scheme_fi(project=project, is_labour_exchange=True)
    get_geo_point_fi(project=project, city=r_u.city)
    get_project_job_application_fi(project=project, user=r_u, status=status)
    response = __get_response(api_client, user=r_u)
    assert project.id in _response_instances_ids(response.data)


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
@pytest.mark.parametrize("status", NOT_ACTIVE_PROJECT_STATUS)
def test__not_active_project__not_display(
    api_client, r_u, get_project_fi, get_project_scheme_fi, get_geo_point_fi, status
):
    project = get_project_fi(status=status.value)
    get_project_scheme_fi(project=project, is_labour_exchange=True)
    get_geo_point_fi(project=project, city=r_u.city)
    response = __get_response(api_client, user=r_u)
    assert project.id not in _response_instances_ids(response.data)


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__specialisation_filtering(
    api_client, r_u, get_project_fi, get_project_scheme_fi, get_geo_point_fi, get_specialisation_fi
):
    project1 = get_project_fi()
    project2 = get_project_fi()
    project3 = get_project_fi()
    s1 = get_specialisation_fi(title=f"test_{get_random_string()}")
    s2 = get_specialisation_fi(title=f"test_{get_random_string()}")
    s3 = get_specialisation_fi(title=f"test_{get_random_string()}")
    get_project_scheme_fi(project=project1, is_labour_exchange=True, specialisation=s1)
    get_project_scheme_fi(project=project2, is_labour_exchange=True, specialisation=s2)
    get_project_scheme_fi(project=project3, is_labour_exchange=True, specialisation=s3)
    get_geo_point_fi(project=project1, city=get_random_string())
    get_geo_point_fi(project=project2, city=get_random_string())
    get_geo_point_fi(project=project3, city=get_random_string())

    response = __get_response(
        api_client, user=r_u, query_kwargs={"specialisation__title__in": f"{s1.title},{s2.title}"}
    )
    response_ids = _response_instances_ids(response.data)
    assert project1.id in response_ids
    assert project2.id in response_ids
    assert project3.id not in response_ids

    response = __get_response(api_client, user=r_u, query_kwargs={"specialisation__title": f"{s3.title}"})
    response_ids = _response_instances_ids(response.data)
    assert project1.id not in response_ids
    assert project2.id not in response_ids
    assert project3.id in response_ids


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__city_filtering(
    api_client, r_u, get_project_fi, get_project_scheme_fi, get_geo_point_fi, get_specialisation_fi
):
    "project__project_territories__geo_points__city"
    project1 = get_project_fi()
    project2 = get_project_fi()
    project3 = get_project_fi()
    s1 = get_specialisation_fi(title=f"test_{get_random_string()}")
    s2 = get_specialisation_fi(title=f"test_{get_random_string()}")
    s3 = get_specialisation_fi(title=f"test_{get_random_string()}")
    get_project_scheme_fi(project=project1, is_labour_exchange=True, specialisation=s1)
    get_project_scheme_fi(project=project2, is_labour_exchange=True, specialisation=s2)
    get_project_scheme_fi(project=project3, is_labour_exchange=True, specialisation=s3)
    gp1 = get_geo_point_fi(project=project1, city=get_random_string())
    gp2 = get_geo_point_fi(project=project2, city=get_random_string())
    gp3 = get_geo_point_fi(project=project3, city=get_random_string())

    query_kwargs = {"project__project_territories__geo_points__city__in": f"{gp1.city},{gp2.city}"}
    response = __get_response(api_client, user=r_u, query_kwargs=query_kwargs)
    response_ids = _response_instances_ids(response.data)
    assert project1.id in response_ids
    assert project2.id in response_ids
    assert project3.id not in response_ids

    query_kwargs = {"project__project_territories__geo_points__city": f"{gp3.city}"}
    response = __get_response(api_client, user=r_u, query_kwargs=query_kwargs)
    response_ids = _response_instances_ids(response.data)
    assert project1.id not in response_ids
    assert project2.id not in response_ids
    assert project3.id in response_ids


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__response_data(
    api_client,
    r_u,
    get_specialisation_fi,
    get_project_fi,
    get_project_scheme_fi,
    get_geo_point_fi,
    get_project_territory_fi,
):
    project1 = get_project_fi()
    s1 = get_specialisation_fi(title=f"test_{get_random_string()}")
    get_project_scheme_fi(project=project1, is_labour_exchange=True, specialisation=s1)

    reward1, reward2 = 100, 1000
    pt1 = get_project_territory_fi(project=project1, reward=reward1)
    pt2 = get_project_territory_fi(project=project1, reward=reward2)

    get_geo_point_fi(project_territory=pt1, city=r_u.city)
    get_geo_point_fi(project_territory=pt2, city=r_u.city)
    response = __get_response(api_client, user=r_u)

    response_instances = [ri for ri in response.data if ri.get("id") == project1.id]
    response_instance = response_instances[0]
    assert response_instance.pop("id") == project1.id
    if response_company := retrieve_response_instance(response_instance, "company", dict):
        assert response_company.pop("id") == project1.company.id
        assert response_company.pop("title") == project1.company.title
        assert response_company.pop("subdomain") == project1.company.subdomain
        assert response_company.pop("logo") == project1.company.logo
    assert not response_company
    # assert not response_project

    assert response_instance.pop("specialisations") == [{"id": s1.id, "title": s1.title}]
    assert response_instance.pop("project_territories_rewards") == [reward2, reward1]
    assert response_instance.pop("instruction") == {}
    assert response_instance.pop("title") == project1.title
    assert response_instance.pop("description") == project1.description
    assert response_instance.pop("is_adv_for_labour") is None
    assert response_instance.pop("adv_label") is None
    assert response_instance.pop("adv_url") is None
    assert not response_instance


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__response_data__instructions(
    api_client,
    r_u,
    get_specialisation_fi,
    get_project_scheme_fi,
    get_worker_instruction_fi,
    get_geo_point_fi,
    get_project_fi,
    get_project_territory_fi,
):

    project1 = get_project_fi()
    s1 = get_specialisation_fi(title=f"test_{get_random_string()}")
    get_project_scheme_fi(project=project1, is_labour_exchange=True, specialisation=s1)

    reward1, reward2 = 100, 1000
    pt1 = get_project_territory_fi(project=project1, reward=reward1)
    pt2 = get_project_territory_fi(project=project1, reward=reward2)

    get_geo_point_fi(project_territory=pt1, city=r_u.city)
    get_geo_point_fi(project_territory=pt2, city=r_u.city)

    instruction_data = [{"type": TITLE, "values": [get_random_string()]}]
    _project_instruction = get_worker_instruction_fi(project=project1, instructions_data=instruction_data)

    response = __get_response(api_client, user=r_u)
    response_instances = [ri for ri in response.data if ri.get("id") == project1.id]
    assert len(response_instances) == 1
    response_instance = response_instances[0]
    assert response_instance.pop("id") == project1.id
    assert response_instance["instruction"] == {"title": None, "data": instruction_data}
