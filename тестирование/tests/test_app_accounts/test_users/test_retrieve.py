import functools

from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated, PermissionDenied

from tests.utils import request_response_get
from accounts.permissions import USER_MUST_BE_MODEL_OWNER
from accounts.serializers.user import UserSerializer

User = get_user_model()

__get_response = functools.partial(request_response_get, path="/api/v1/users/")


def test__anonymous(api_client, user_fi):
    response = __get_response(api_client, user_fi.id, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


def test__random_user__fail(api_client, get_user_fi):
    requesting_user = get_user_fi()
    target_user = get_user_fi()
    response = __get_response(api_client, target_user.id, requesting_user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


def test__model_owner__success(api_client, user_fi):
    response = __get_response(api_client, user_fi.id, user_fi)
    expected_data = UserSerializer(instance=user_fi).data
    assert all(response.data[key] == value for key, value in expected_data.items())


def test__superuser__fail(api_client, user_fi: User, super_user_fi: User):
    response = __get_response(api_client, user_fi.id, super_user_fi, status_codes=PermissionDenied)
    assert response.data == {"detail": USER_MUST_BE_MODEL_OWNER}
