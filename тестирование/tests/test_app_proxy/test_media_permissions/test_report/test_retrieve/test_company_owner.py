import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied

from proxy.permissions.media_permissions.worker_report import _retrieve_object_ids
from tests.test_app_proxy.test_media_permissions.test_report.test_retrieve.utils import __get_response

User = get_user_model()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("object_index", (0, 1, 2))
def test__accepted_owner__success(api_client, mock_policies_false, get_worker_report_fi, object_index, r_cu):
    worker_report = get_worker_report_fi(company=r_cu.company, is_create=False)
    object_id = list(_retrieve_object_ids(worker_report.json_fields))[object_index]
    assert __get_response(api_client, model_id=worker_report.id, object_id=object_id, user=r_cu.user)


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(("attribute", "value"), (("is_deleted", True), ("is_verified_email", False)))
def test__not_ta_requesting_company_owner__fail(
    api_client, mock_policies_false, get_worker_report_fi, r_cu, attribute: str, value: int
):
    worker_report = get_worker_report_fi(company=r_cu.company, is_create=False)
    setattr(r_cu.user, attribute, value)
    r_cu.user.save()
    object_id = list(_retrieve_object_ids(worker_report.json_fields))[0]
    response = __get_response(
        api_client,
        model_id=worker_report.id,
        object_id=object_id,
        user=r_cu.user,
        status_codes=PermissionDenied,
    )
    assert not response.data
