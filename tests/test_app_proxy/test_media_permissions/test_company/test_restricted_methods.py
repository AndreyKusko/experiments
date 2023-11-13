import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model

from tests.utils import get_authorization_token
from ma_saas.constants.system import TYPE, VALUES, BASENAME
from ma_saas.constants.constant import PHOTO
from proxy.views.media_permission import COMPANY
from companies.models.company_user import CompanyUser

User = get_user_model()


link = f"/api/v1/media-permissions/{COMPANY}"


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__post__fail(api_client, r_cu):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.post(f"{link}/")
    assert response.status_code == status_code.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__patch__fail(api_client, r_cu):
    object_id = "e0kj309230e0203"
    media_field = {TYPE: PHOTO, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    parent_instance = r_cu.company
    parent_instance.logo = media_field
    parent_instance.save()

    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.patch(f"{link}/{parent_instance.id}/{object_id}/", data={})
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__put__fail(api_client, r_cu):
    object_id = "e0kj309230e0203"
    media_field = {TYPE: PHOTO, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    parent_instance = r_cu.company
    parent_instance.logo = media_field
    parent_instance.save()

    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.put(f"{link}/{parent_instance.id}/{object_id}/", data={})
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__put__fail(api_client, r_cu):
    object_id = "e0kj309230e0203"
    media_field = {TYPE: PHOTO, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    parent_instance = r_cu.company
    parent_instance.logo = media_field
    parent_instance.save()

    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.put(f"{link}/{parent_instance.id}/{object_id}/", data={})
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__delete__fail(api_client, r_cu):
    object_id = "e0kj309230e0203"
    media_field = {TYPE: PHOTO, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    parent_instance = r_cu.company
    parent_instance.logo = media_field
    parent_instance.save()

    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.delete(f"{link}/{parent_instance.id}/{object_id}/")
    status_codes = status_code.HTTP_405_METHOD_NOT_ALLOWED
    assert response.status_code == status_codes


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__list__method__fail(api_client, r_cu):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.get(f"{link}")
    assert response.status_code == status_code.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__list__with_model__method__fail(api_client, r_cu):
    object_id = "e0kj309230e0203"
    media_field = {TYPE: PHOTO, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    parent_instance = r_cu.company
    parent_instance.logo = media_field
    parent_instance.save()

    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.get(f"{link}/{parent_instance.id}/")
    assert response.status_code == status_code.HTTP_404_NOT_FOUND
