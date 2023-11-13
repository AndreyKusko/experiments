import functools

import pytest
from django.forms import model_to_dict
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated, PermissionDenied

from tests.utils import request_response_get, retrieve_response_instance
from pg_logger.models import PgLog
from ma_saas.constants.report import (
    NOT_ACCEPTED_PROCESSED_REPORT_STATUSES_VALUES,
    ProcessedReportStatus,
    ProcessedReportFormFieldSpecTypes,
)
from ma_saas.constants.system import Callable, PgLogLVL
from ma_saas.constants.company import CUR, NOT_ACCEPT_CUS, NOT_WORKER_ROLES, CompanyUserStatus
from companies.models.company_user import CUS_MUST_BE_ACCEPT, NOT_TA_COMPANY_USER_REASON, CompanyUser
from reports.models.processed_report import ProcessedReport
from tests.fixtures.processed_report_form import ALL_FIELDS_SPECS_LIST
from tests.test_app_reports.test_processed_reports.constants import PROCESSED_REPORTS_PATH

User = get_user_model()


__get_response = functools.partial(request_response_get, path=PROCESSED_REPORTS_PATH)


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("processed_report_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data(
    api_client,
    r_cu: CompanyUser,
    get_processed_report_fi,
    get_processed_report_form_fi: Callable,
    generate_processed_report_field_fi,
):

    clean_fields = dict()
    existed_unique_fields = set()
    for index, field in enumerate(ALL_FIELDS_SPECS_LIST):
        if field["type"] in ProcessedReportFormFieldSpecTypes.unique_by_type:
            if field["type"] in existed_unique_fields:
                continue
            else:
                existed_unique_fields.add(field["type"])
        clean_fields[index] = field
    processed_report_form = get_processed_report_form_fi(company=r_cu.company, fields_specs=clean_fields)
    json_fields = dict()
    for field_id, field_spec in clean_fields.items():
        json_fields[f"{field_id}"] = {"values": generate_processed_report_field_fi(field_spec=field_spec)}

    instance = get_processed_report_fi(
        processed_report_form=processed_report_form,
        json_fields=json_fields,
    )
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    instance_dict = model_to_dict(instance)
    instance_dict["accepted_at"] = instance.accepted_at.isoformat() + "Z" if instance.accepted_at else None
    response_instance = response.data
    assert response_instance

    assert response_instance["id"]

    if response_project_scheme := retrieve_response_instance(response_instance, "project_scheme", dict):
        assert response_project_scheme.pop("id") == instance.processed_report_form.project_scheme.id
        assert response_project_scheme.pop("title") == instance.processed_report_form.project_scheme.title
    assert not response_project_scheme

    if response_processed_report_form := retrieve_response_instance(
        response_instance, "processed_report_form", dict
    ):
        assert response_processed_report_form.pop("id") == processed_report_form.id
        assert response_processed_report_form.pop("fields_specs") == processed_report_form.fields_specs
    assert not response_processed_report_form

    assert response_instance["worker_report"] == instance.worker_report.id

    if response_company_user := retrieve_response_instance(response_instance, "company_user", dict):
        assert response_company_user.pop("id") == instance.company_user.id
        assert response_company_user.pop("first_name") == instance.company_user.user.first_name
        assert response_company_user.pop("last_name") == instance.company_user.user.last_name
        assert response_company_user.pop("email") == instance.company_user.user.email
    assert not response_company_user

    assert response_instance["status"] == ProcessedReportStatus.CREATED.value

    assert response_instance["json_fields"] == instance.json_fields

    assert response_instance["created_at"]
    assert response_instance["updated_at"]
    assert not response_instance["accepted_at"]
    assert response_instance["updated_by"] == {"user": {}, "company_user": {}}
    assert response_instance["comment"] == instance.comment
    assert not response_instance


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("status", ProcessedReportStatus.values)
def test__contractor_owner_any_report_status__success(
    api_client,
    r_cu,
    get_project_territory_fi,
    get_processed_report_fi,
    status,
):
    pt = get_project_territory_fi(company=r_cu.company)
    instance = get_processed_report_fi(pt=pt, status=status)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__client_owner_accepted_report__success(api_client, r_cu, get_processed_report_fi):
    instance = get_processed_report_fi(status=ProcessedReportStatus.ACCEPTED.value)
    instance.processed_report_form.project_scheme.project.invited_company = r_cu.company
    instance.processed_report_form.project_scheme.project.save()
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    assert response.data["id"] == instance.id


#
#
# @pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
# @pytest.mark.parametrize("invited_company_status", NOT_ACCEPT_COMPANY_PARTNERSHIP_STATUS)
# def test__client_owner__project_not_accept_partner_status__fail(
#     api_client, r_cu, get_processed_report_fi, status,
# ):
#     instance = get_processed_report_fi(status=ProcessedReportStatus.ACCEPTED.value)
#     instance.processed_report_form.project_scheme.project.invited_company = r_cu.company
#     instance.processed_report_form.project_scheme.project.invited_company_status = status
#     instance.processed_report_form.project_scheme.project.save()
#     response = __get_response(
#         api_client, instance_id=instance.id, user=r_cu.user, status_codes=NotFound,
#     )
#     assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("status", NOT_ACCEPTED_PROCESSED_REPORT_STATUSES_VALUES)
def test__client_owner_not_accepted_report__fail(
    api_client, r_cu: CompanyUser, get_processed_report_fi, status
):
    instance = get_processed_report_fi(status=status)
    instance.processed_report_form.project_scheme.invited_company = r_cu.company
    instance.processed_report_form.project_scheme.save()
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__contractor_not_accepted_cu_owner__fail(
    api_client,
    get_cu_fi,
    get_project_territory_fi,
    get_processed_report_fi,
    status,
):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status)
    project_territory = get_project_territory_fi(company=r_cu.company)
    instance = get_processed_report_fi(project_territory=project_territory)
    response = __get_response(api_client, instance.id, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__client_not_accepted_cu_owner__fail(
    api_client,
    get_cu_fi,
    get_processed_report_fi,
    status,
):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status)
    instance = get_processed_report_fi()
    instance.processed_report_form.project_scheme.invited_company = r_cu.company
    instance.processed_report_form.project_scheme.save()
    response = __get_response(api_client, instance.id, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("status", ProcessedReportStatus.values)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__related_manager_model_owner__any_report_status__success(
    api_client, r_cu, get_processed_report_fi, status
):
    instance = get_processed_report_fi(company_user=r_cu, status=status)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("status", ProcessedReportStatus.values)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__another_manager__any_report_status__success(api_client, r_cu, get_processed_report_fi, status):
    instance = get_processed_report_fi(company=r_cu.company, status=status)
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("pt_worker_fi")])
def test__contractor_worker__fail(api_client, pt_worker, get_processed_report_fi):
    r_cu = pt_worker.company_user.user
    instance = get_processed_report_fi(project_territory=pt_worker.project_territory)
    response = __get_response(api_client, instance.id, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("invited_company_status", NOT_ACCEPT_PROJECT_partner_status_VALUES)
def test__client_project_manager__project_not_accept_partner_status__fail(
    api_client,
    get_client_project_manager_fi: Callable,
    get_project_territory_fi: Callable,
    get_processed_report_fi,
    get_company_fi,
    partner_status,
):
    requesting_project_manager = get_client_project_manager_fi()
    company = get_company_fi(kind=CompanyKind.CONTRACTOR.value)
    requesting_project_manager.project.company = company
    requesting_project_manager.project.invited_company_status = partner_status
    requesting_project_manager.project.save()
    pt = get_project_territory_fi(project=requesting_project_manager.project)
    instance = get_processed_report_fi(project_territory=pt, status=ProcessedReportStatus.ACCEPTED.value)
    response = __get_response(
        api_client,
        instance_id=instance.id,
        user=requesting_project_manager.company_user.user,
        status_codes=NotFound,
    )
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("status", NOT_ACCEPTED_PROCESSED_REPORT_STATUSES_VALUES)
def test__client_project_manager__not_accepted_report_status__fail(
    api_client,
    get_client_project_manager_fi: Callable,
    get_project_territory_fi: Callable,
    get_processed_report_fi,
    get_company_fi,
    status,
):
    requesting_project_manager = get_client_project_manager_fi()
    company = get_company_fi(kind=CompanyKind.CONTRACTOR.value)
    requesting_project_manager.project.company = company
    requesting_project_manager.project.save()
    pt = get_project_territory_fi(project=requesting_project_manager.project)
    instance = get_processed_report_fi(project_territory=pt, status=status)

    response = __get_response(
        api_client,
        instance_id=instance.id,
        user=requesting_project_manager.company_user.user,
        status_codes=NotFound,
    )
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__contractor_related_manager_model_owner__not_accepted_cu__fail(
    api_client, r_cu, get_processed_report_fi, get_project_territory_fi, status
):
    pt = get_project_territory_fi(company=r_cu.company)
    instance = get_processed_report_fi(
        company_user=r_cu,
        project_territory=pt,
    )
    r_cu.status = status
    r_cu.save()
    response = __get_response(api_client, instance.id, user=r_cu.user, status_codes=PermissionDenied)
    assert response.data == "change me"


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__contractor_another__manager__not_accepted_cu__fail(
    api_client, r_cu, get_cu_manager_fi, get_project_territory_fi, get_processed_report_fi, status
):
    pt = get_project_territory_fi(company=r_cu.company)
    cu_manager = get_cu_manager_fi(company=r_cu.company)
    instance = get_processed_report_fi(company_user=cu_manager, project_territory=pt)
    r_cu.status = status
    r_cu.save()
    response = __get_response(api_client, instance.id, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__client_project_manager__not_accepted_cu__fail(
    api_client,
    get_client_project_manager_fi: Callable,
    get_project_territory_fi: Callable,
    get_processed_report_fi,
    get_company_fi,
    status,
):
    requesting_project_manager = get_client_project_manager_fi()
    company = get_company_fi(kind=CompanyKind.CONTRACTOR.value)
    requesting_project_manager.project.company = company
    requesting_project_manager.project.save()
    pt = get_project_territory_fi(project=requesting_project_manager.project)
    instance = get_processed_report_fi(project_territory=pt)
    requesting_project_manager.company_user.status = status
    requesting_project_manager.company_user.save()
    response = __get_response(
        api_client,
        instance_id=instance.id,
        user=requesting_project_manager.company_user.user,
        status_codes=NotFound,
    )
    assert response.data == {"detail": NotFound.default_detail}


def test__contractor_user_from_different_company__fail(
    api_client, get_cu_fi, get_cu_manager_fi, get_processed_report_fi
):
    r_cu = get_cu_fi(role=CUR.OWNER)
    cu_manager = get_cu_manager_fi()
    instance = get_processed_report_fi(company_user=cu_manager)
    response = __get_response(api_client, instance.id, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__client_user_from_not_related_project__fail(
    api_client,
    r_cu: CompanyUser,
    get_processed_report_fi,
):
    instance = get_processed_report_fi()
    response = __get_response(
        api_client,
        instance_id=instance.id,
        user=r_cu.user,
        status_codes=NotFound,
    )
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("role", NOT_WORKER_ROLES)
@pytest.mark.parametrize("status", CompanyUserStatus.values)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__updated_by_company_user__response_data(
    api_client,
    get_processed_report_fi,
    get_project_territory_fi: Callable,
    r_cu: CompanyUser,
    get_cu_fi,
    status,
    role,
):
    company = r_cu.company
    instance = get_processed_report_fi(project_territory=get_project_territory_fi(company=company))
    updated_cu = get_cu_fi(company=company, role=role, status=status)
    PgLog.objects.create(
        level=PgLogLVL.info.value,
        user=updated_cu.user,
        model_name=ProcessedReport._meta.concrete_model.__name__,
        model_id=instance.id,
        message="",
        params={},
    )
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    assert response.data["updated_by"] == {
        "user": {
            "first_name": updated_cu.user.first_name,
            "last_name": updated_cu.user.last_name,
            "email": updated_cu.user.email,
        },
        "company_user": {
            "id": updated_cu.id,
            "email": updated_cu.user.email,
            "first_name": updated_cu.user.last_name,
            "last_name": updated_cu.user.last_name,
        },
    }, f'response.data.updated_by={response.data["updated_by"]}'


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__updated_by_admin__response_data(
    api_client,
    get_processed_report_fi,
    get_project_territory_fi: Callable,
    get_user_fi,
    r_cu: CompanyUser,
):
    instance = get_processed_report_fi(project_territory=get_project_territory_fi(company=r_cu.company))
    updated_user = get_user_fi()
    updated_user.is_superuser = True
    updated_user.save()

    PgLog.objects.create(
        level=PgLogLVL.info.value,
        user=updated_user,
        model_name=ProcessedReport._meta.concrete_model.__name__,
        model_id=instance.id,
        message="",
        params={},
    )
    response = __get_response(api_client, instance_id=instance.id, user=r_cu.user)
    assert response.data["updated_by"] == {
        "user": {
            "first_name": updated_user.first_name,
            "last_name": updated_user.last_name,
            "email": updated_user.email,
        },
        "company_user": {},
    }, f'response.data.updated_by={response.data["updated_by"]}'
