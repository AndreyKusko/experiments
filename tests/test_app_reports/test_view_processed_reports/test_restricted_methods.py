import pytest
from rest_framework import status as status_code

from ma_saas.utils.encriptor import encrypt_public_link_obj_id
from ma_saas.constants.system import API_V1

VIEW_PROCESSED_REPORT_LINK = f"/{API_V1}/view-manager-reports"


def test__patch__fail(api_client, processed_report_fi):
    encrypted_value = encrypt_public_link_obj_id(value=str(processed_report_fi.id), is_id=True)
    response = api_client.patch(f"{VIEW_PROCESSED_REPORT_LINK}/{encrypted_value}/", data={})
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


def test__put__fail(api_client, processed_report_fi):
    encrypted_value = encrypt_public_link_obj_id(value=str(processed_report_fi.id), is_id=True)
    response = api_client.put(f"{VIEW_PROCESSED_REPORT_LINK}/{encrypted_value}/", data={})
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


def test__delete__fail(api_client, processed_report_fi):
    encrypted_value = encrypt_public_link_obj_id(value=str(processed_report_fi.id), is_id=True)
    response = api_client.delete(f"{VIEW_PROCESSED_REPORT_LINK}/{encrypted_value}/")
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED


def test__list__fail(api_client, processed_report_fi):
    response = api_client.patch(f"{VIEW_PROCESSED_REPORT_LINK}/")
    assert response.status_code == status_code.HTTP_404_NOT_FOUND
