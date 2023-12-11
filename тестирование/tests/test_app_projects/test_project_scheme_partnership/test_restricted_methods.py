from http.client import responses

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import MethodNotAllowed

from tests.utils import get_authorization_token
from ma_saas.constants.company import CUR, CUS

User = get_user_model()


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("project_scheme_partnership_fi")])
def test__method_retrieve__fail(api_client, mock_policies_false, get_cu_fi, instance):
    inviting_company = instance.project_partnership.company_partnership.inviting_company
    r_cu = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value, company=inviting_company)
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.get(f"/api/v1/project-scheme-partnership/{instance.id}/")
    assert response.status_code == MethodNotAllowed.status_code
    assert response.status_text == responses[MethodNotAllowed.status_code]
    assert response.data["detail"] == MethodNotAllowed.default_detail.format(method="GET")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("project_scheme_partnership_fi")])
def test__method_update__fail(api_client, mock_policies_false, get_cu_fi, instance):
    inviting_company = instance.project_partnership.company_partnership.inviting_company
    r_cu = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value, company=inviting_company)
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.patch(f"/api/v1/project-scheme-partnership/{instance.id}/", data={})
    assert response.status_code == MethodNotAllowed.status_code
    assert response.status_text == responses[MethodNotAllowed.status_code]
    assert response.data["detail"] == MethodNotAllowed.default_detail.format(method="PATCH")
