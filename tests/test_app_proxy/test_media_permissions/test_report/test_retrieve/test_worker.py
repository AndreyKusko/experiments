import pytest
from django.contrib.auth import get_user_model

from ma_saas.constants.company import CUR, CUS
from proxy.permissions.media_permissions.worker_report import _retrieve_object_ids
from tests.test_app_proxy.test_media_permissions.test_report.test_retrieve.utils import __get_response

User = get_user_model()


@pytest.mark.parametrize("object_index", (0, 1, 2))
@pytest.mark.parametrize("status", CUS)
def test__worker_model_owner__success(
    api_client, mock_policies_false, get_cu_fi, get_worker_report_fi, object_index, status
):
    r_cu = get_cu_fi(role=CUR.WORKER, status=status)
    worker_report = get_worker_report_fi(company_user=r_cu, is_create=False)
    object_id = list(_retrieve_object_ids(worker_report.json_fields))[object_index]

    assert __get_response(api_client, user=r_cu.user, model_id=worker_report.id, object_id=object_id)


@pytest.mark.parametrize(("attribute", "value"), (("is_deleted", True), ("is_verified_phone", False)))
@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__not_ta_requesting_worker_model_owner__success(
    api_client, monkeypatch, get_worker_report_fi, attribute: str, value: int, pt_worker
):
    r_cu, pt = pt_worker.company_user, pt_worker.project_territory
    worker_report = get_worker_report_fi(
        project_territory_worker=pt_worker, company_user=r_cu.id, is_create=False
    )
    setattr(r_cu.user, attribute, value)
    r_cu.user.save()
    object_id = list(_retrieve_object_ids(worker_report.json_fields))[0]

    response = __get_response(api_client, user=r_cu.user, model_id=worker_report.id, object_id=object_id)
    assert not response.data
