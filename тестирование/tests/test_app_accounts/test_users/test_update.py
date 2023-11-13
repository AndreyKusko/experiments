import json
import functools

import pytest
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework.exceptions import NotFound, ValidationError, NotAuthenticated

from tests.utils import get_random_email, get_random_phone, request_response_update
from ma_saas.constants.system import VALUES, BASENAME, FILE_LINK, Callable
from clients.objects_store.views import get_media_link
from proxy.views.media_permission import USER
from companies.serializers.company import (
    BASENAME_VALUE_REQ,
    VALUES_QTY_MUST_BE_1,
    BASENAME_AND_VALUES_REQ,
    VALUES_VALUE_MUST_BE_LIST,
    BASENAME_VALUE_MUST_BE_STRING,
    VALUES_LIST_VALUE_MUST_BE_STRING,
)

User = get_user_model()


__get_response = functools.partial(request_response_update, path="/api/v1/users/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("user_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, {}, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


def test__random_user__fail(api_client, get_user_fi, new_user_data: Callable):
    r_u = get_user_fi()
    target_user = get_user_fi()
    data = new_user_data()
    response = __get_response(api_client, target_user.id, data, user=r_u, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


def test__user_self_update_phone__fail(api_client, get_user_fi, new_user_data: Callable):
    old_phone = get_random_phone()
    r_u = get_user_fi(phone=old_phone)
    assert r_u.is_verified_phone

    new_phone = get_random_phone()
    response = __get_response(api_client, instance_id=r_u.id, data={"phone": new_phone}, user=r_u)
    updated_user = User.objects.get(id=r_u.id)
    assert updated_user.phone == response.data["phone"] == f"7{old_phone}" != f"7{new_phone}"
    assert updated_user.is_verified_phone


def test__user_self_update_email__success(api_client, get_user_fi, user_fi: User, new_user_data: Callable):
    old_email = get_random_email()
    r_u = get_user_fi(email=old_email)
    assert r_u.is_verified_email

    new_email = get_random_email()
    response = __get_response(api_client, r_u.id, {"email": new_email}, user=r_u)
    updated_user = User.objects.get(id=r_u.id)
    assert updated_user.email == response.data["email"] == old_email != new_email
    assert updated_user.is_verified_email
