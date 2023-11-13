import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model

from tests.utils import get_authorization_token
from ma_saas.constants.system import TYPE, VALUES, BASENAME
from ma_saas.constants.constant import PHOTO
from proxy.views.media_permission import PROJECT_QUESTIONNAIRE

User = get_user_model()


link = f"/api/v1/media-permissions/{PROJECT_QUESTIONNAIRE}"


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__post__fail(api_client, r_u):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_u))
    response = api_client.post(f"{link}/")
    assert response.status_code == status_code.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__patch__fail(api_client, r_u, get_project_questionnaire_fi):
    object_id = "e0kj309230e0203"
    media_field = {TYPE: PHOTO, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    parent_instance = get_project_questionnaire_fi(user=r_u)
    parent_instance.media_json = [media_field]
    parent_instance.save()

    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_u))
    response = api_client.patch(f"{link}/{parent_instance.id}/{object_id}/", data={})
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__put__fail(api_client, r_u, get_project_questionnaire_fi):
    object_id = "e0kj309230e0203"
    media_field = {TYPE: PHOTO, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    parent_instance = get_project_questionnaire_fi(user=r_u)
    parent_instance.media_json = [media_field]
    parent_instance.save()

    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_u))
    response = api_client.put(f"{link}/{parent_instance.id}/{object_id}/", data={})
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__put__fail(api_client, r_u, get_project_questionnaire_fi):
    object_id = "e0kj309230e0203"
    media_field = {TYPE: PHOTO, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    parent_instance = get_project_questionnaire_fi(user=r_u)
    parent_instance.media_json = [media_field]
    parent_instance.save()

    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_u))
    response = api_client.put(f"{link}/{parent_instance.id}/{object_id}/", data={})
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__delete__fail(api_client, r_u, get_project_questionnaire_fi):
    object_id = "e0kj309230e0203"
    media_field = {TYPE: PHOTO, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    parent_instance = get_project_questionnaire_fi(user=r_u)
    parent_instance.media_json = [media_field]
    parent_instance.save()

    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_u))
    response = api_client.delete(f"{link}/{parent_instance.id}/{object_id}/")
    status_codes = status_code.HTTP_405_METHOD_NOT_ALLOWED
    assert response.status_code == status_codes


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__list__method__fail(api_client, r_u):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_u))
    response = api_client.get(f"{link}")
    assert response.status_code == status_code.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__list__with_model__method__fail(api_client, r_u, get_project_questionnaire_fi):
    object_id = "e0kj309230e0203"
    media_field = {TYPE: PHOTO, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    parent_instance = get_project_questionnaire_fi(user=r_u)
    parent_instance.media_json = [media_field]
    parent_instance.save()

    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_u))
    response = api_client.get(f"{link}/{parent_instance.id}/")
    assert response.status_code == status_code.HTTP_404_NOT_FOUND
