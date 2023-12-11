import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied

from clients.policies.interface import Policies
from proxy.permissions.media_permissions.worker_report import _retrieve_object_ids
from tests.test_app_proxy.test_media_permissions.test_report.test_retrieve.utils import __get_response

User = get_user_model()


@pytest.mark.parametrize("object_index", (0, 1, 2))
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__contractor__manager__with_policy__success(
    api_client, monkeypatch, get_worker_report_fi, object_index: int, r_cu, get_project_territory_fi
):
    pt = get_project_territory_fi(company=r_cu.company)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    worker_report = get_worker_report_fi(project_territory=pt, is_create=False)
    object_id = list(_retrieve_object_ids(worker_report.json_fields))[object_index]
    response = __get_response(api_client, user=r_cu.user, model_id=worker_report.id, object_id=object_id)
    assert not response.data


@pytest.mark.parametrize("object_index", (0, 1, 2))
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__contractor__manager__without_policy__fail(
    api_client,
    mock_policies_false,
    get_worker_report_fi,
    r_cu,
    get_project_territory_fi,
    object_index: int,
):
    pt = get_project_territory_fi(company=r_cu.company)
    worker_report = get_worker_report_fi(project_territory=pt, is_create=False)
    object_id = list(_retrieve_object_ids(worker_report.json_fields))[object_index]
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
def test__not_ta_requesting__manager__fail(
    api_client,
    monkeypatch,
    get_worker_report_fi,
    r_cu,
    attribute: str,
    value: int,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
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
