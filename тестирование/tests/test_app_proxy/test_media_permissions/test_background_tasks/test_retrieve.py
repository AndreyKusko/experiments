import json
import typing as tp
from http.client import responses

import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from tests.utils import get_authorization_token
from background.models import BackgroundTask
from ma_saas.constants.system import Callable
from ma_saas.constants.company import CUR, NOT_OWNER_ROLES, NOT_ACCEPT_CUS_VALUES
from proxy.views.media_permission import BACKGROUND_TASKS
from companies.models.company_user import CompanyUser
from ma_saas.constants.background_task import BackgroundTaskType as BTT

User = get_user_model()


def __get_response(
    api_client, model_id: int, status_codes: int, object_id: str, user: tp.Optional[User] = None
) -> Response:
    """Return response."""
    if user:
        api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user))
    response = api_client.get(f"/api/v1/media-permissions/{BACKGROUND_TASKS}/{model_id}/{object_id}/")
    assert response.status_code == status_codes
    assert response.status_text == responses[status_codes]
    return response


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("task_type", BTT.values)
def test__accpeted_owner__success(
    api_client, mock_policies_false, get_background_task_fi: Callable, r_cu: CompanyUser, task_type: int
):
    company = r_cu.company
    instance = get_background_task_fi(company=company, task_type=task_type, is_output_files=True)
    response = __get_response(
        api_client,
        user=r_cu.user,
        status_codes=status_code.HTTP_200_OK,
        model_id=instance.id,
        object_id=instance.output_files[0],
    )
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__client_cu_owner__model_owner__success(
    api_client, r_cu: CompanyUser, get_background_task_fi: Callable, get_company_fi
):
    instance = get_background_task_fi(
        company=get_company_fi(kind=CompanyKind.CONTRACTOR.value),
        company_user=r_cu,
        task_type=BTT.EXPORT_PROCESSED_REPORTS.value,
        is_output_files=True,
    )
    response = __get_response(
        api_client,
        user=r_cu.user,
        status_codes=status_code.HTTP_200_OK,
        model_id=instance.id,
        object_id=instance.output_files[0],
    )
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__client_cu_owner__not_model_owner__success(
    api_client,
    r_cu: CompanyUser,
    get_background_task_fi: Callable,
    get_company_fi,
    get_cu_fi,
):
    model_owner_cu = get_cu_fi(company=r_cu.company, role=CUR.OWNER)
    instance = get_background_task_fi(
        company=get_company_fi(kind=CompanyKind.CONTRACTOR.value),
        company_user=model_owner_cu,
        task_type=BTT.EXPORT_PROCESSED_REPORTS.value,
        is_output_files=True,
    )
    response = __get_response(
        api_client,
        user=r_cu.user,
        status_codes=status_code.HTTP_200_OK,
        model_id=instance.id,
        object_id=instance.output_files[0],
    )
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__client_cu_manager__model_owner__success(
    api_client,
    r_cu: CompanyUser,
    get_background_task_fi: Callable,
    get_company_fi,
    get_cu_fi,
):
    instance = get_background_task_fi(
        company=get_company_fi(kind=CompanyKind.CONTRACTOR.value),
        company_user=r_cu,
        task_type=BTT.EXPORT_PROCESSED_REPORTS.value,
        is_output_files=True,
    )
    response = __get_response(
        api_client,
        user=r_cu.user,
        status_codes=status_code.HTTP_200_OK,
        model_id=instance.id,
        object_id=instance.output_files[0],
    )
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__client_cu_manager__not_model_owner__success(
    api_client,
    r_cu: CompanyUser,
    get_background_task_fi: Callable,
    get_company_fi,
    get_cu_fi,
):
    model_owner_cu = get_cu_fi(company=r_cu.company, role=CUR.OWNER)
    instance = get_background_task_fi(
        company=get_company_fi(kind=CompanyKind.CONTRACTOR.value),
        company_user=model_owner_cu,
        task_type=BTT.EXPORT_PROCESSED_REPORTS.value,
        is_output_files=True,
    )
    response = __get_response(
        api_client,
        user=r_cu.user,
        status_codes=status_code.HTTP_200_OK,
        model_id=instance.id,
        object_id=instance.output_files[0],
    )
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
@pytest.mark.parametrize("task_type", BTT.values)
def test__contractor_model_owner__success(
    api_client, get_background_task_fi: Callable, r_cu: CompanyUser, task_type: int
):
    _company = r_cu.company
    instance = get_background_task_fi(
        company=_company, company_user=r_cu, task_type=task_type, is_output_files=True
    )
    response = __get_response(
        api_client,
        user=r_cu.user,
        status_codes=status_code.HTTP_200_OK,
        model_id=instance.id,
        object_id=instance.output_files[0],
    )
    assert not response.data


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
@pytest.mark.parametrize("status", NOT_ACCEPT_CUS_VALUES)
def test__contractor__not_model_owner__not_owner_cu__fail(
    api_client, get_background_task_fi: Callable, get_cu_fi, role, status
):
    r_cu = get_cu_fi(role=role, status=status)
    instance = get_background_task_fi(
        company=r_cu.company, task_type=BTT.EXPORT_PROCESSED_REPORTS.value, is_output_files=True
    )
    response = __get_response(
        api_client,
        user=r_cu.user,
        status_codes=status_code.HTTP_403_FORBIDDEN,
        model_id=instance.id,
        object_id=instance.output_files[0],
    )
    assert not response.data


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS_VALUES)
def test__client_cu_owner__not_accepted_cu__fail(
    api_client,
    get_background_task_fi: Callable,
    get_company_fi,
    get_cu_fi,
    status,
):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status)
    instance = get_background_task_fi(
        company=get_company_fi(kind=CompanyKind.CONTRACTOR.value),
        company_user=r_cu,
        task_type=BTT.EXPORT_PROCESSED_REPORTS.value,
        is_output_files=True,
    )
    response = __get_response(
        api_client,
        user=r_cu.user,
        status_codes=status_code.HTTP_403_FORBIDDEN,
        model_id=instance.id,
        object_id=instance.output_files[0],
    )
    assert not response.data


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS_VALUES)
def test__contractor_not_accepted_cu_owner__fail(
    api_client, get_background_task_fi: Callable, get_cu_fi, status
):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status)
    company = r_cu.company
    instance = get_background_task_fi(
        company=company, task_type=BTT.EXPORT_PROCESSED_REPORTS.value, is_output_files=True
    )
    response = __get_response(
        api_client,
        user=r_cu.user,
        status_codes=status_code.HTTP_403_FORBIDDEN,
        model_id=instance.id,
        object_id=instance.output_files[0],
    )
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(("attribute", "value"), (("is_deleted", True), ("is_verified_email", False)))
def not_contractor__not_ta_r_cu_owner__fail(
    api_client, get_background_task_fi: Callable, r_cu: CompanyUser, attribute: str, value: int
):
    company = r_cu.company
    instance = get_background_task_fi(company=company, task_type=BTT.EXPORT_PROCESSED_REPORTS.value)
    setattr(r_cu.user, attribute, value)
    r_cu.user.save()
    response = __get_response(
        api_client,
        user=r_cu.user,
        status_codes=status_code.HTTP_403_FORBIDDEN,
        model_id=instance.id,
        object_id=json.loads(instance.output_files)[0],
    )
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
@pytest.mark.parametrize(("attribute", "value"), (("is_deleted", True), ("is_verified_email", False)))
def test__contractor__not_ta_requesting_model_owner__fail(
    api_client, get_background_task_fi: Callable, r_cu: CompanyUser, attribute: str, value: int
):
    company = r_cu.company
    task_type = BTT.EXPORT_PROCESSED_REPORTS.value
    instance = get_background_task_fi(
        company=company, company_user=r_cu, task_type=task_type, is_output_files=True
    )
    setattr(r_cu.user, attribute, value)
    r_cu.user.save()
    response = __get_response(
        api_client,
        user=r_cu.user,
        status_codes=status_code.HTTP_403_FORBIDDEN,
        model_id=instance.id,
        object_id=instance.output_files[0],
    )
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(("attribute", "value"), (("is_deleted", True), ("is_verified_email", False)))
def test__client__not_ta_r_cu_owner_model_owner__fail(
    api_client,
    r_cu: CompanyUser,
    get_company_fi,
    get_background_task_fi: Callable,
    attribute: str,
    value: int,
):
    instance = get_background_task_fi(
        company=get_company_fi(kind=CompanyKind.CONTRACTOR.value),
        company_user=r_cu,
        task_type=BTT.EXPORT_PROCESSED_REPORTS.value,
        is_output_files=True,
    )
    setattr(r_cu.user, attribute, value)
    r_cu.user.save()

    response = __get_response(
        api_client,
        user=r_cu.user,
        status_codes=status_code.HTTP_403_FORBIDDEN,
        model_id=instance.id,
        object_id=instance.output_files[0],
    )
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__not_existing_not_found__fail(api_client, get_background_task_fi: Callable, r_cu: CompanyUser):
    task_type = BTT.EXPORT_PROCESSED_REPORTS.value
    get_background_task_fi(company=r_cu.company, company_user=r_cu, task_type=task_type, is_output_files=True)
    instance_last_instance = BackgroundTask.objects.all().order_by("id").last()
    response = __get_response(
        api_client,
        user=r_cu.user,
        status_codes=NotFound,
        model_id=instance_last_instance.id + 1,
        object_id=instance_last_instance.output_files[0],
    )
    assert response.data["detail"] == NotFound.default_detail
