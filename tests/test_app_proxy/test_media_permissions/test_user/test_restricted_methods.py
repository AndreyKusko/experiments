import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model

from tests.utils import get_authorization_token
from ma_saas.constants.system import TYPE, VALUES, BASENAME
from ma_saas.constants.constant import PHOTO
from proxy.views.media_permission import USER, WORKER_INSTRUCTION
from companies.models.company_user import CompanyUser
from ma_saas.constants.worker_instruction import WorkerInstructionMediaType

User = get_user_model()

link = f"/api/v1/media-permissions/{USER}"


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__post__fail(api_client, r_u):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_u))
    response = api_client.post(f"{link}/")
    assert response.status_code == status_code.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__patch__fail(api_client, r_u):
    object_id = "e0kj309230e0203"
    media_field = {TYPE: PHOTO, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    r_u.avatar = media_field
    r_u.save()

    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_u))
    response = api_client.patch(f"{link}/{r_u.id}/{object_id}/", data={})
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__put__fail(api_client, r_u):
    object_id = "e0kj309230e0203"
    media_field = {TYPE: PHOTO, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    r_u.avatar = media_field
    r_u.save()

    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_u))
    response = api_client.put(f"{link}/{r_u.id}/{object_id}/", data={})
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__put__fail(api_client, r_u):
    object_id = "e0kj309230e0203"
    media_field = {TYPE: PHOTO, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    r_u.avatar = media_field
    r_u.save()

    response = api_client.put(f"{link}/{r_u.id}/{object_id}/", data={})
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__delete__fail(api_client, r_u):
    object_id = "e0kj309230e0203"
    media_field = {TYPE: PHOTO, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    r_u.avatar = media_field
    r_u.save()

    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_u))
    response = api_client.delete(f"{link}/{r_u.id}/{object_id}/")
    status_codes = status_code.HTTP_405_METHOD_NOT_ALLOWED
    assert response.status_code == status_codes


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__list__method__fail(api_client, r_u):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_u))
    response = api_client.get(f"{link}")
    assert response.status_code == status_code.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__list__with_model__method__fail(api_client, r_u):
    object_id = "e0kj309230e0203"
    media_field = {TYPE: PHOTO, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    r_u.avatar = media_field
    r_u.save()

    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_u))
    response = api_client.get(f"{link}/{r_u.id}/")
    assert response.status_code == status_code.HTTP_404_NOT_FOUND
