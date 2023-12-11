import functools

import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated

from tests.utils import request_response_update
from clients.policies.interface import Policies

User = get_user_model()


__get_response = functools.partial(
    request_response_update, path="/api/v1/contractor-project-territory-managers/"
)


@pytest.mark.parametrize("pt_manager", [pytest.lazy_fixture("contractor_pt_manager_fi")])
def test__anonymous_user__fail(api_client, pt_manager):
    response = __get_response(api_client, pt_manager.id, {}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__update__fail(api_client, monkeypatch, r_cu, get_contractor_pt_manager_fi):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    instance = get_contractor_pt_manager_fi(company=r_cu.company)
    response = __get_response(
        api_client, instance.id, {}, r_cu.user, status_codes=status_code.HTTP_405_METHOD_NOT_ALLOWED
    )
    assert response.data == {"detail": 'Method "PATCH" not allowed.'}
