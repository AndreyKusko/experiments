import typing as tp

import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotAuthenticated

from tests.utils import _process_status_codes, get_authorization_token
from ma_saas.constants.system import TYPE, VALUES, BASENAME
from ma_saas.constants.constant import PHOTO
from proxy.views.media_permission import USER

User = get_user_model()


def __get_response(
    api_client, model_id: int, object_id: str, status_codes=None, user: tp.Optional[User] = None
) -> Response:
    """Return response."""
    if user:
        api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user))
    response = api_client.post(f"/api/v1/media-permissions/{USER}/{model_id}/{object_id}/")

    expecting_status_codes = _process_status_codes(status_codes, default={status_code.HTTP_200_OK})
    response_status_code = response.status_code
    is_correct_response_status_code = response_status_code in expecting_status_codes
    assert (
        is_correct_response_status_code
    ), f"response_status_code {response_status_code} not in {expecting_status_codes} | response.data = {response.data}"

    return response


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_u):
    parent_instance = r_u
    object_id = "e0kj309230e0203"
    media_field = {TYPE: PHOTO, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    parent_instance.avatar = media_field
    parent_instance.save()
    response = __get_response(api_client, user=r_u, model_id=parent_instance.id, object_id=object_id)
    assert not response.data


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__familiar__fail(monkeypatch, api_client, r_u, get_user_fi):
    user = get_user_fi()
    parent_instance = user

    object_id = "e0kj309230e0203"
    media_field = {TYPE: PHOTO, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    parent_instance.avatar = media_field
    parent_instance.save()

    response = __get_response(
        api_client, user=r_u, model_id=user.id, object_id=object_id, status_codes=ValidationError
    )
    assert response.data == ["Target user must be requesting user"]


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__401__fail(monkeypatch, api_client, r_u):
    parent_instance = r_u
    object_id = "e0kj309230e0203"
    media_field = {TYPE: PHOTO, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    parent_instance.avatar = media_field
    parent_instance.save()

    response = __get_response(
        api_client, model_id=parent_instance.id, object_id=object_id, status_codes=NotAuthenticated
    )
    assert response.data == {"detail": NotAuthenticated.default_detail}
