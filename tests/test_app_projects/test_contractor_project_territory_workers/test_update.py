import functools

import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated

from tests.utils import request_response_update
from companies.models.company_user import CompanyUser

User = get_user_model()


__get_response = functools.partial(
    request_response_update, path="/api/v1/contractor-project-territory-workers/"
)


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, {}, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__update__fail(api_client, r_cu: CompanyUser, get_pt_worker_fi):
    instance = get_pt_worker_fi(company=r_cu.company)
    response = __get_response(
        api_client,
        instance_id=instance.id,
        data={},
        user=r_cu.user,
        status_codes=status_code.HTTP_405_METHOD_NOT_ALLOWED,
    )
    assert response.data["detail"] == 'Method "PATCH" not allowed.'
