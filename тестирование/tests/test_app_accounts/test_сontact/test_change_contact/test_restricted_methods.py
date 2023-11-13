import pytest
from rest_framework.exceptions import NotFound, MethodNotAllowed

from tests.utils import _aut_user

LINK = "/api/v1/change-contact/"


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__list__fail(api_client, r_u):
    _aut_user(api_client, r_u)
    response = api_client.delete(f"{LINK}{1}")
    # assert response.status_code == MethodNotAllowed.status_code
    assert response.status_code == NotFound.status_code


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__list__fail(api_client, r_u):
    _aut_user(api_client, r_u)
    response = api_client.get(f"{LINK}{1}")
    # assert response.status_code == MethodNotAllowed.status_code
    assert response.status_code == NotFound.status_code


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
def test__list__fail(api_client, r_u):
    _aut_user(api_client, r_u)
    response = api_client.get(f"{LINK}")
    assert response.status_code == MethodNotAllowed.status_code
