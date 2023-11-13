from http.client import responses

from rest_framework import status as status_code
from django.contrib.auth import get_user_model

from tests.utils import get_authorization_token
from tests.test_app_reports.test_processed_reports.constants import PROCESSED_REPORTS_PATH

User = get_user_model()


def test__method__fail(api_client, processed_report_fi, get_cu_fi):
    r_cu = get_cu_fi(company=processed_report_fi.company_user.company)
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.delete(f"{PROCESSED_REPORTS_PATH}{processed_report_fi.id}/")
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED
    assert response.status_text == responses[status_code.HTTP_405_METHOD_NOT_ALLOWED]
