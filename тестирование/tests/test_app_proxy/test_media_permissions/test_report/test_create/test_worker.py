import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, PermissionDenied

from ma_saas.constants.company import NOT_WORKER_ROLES, NOT_ACCEPT_CUS_VALUES
from ma_saas.constants.project import NOT_ACTIVE_PROJECT_STATUS_VALUES
from companies.models.company_user import CompanyUser
from proxy.permissions.media_permissions.worker_report import _retrieve_object_ids
from projects.models.contractor_project_territory_worker import ContractorProjectTerritoryWorker
from tests.test_app_proxy.test_media_permissions.test_report.test_create.utils import __get_response

User = get_user_model()


@pytest.mark.parametrize("object_index", (0, 1, 2))
@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__worker_model_owner__success(api_client, pt_worker, get_worker_report_fi, object_index):
    worker_report = get_worker_report_fi(project_territory_worker=pt_worker, is_create=False)
    object_id = list(_retrieve_object_ids(worker_report.json_fields))[object_index]

    response = __get_response(
        api_client, user=pt_worker.company_user.user, model_id=worker_report.id, object_id=object_id
    )
    assert not response.data


@pytest.mark.parametrize("cu_role", NOT_WORKER_ROLES)
@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__not_model_owner__fail(
    api_client,
    get_cu_fi,
    get_pt_worker_fi,
    get_worker_report_fi,
    cu_role,
    pt_worker,
):
    r_cu = get_cu_fi(company=pt_worker.company_user.company, role=cu_role)
    worker_report = get_worker_report_fi(project_territory=pt_worker.project_territory, is_create=False)
    response = __get_response(
        api_client,
        user=r_cu.user,
        model_id=worker_report.id,
        object_id=list(_retrieve_object_ids(worker_report.json_fields))[0],
        status_codes=PermissionDenied,
    )
    assert not response.data


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__not_active_company__fail(api_client, get_company_fi, pt_worker, get_worker_report_fi):
    r_cu, pt = pt_worker.company_user, pt_worker.project_territory
    worker_report = get_worker_report_fi(project_territory=pt, company_user=r_cu.id, is_create=False)

    r_cu.company.is_deleted = True
    r_cu.company.save()

    response = __get_response(
        api_client,
        user=r_cu.user,
        model_id=worker_report.id,
        object_id=list(_retrieve_object_ids(worker_report.json_fields))[0],
        status_codes=PermissionDenied,
    )
    assert not response.data


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__not_active_company__fail(api_client, pt_worker, get_worker_report_fi):
    company = pt_worker.project_territory.project.company
    worker_report = get_worker_report_fi(project_territory_worker=pt_worker, is_create=False)

    company.is_deleted = True
    company.save()
    response = __get_response(
        api_client,
        user=pt_worker.company_user.user,
        model_id=worker_report.id,
        object_id=list(_retrieve_object_ids(worker_report.json_fields))[0],
        status_codes=PermissionDenied,
    )
    assert not response.data


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
@pytest.mark.parametrize("cu_status", NOT_ACCEPT_CUS_VALUES)
def test__not_accept_worker__fail(api_client, monkeypatch, pt_worker, get_worker_report_fi, cu_status):
    monkeypatch.setattr(CompanyUser, "deactivate_policies", lambda *a, **kw: None)

    worker_report = get_worker_report_fi(project_territory_worker=pt_worker, is_create=False)

    pt_worker.company_user.status = cu_status
    pt_worker.company_user.save()

    response = __get_response(
        api_client,
        user=pt_worker.company_user.user,
        model_id=worker_report.id,
        object_id=list(_retrieve_object_ids(worker_report.json_fields))[0],
        status_codes=PermissionDenied,
    )
    assert not response.data


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__deleted_company_user__fail(api_client, monkeypatch, pt_worker, get_worker_report_fi):
    monkeypatch.setattr(CompanyUser, "deactivate_policies", lambda *a, **kw: None)
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    r_cu, pt = pt_worker.company_user, pt_worker.project_territory
    worker_report = get_worker_report_fi(project_territory_worker=pt_worker, is_create=False)

    r_cu.is_deleted = True
    r_cu.save()

    response = __get_response(
        api_client,
        user=r_cu.user,
        model_id=worker_report.id,
        object_id=list(_retrieve_object_ids(worker_report.json_fields))[0],
        status_codes=PermissionDenied,
    )
    assert not response.data


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__deleted_project_territory__fail(api_client, pt_worker, get_worker_report_fi):
    r_cu, pt = pt_worker.company_user, pt_worker.project_territory

    worker_report = get_worker_report_fi(project_territory_worker=pt_worker, is_create=False)

    pt.is_deleted = True
    pt.save()

    response = __get_response(
        api_client,
        user=r_cu.user,
        model_id=worker_report.id,
        object_id=list(_retrieve_object_ids(worker_report.json_fields))[0],
        status_codes=PermissionDenied,
    )
    assert not response.data


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__not_active_project_territory__fail(api_client, pt_worker, get_worker_report_fi):
    r_cu, pt = pt_worker.company_user, pt_worker.project_territory

    worker_report = get_worker_report_fi(project_territory_worker=pt_worker, is_create=False)

    pt_worker.project_territory.is_active = False
    pt_worker.project_territory.save()

    response = __get_response(
        api_client,
        user=r_cu.user,
        model_id=worker_report.id,
        object_id=list(_retrieve_object_ids(worker_report.json_fields))[0],
        status_codes=PermissionDenied,
    )
    assert not response.data


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__deleted_project__fail(api_client, pt_worker, get_worker_report_fi):
    r_cu, pt = pt_worker.company_user, pt_worker.project_territory

    worker_report = get_worker_report_fi(project_territory_worker=pt_worker, is_create=False)

    pt_worker.project_territory.is_deleted = True
    pt_worker.project_territory.save()

    response = __get_response(
        api_client,
        user=r_cu.user,
        model_id=worker_report.id,
        object_id=list(_retrieve_object_ids(worker_report.json_fields))[0],
        status_codes=PermissionDenied,
    )
    assert not response.data


@pytest.mark.parametrize("project_status", NOT_ACTIVE_PROJECT_STATUS_VALUES)
@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__not_active_project__fail(api_client, get_worker_report_fi, project_status, pt_worker):
    r_cu, pt = pt_worker.company_user, pt_worker.project_territory

    worker_report = get_worker_report_fi(project_territory_worker=pt_worker, is_create=False)

    pt.project.status = project_status
    pt.project.save()

    response = __get_response(
        api_client,
        user=r_cu.user,
        model_id=worker_report.id,
        object_id=list(_retrieve_object_ids(worker_report.json_fields))[0],
        status_codes=PermissionDenied,
    )
    assert not response.data


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__deleted_territory__fail(
    api_client, pt_worker: ContractorProjectTerritoryWorker, get_worker_report_fi
):
    r_cu, pt = pt_worker.company_user, pt_worker.project_territory

    worker_report = get_worker_report_fi(project_territory_worker=pt_worker, is_create=False)

    pt.territory.is_deleted = True
    pt.territory.save()

    response = __get_response(
        api_client,
        user=r_cu.user,
        model_id=worker_report.id,
        object_id=list(_retrieve_object_ids(worker_report.json_fields))[0],
        status_codes=PermissionDenied,
    )
    assert not response.data


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__not_existing__fail(api_client, pt_worker, get_worker_report_fi):
    r_cu, pt = pt_worker.company_user, pt_worker.project_territory

    worker_report = get_worker_report_fi(project_territory_worker=pt_worker, is_create=False)
    response = __get_response(
        api_client,
        user=r_cu.user,
        model_id=worker_report.id + 1,
        object_id=list(_retrieve_object_ids(worker_report.json_fields))[0],
        status_codes=NotFound,
    )
    assert response.data == {"detail": "WorkerReport not found"}


@pytest.mark.parametrize(("attribute", "value"), (("is_deleted", True), ("is_verified_phone", False)))
@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
def test__ta_requesting_worker_model_owner__fail(
    api_client,
    get_worker_report_fi,
    attribute,
    value,
    pt_worker,
):
    r_cu = pt_worker.company_user

    worker_report = get_worker_report_fi(project_territory_worker=pt_worker, is_create=False)
    setattr(r_cu.user, attribute, value)
    r_cu.user.save()
    response = __get_response(
        api_client,
        user=r_cu.user,
        model_id=worker_report.id,
        object_id=list(_retrieve_object_ids(worker_report.json_fields))[0],
        status_codes=PermissionDenied,
    )
    assert not response.data
