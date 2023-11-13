import functools

from django.forms import model_to_dict
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated

from tests.utils import request_response_list

User = get_user_model()


__get_response = functools.partial(request_response_list, path="/api/v1/users/")


def test__anonymous(api_client):
    response = __get_response(api_client, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


def test__response(api_client, user_fi):
    response = __get_response(api_client, user=user_fi)
    instance_dict = model_to_dict(user_fi)
    assert len(response.data) == 1
    response_instance = response.data[0]
    assert response_instance.pop("avatar") == "{}"
    for key, value in response_instance.items():
        assert instance_dict[key] == value
