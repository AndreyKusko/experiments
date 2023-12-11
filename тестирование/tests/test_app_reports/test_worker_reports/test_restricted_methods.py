import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model

from tests.utils import get_authorization_token

User = get_user_model()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__method__fail(api_client, get_worker_report_fi, r_cu):

    instance = get_worker_report_fi(company=r_cu.company)
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))

    response = api_client.delete(f"/api/v1/worker-reports/{instance.id}/")

    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED
