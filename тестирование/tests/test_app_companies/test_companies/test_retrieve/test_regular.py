import functools

import pytest
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework.exceptions import NotAuthenticated

from tests.utils import get_random_email, request_response_get
from ma_saas.settings import SERVER_ENVIRONMENT
from ma_saas.constants.company import CUR, CUS

User = get_user_model()


__get_response = functools.partial(request_response_get, path="/api/v1/companies/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("company_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


def test__response_data(mock_policies_false, api_client, get_company_fi, get_cu_fi):

    support_email = get_random_email()
    subdomain = get_random_string(length=5).lower()
    instance = get_company_fi(support_email=support_email, subdomain=subdomain)
    r_cu = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value, company=instance)

    response = __get_response(api_client, instance_id=r_cu.company.id, user=r_cu.user)
    response_instance = response.data
    assert response_instance.pop("id") == instance.id
    assert response_instance.pop("title") == instance.title
    assert str(response_instance.pop("logo")) == instance.logo
    assert response_instance.pop("support_email") == instance.support_email == support_email
    assert response_instance.pop("subdomain") == instance.subdomain == subdomain + f"-{SERVER_ENVIRONMENT}"
    assert response_instance.pop("transactions_list_scheme") == instance.transactions_list_scheme
    assert response_instance.pop("created_at")
    assert response_instance.pop("updated_at")
    assert not response_instance
