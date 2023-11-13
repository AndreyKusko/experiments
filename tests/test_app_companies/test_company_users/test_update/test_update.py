import pytest
from rest_framework.exceptions import NotAuthenticated

from tests.test_app_companies.test_company_users.test_update.test_model_owner_update import __get_response


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("cu_owner_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, {}, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail
