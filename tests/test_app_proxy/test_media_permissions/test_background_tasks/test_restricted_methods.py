import json

import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound

from tests.utils import get_authorization_token
from ma_saas.constants.system import Callable
from proxy.views.media_permission import BACKGROUND_TASKS
from companies.models.company_user import CompanyUser
from ma_saas.constants.background_task import BackgroundTaskType as BTT

User = get_user_model()


link = f"/api/v1/media-permissions/{BACKGROUND_TASKS}"


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__post__fail(api_client, r_cu: CompanyUser):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.post(f"{link}/")
    assert response.status_code == NotFound.status_code


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__post_with_instance__fail(api_client, r_cu: CompanyUser, get_background_task_fi: Callable):
    company = r_cu.company
    instance = get_background_task_fi(
        company=company, task_type=BTT.EXPORT_PROCESSED_REPORTS.value, is_output_files=True
    )
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.post(f"{link}/{instance.id}/{instance.output_files[0]}/")
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__patch__fail(api_client, r_cu: CompanyUser, get_background_task_fi: Callable):
    company = r_cu.company
    instance = get_background_task_fi(
        company=company, task_type=BTT.EXPORT_PROCESSED_REPORTS.value, is_output_files=True
    )
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.patch(f"{link}/{instance.id}/{instance.output_files[0]}/", data={})
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__put__fail(api_client, r_cu: CompanyUser, get_background_task_fi: Callable):
    company = r_cu.company
    instance = get_background_task_fi(
        company=company, task_type=BTT.EXPORT_PROCESSED_REPORTS.value, is_output_files=True
    )
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.put(f"{link}/{instance.id}/{json.loads(instance.output_files)[0]}/", data={})
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__put__fail(api_client, r_cu: CompanyUser, get_background_task_fi: Callable):
    company = r_cu.company
    instance = get_background_task_fi(
        company=company, task_type=BTT.EXPORT_PROCESSED_REPORTS.value, is_output_files=True
    )
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.put(f"{link}/{instance.id}/{instance.output_files[0]}/", data={})
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__delete__fail(api_client, r_cu: CompanyUser, get_background_task_fi: Callable):
    company = r_cu.company
    instance = get_background_task_fi(
        company=company, task_type=BTT.EXPORT_PROCESSED_REPORTS.value, is_output_files=True
    )
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.delete(f"{link}/{instance.id}/{instance.output_files[0]}/")
    status_codes = status_code.HTTP_405_METHOD_NOT_ALLOWED
    assert response.status_code == status_codes


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__list__method__fail(api_client, r_cu: CompanyUser):
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.get(f"{link}")
    assert response.status_code == NotFound.status_code


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__list__with_model__method__fail(api_client, r_cu: CompanyUser, get_background_task_fi: Callable):
    company = r_cu.company
    instance = get_background_task_fi(
        company=company, task_type=BTT.EXPORT_PROCESSED_REPORTS.value, is_output_files=True
    )
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.get(f"{link}/{instance.id}/")
    assert response.status_code == NotFound.status_code
