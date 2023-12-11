import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied

from clients.policies.interface import Policies
from proxy.permissions.media_permissions.worker_report import _retrieve_object_ids
from tests.test_app_proxy.test_media_permissions.test_report.test_create.utils import __get_response

User = get_user_model()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
@pytest.mark.parametrize("has_object_policy", [True, False])
def test__manager__any_policy__fail(api_client, monkeypatch, r_cu, get_worker_report_fi, has_object_policy):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)

    worker_report = get_worker_report_fi(company=r_cu.company, is_create=False)
    object_id = list(_retrieve_object_ids(worker_report.json_fields))[0]
    response = __get_response(
        api_client,
        user=r_cu.user,
        model_id=worker_report.id,
        object_id=object_id,
        status_codes=PermissionDenied,
    )
    assert not response.data


@pytest.mark.parametrize(("attribute", "value"), (("is_deleted", True), ("is_verified_email", False)))
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
@pytest.mark.parametrize("has_object_policy", [True, False])
def test__not_ta_requesting__manager__fail(
    api_client, monkeypatch, get_worker_report_fi, r_cu, attribute, has_object_policy, value
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)

    worker_report = get_worker_report_fi(company=r_cu.company, is_create=False)
    object_id = list(_retrieve_object_ids(worker_report.json_fields))[0]
    setattr(r_cu.user, attribute, value)
    r_cu.user.save()
    response = __get_response(
        api_client,
        user=r_cu.user,
        model_id=worker_report.id,
        object_id=object_id,
        status_codes=PermissionDenied,
    )
    assert not response.data
