import typing as tp

import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.response import Response

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
    response = api_client.get(f"/api/v1/media-permissions/{USER}/{model_id}/{object_id}/")

    expecting_status_codes = _process_status_codes(status_codes, default={status_code.HTTP_200_OK})
    response_status_code = response.status_code
    is_correct_response_status_code = response_status_code in expecting_status_codes
    assert (
        is_correct_response_status_code
    ), f"response_status_code {response_status_code} not in {expecting_status_codes} | response.data = {response.data}"
    return response


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__accepted_owner__success(api_client, mock_policies_false, r_u):
    object_id = "e0kj309230e0203"
    media_field = {TYPE: PHOTO, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    r_u.avatar = media_field
    r_u.save()
    response = __get_response(api_client, user=r_u, model_id=r_u.id, object_id=object_id)
    assert not response.data


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__familiar__success(monkeypatch, api_client, r_u, get_user_fi):
    user = get_user_fi()
    object_id = "e0kj309230e0203"
    media_field = {TYPE: PHOTO, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    user.avatar = media_field
    user.save()
    response = __get_response(api_client, user=r_u, model_id=user.id, object_id=object_id)
    assert not response.data


@pytest.mark.parametrize("user", [pytest.lazy_fixture("user_fi")])
def test__401__fail(monkeypatch, api_client, user):
    object_id = "e0kj309230e0203"
    media_field = {TYPE: PHOTO, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    user.avatar = media_field
    user.save()
    response = __get_response(api_client, model_id=user.id, object_id=object_id)
    assert not response.data
