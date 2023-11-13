import typing as tp
from http.client import responses

import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.response import Response

from tests.utils import get_authorization_token
from pg_logger.views import PgLogger
from pg_logger.models import PgLog
from ma_saas.utils.encriptor import encrypt_public_link_obj_id
from ma_saas.constants.report import ProcessedReportFormFieldSpecKeys
from ma_saas.constants.system import VALUES, VALUES_LINKS, DATETIME_FORMAT, PgLogLVL
from ma_saas.constants.company import ROLES, CompanyUserStatus
from clients.objects_store.views import make_objstore_file_public_link
from reports.models.processed_report import ProcessedReport
from tests.test_app_reports.test_view_processed_reports.test_restricted_methods import (
    VIEW_PROCESSED_REPORT_LINK,
)

User = get_user_model()
pg_logger = PgLogger()


def __get_response(
    api_client, encrypted_instance_id: str, status_codes: int, user: tp.Optional[User] = None
) -> Response:
    """Return response."""
    if user:
        api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user))
    response = api_client.get(f"{VIEW_PROCESSED_REPORT_LINK}/{encrypted_instance_id}/")
    assert response.status_code == status_codes, f"response.data = {response.data}"
    assert response.status_text == responses[status_codes]
    return response


def test__data_response(api_client, processed_report_fi):
    encrypted_value = encrypt_public_link_obj_id(value=str(processed_report_fi.id), is_id=True)
    response = __get_response(api_client, encrypted_instance_id=encrypted_value)

    assert response.data
    assert len(response.data) == 11

    assert response.data["comment"] == processed_report_fi.comment
    assert response.data["public_client_link_id"] == encrypted_value

    author_user = processed_report_fi.company_user.user
    assert response.data["company_user"] == {
        "first_name": author_user.first_name,
        "last_name": author_user.last_name,
    }

    prf = processed_report_fi.processed_report_form
    assert response.data["project"] == {"title": prf.project_scheme.project.title}
    assert response.data["processed_report_form"] == {"fields_specs": prf.fields_specs}

    assert response.data["updated_by"] == {"user": {}}
    assert response.data["created_at"] == processed_report_fi.created_at.strftime(DATETIME_FORMAT)
    assert response.data["updated_at"] == processed_report_fi.updated_at.strftime(DATETIME_FORMAT)
    assert not response.data["accepted_at"]

    assert response.data["json_fields"] == {
        "1": {
            VALUES_LINKS: {
                "video": [
                    make_objstore_file_public_link(
                        processed_report_fi.json_fields["1"][VALUES][ProcessedReportFormFieldSpecKeys.VIDEO][
                            0
                        ]
                    )
                ],
                "audio": [
                    make_objstore_file_public_link(
                        processed_report_fi.json_fields["1"][VALUES][ProcessedReportFormFieldSpecKeys.AUDIO][
                            0
                        ]
                    )
                ],
                "photo": [
                    make_objstore_file_public_link(
                        processed_report_fi.json_fields["1"][VALUES][ProcessedReportFormFieldSpecKeys.PHOTO][
                            0
                        ]
                    )
                ],
            }
        }
    }


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", CompanyUserStatus.values)
def test__updated_by_company_user_data(api_client, processed_report_fi, get_cu_fi, status, role):
    updated_cu = get_cu_fi(
        company=processed_report_fi.processed_report_form.project_scheme.project.company,
        role=role,
        status=status,
    )
    PgLog.objects.create(
        level=PgLogLVL.info.value,
        user=updated_cu.user,
        model_name=ProcessedReport._meta.concrete_model.__name__,
        model_id=processed_report_fi.id,
        message="",
        params={},
    )
    encrypted_value = encrypt_public_link_obj_id(value=str(processed_report_fi.id), is_id=True)
    response = __get_response(api_client, encrypted_instance_id=encrypted_value)
    assert response.data["updated_by"] == {
        "user": {"first_name": updated_cu.user.first_name, "last_name": updated_cu.user.last_name}
    }, f'response.data.updated_by ={response.data["updated_by"]}'


def test__updated_by_admin_data(api_client, processed_report_fi, get_user_fi):
    updated_user = get_user_fi()
    updated_user.is_superuser = True
    updated_user.save()

    PgLog.objects.create(
        level=PgLogLVL.info.value,
        user=updated_user,
        model_name=ProcessedReport._meta.concrete_model.__name__,
        model_id=processed_report_fi.id,
        message="",
        params={},
    )
    encrypted_value = encrypt_public_link_obj_id(value=str(processed_report_fi.id), is_id=True)
    response = __get_response(api_client, encrypted_instance_id=encrypted_value)

    assert response.data["updated_by"] == {
        "user": {"first_name": updated_user.first_name, "last_name": updated_user.last_name}
    }, f'response.data.updated_by ={response.data["updated_by"]}'


def test__anonymous__success(api_client, processed_report_fi):
    encrypted_value = encrypt_public_link_obj_id(value=str(processed_report_fi.id), is_id=True)
    response = __get_response(api_client, encrypted_instance_id=encrypted_value)
    assert response.data


def test__random_user__success(api_client, processed_report_fi):
    encrypted_value = encrypt_public_link_obj_id(value=str(processed_report_fi.id), is_id=True)
    response = __get_response(api_client, encrypted_instance_id=encrypted_value)
    assert response.data


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("status", CompanyUserStatus.values)
@pytest.mark.parametrize("is_deleted", (True, False))
def test__any_company_user__success(
    api_client,
    processed_report_fi,
    get_cu_fi,
    role,
    status,
    is_deleted: bool,
):
    r_cu = get_cu_fi(role=role, status=status)
    setattr(r_cu, "is_deleted", is_deleted)
    r_cu.save()

    encrypted_value = encrypt_public_link_obj_id(value=str(processed_report_fi.id), is_id=True)
    response = __get_response(
        api_client,
        encrypted_instance_id=encrypted_value,
        status_codes=status_code.HTTP_200_OK,
        user=r_cu.user,
    )
    assert response.data


@pytest.mark.parametrize("field_name", ("is_deleted", "is_blocked"))
@pytest.mark.parametrize("value", (True, False))
def test__not_ta_user__success(api_client, processed_report_fi, user_fi: User, field_name: str, value: bool):
    user = user_fi
    setattr(user, field_name, value)
    user.save()

    encrypted_value = encrypt_public_link_obj_id(value=str(processed_report_fi.id), is_id=True)
    response = __get_response(api_client, encrypted_instance_id=encrypted_value)
    assert response.data
