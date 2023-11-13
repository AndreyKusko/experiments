import typing as tp

import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from tests.utils import _process_status_codes, get_authorization_token
from accounts.models import USER_IS_DELETED, NOT_TA_USER_REASON, USER_EMAIL_NOT_VERIFIED
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from ma_saas.constants.system import TYPE, VALUES, BASENAME
from clients.policies.interface import Policies
from proxy.views.media_permission import WORKER_INSTRUCTION
from companies.models.company_user import NOT_TA_RCU_REASON
from ma_saas.constants.worker_instruction import GALLERY, WORKER_INSTRUCTION_MEDIA_TYPES

User = get_user_model()


def __get_response(
    api_client, model_id: int, object_id: str, status_codes=None, user: tp.Optional[User] = None
) -> Response:
    """Return response."""
    if user:
        api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(user))
    response = api_client.post(f"/api/v1/media-permissions/{WORKER_INSTRUCTION}/{model_id}/{object_id}/")

    expecting_status_codes = _process_status_codes(status_codes, default={status_code.HTTP_200_OK})
    response_status_code = response.status_code
    is_correct_response_status_code = response_status_code in expecting_status_codes
    assert (
        is_correct_response_status_code
    ), f"response_status_code {response_status_code} not in {expecting_status_codes} | response.data = {response.data}"
    # assert response.status_text == responses[status_codes]

    return response


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("media_type", WORKER_INSTRUCTION_MEDIA_TYPES)
@pytest.mark.parametrize("is_gallery", (True, False))
def test__accepted_owner__success(
    api_client, mock_policies_false, r_cu, get_worker_instruction_fi, media_type, is_gallery
):
    object_id = "e0kj309230e0203"
    media_field = {TYPE: media_type, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    data = [{TYPE: GALLERY, VALUES: [media_field]}] if is_gallery else [media_field]

    parent_instance = get_worker_instruction_fi(company=r_cu.company, instructions_data=data)

    response = __get_response(api_client, user=r_cu.user, model_id=parent_instance.id, object_id=object_id)
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("attribute", "value", "err_msg"),
    (("is_deleted", True, USER_IS_DELETED), ("is_verified_email", False, USER_EMAIL_NOT_VERIFIED)),
)
@pytest.mark.parametrize("media_type", WORKER_INSTRUCTION_MEDIA_TYPES)
@pytest.mark.parametrize("is_gallery", (True, False))
def test__contractor_not_ta_cu_owner__fail(
    monkeypatch,
    api_client,
    r_cu,
    get_worker_instruction_fi,
    media_type,
    is_gallery,
    attribute,
    value,
    err_msg,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    object_id = "e0kj309230e0203"
    media_field = {TYPE: media_type, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    data = [{TYPE: GALLERY, VALUES: [media_field]}] if is_gallery else [media_field]

    parent_instance = get_worker_instruction_fi(company=r_cu.company, instructions_data=data)
    setattr(r_cu.user, attribute, value)
    r_cu.user.save()
    response = __get_response(
        api_client,
        user=r_cu.user,
        model_id=parent_instance.id,
        object_id=object_id,
        status_codes=PermissionDenied,
    )
    assert response.data == {
        "detail": NOT_TA_RCU_REASON.format(reason=NOT_TA_USER_REASON.format(reason=err_msg))
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
@pytest.mark.parametrize("media_type", WORKER_INSTRUCTION_MEDIA_TYPES)
@pytest.mark.parametrize("is_gallery", (True, False))
def test__contractor__manager_with_policy__success(
    api_client, monkeypatch, r_cu, get_worker_instruction_fi, media_type, is_gallery, get_project_fi
):

    object_id = "e0kj309230e0203"

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    project = get_project_fi(company=r_cu.company)
    media_field = {TYPE: media_type, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    data = [{TYPE: GALLERY, VALUES: [media_field]}] if is_gallery else [media_field]

    parent_instance = get_worker_instruction_fi(project=project, instructions_data=data)
    response = __get_response(api_client, user=r_cu.user, model_id=parent_instance.id, object_id=object_id)
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
@pytest.mark.parametrize("media_type", WORKER_INSTRUCTION_MEDIA_TYPES)
@pytest.mark.parametrize("is_gallery", (True, False))
@pytest.mark.parametrize(
    ("attribute", "value", "err_msg"),
    (("is_deleted", True, USER_IS_DELETED), ("is_verified_email", False, USER_EMAIL_NOT_VERIFIED)),
)
def test__contractor_not_ta_requesting__manager__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_project_fi,
    get_worker_instruction_fi,
    media_type,
    is_gallery,
    attribute: str,
    value: int,
    err_msg,
):
    object_id = "e0kj309230e0203"
    project = get_project_fi(company=r_cu.company)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    media_field = {TYPE: media_type, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    data = [{TYPE: GALLERY, VALUES: [media_field]}] if is_gallery else [media_field]

    parent_instance = get_worker_instruction_fi(project=project, instructions_data=data)
    setattr(r_cu.user, attribute, value)
    r_cu.user.save()
    response = __get_response(
        api_client,
        user=r_cu.user,
        model_id=parent_instance.id,
        object_id=object_id,
        status_codes=PermissionDenied,
    )
    assert response.data == {
        "detail": NOT_TA_RCU_REASON.format(reason=NOT_TA_USER_REASON.format(reason=err_msg))
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
@pytest.mark.parametrize("media_type", WORKER_INSTRUCTION_MEDIA_TYPES)
@pytest.mark.parametrize("is_gallery", (True, False))
def test__contractor__manager_without_policy__fail(
    api_client, monkeypatch, r_cu, get_worker_instruction_fi, get_project_fi, media_type, is_gallery
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [])

    project = get_project_fi(company=r_cu.company)
    object_id = "e0kj309230e0203"
    media_field = {TYPE: media_type, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    data = [{TYPE: GALLERY, VALUES: [media_field]}] if is_gallery else [media_field]

    parent_instance = get_worker_instruction_fi(project=project, instructions_data=data)
    response = __get_response(
        api_client,
        user=r_cu.user,
        model_id=parent_instance.id,
        object_id=object_id,
        status_codes=PermissionDenied,
    )
    assert not response.data


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
@pytest.mark.parametrize("media_type", WORKER_INSTRUCTION_MEDIA_TYPES)
@pytest.mark.parametrize("is_gallery", (True, False))
@pytest.mark.parametrize("has_object_policy", (True, False))
def test__contractor_pt_worker___fail(
    api_client, monkeypatch, pt_worker, get_worker_instruction_fi, media_type, is_gallery, has_object_policy
):
    r_cu, object_id = pt_worker.company_user, "e0kj309230e0203"

    __get_target_policies_return = [r_cu.company.id] if has_object_policy else []
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: __get_target_policies_return)

    media_field = {TYPE: media_type, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    data = [{TYPE: GALLERY, VALUES: [media_field]}] if is_gallery else [media_field]

    parent_instance = get_worker_instruction_fi(
        project=pt_worker.project_territory.project, instructions_data=data
    )
    response = __get_response(
        api_client,
        user=r_cu.user,
        model_id=parent_instance.id,
        object_id=object_id,
        status_codes=PermissionDenied,
    )
    assert not response.data


@pytest.mark.parametrize("pt_worker", [pytest.lazy_fixture("contractor_pt_worker_fi")])
@pytest.mark.parametrize("media_type", WORKER_INSTRUCTION_MEDIA_TYPES)
@pytest.mark.parametrize("is_gallery", (True, False))
@pytest.mark.parametrize("has_object_policy", (True, False))
@pytest.mark.parametrize("with_reservation", (True, False))
def test__contractor_pt_worker__fail(
    api_client,
    monkeypatch,
    pt_worker,
    get_worker_instruction_fi,
    get_schedule_time_slot_fi,
    get_reservation_fi,
    media_type,
    is_gallery,
    has_object_policy,
    with_reservation,
):
    r_cu, object_id = pt_worker.company_user, "e0kj309230e0203"

    __get_target_policies_return = [r_cu.company.id] if has_object_policy else []
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: __get_target_policies_return)

    media_field = {TYPE: media_type, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    data = [{TYPE: GALLERY, VALUES: [media_field]}] if is_gallery else [media_field]

    sts = get_schedule_time_slot_fi(project_territory=pt_worker.project_territory)
    if with_reservation:
        get_reservation_fi(schedule_time_slot=sts, project_territory_worker=pt_worker)

    parent_instance = get_worker_instruction_fi(project_scheme=sts.project_scheme, instructions_data=data)

    response = __get_response(
        api_client,
        user=r_cu.user,
        model_id=parent_instance.id,
        object_id=object_id,
        status_codes=PermissionDenied,
    )
    assert not response.data


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
@pytest.mark.parametrize("media_type", WORKER_INSTRUCTION_MEDIA_TYPES)
@pytest.mark.parametrize("is_gallery", (True, False))
@pytest.mark.parametrize("has_object_policy", (True, False))
def test__labour_exchange_project__success(
    api_client,
    monkeypatch,
    r_u,
    get_worker_instruction_fi,
    get_project_scheme_fi,
    get_reservation_fi,
    media_type,
    is_gallery,
    has_object_policy,
):
    object_id = "e0kj309230e0203"
    media_field = {TYPE: media_type, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    data = [{TYPE: GALLERY, VALUES: [media_field]}] if is_gallery else [media_field]
    project_scheme = get_project_scheme_fi(is_labour_exchange=True)
    parent_instance = get_worker_instruction_fi(project=project_scheme.project, instructions_data=data)
    company = parent_instance.project.company

    __get_target_policies_return = [company.id] if has_object_policy else []
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: __get_target_policies_return)

    response = __get_response(
        api_client, user=r_u, model_id=parent_instance.id, object_id=object_id, status_codes=PermissionDenied
    )
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}


@pytest.mark.parametrize("r_u", [pytest.lazy_fixture("user_fi")])
@pytest.mark.parametrize("media_type", WORKER_INSTRUCTION_MEDIA_TYPES)
@pytest.mark.parametrize("is_gallery", (True, False))
@pytest.mark.parametrize("has_object_policy", (True, False))
def test__not_labour_exchange_project__fail(
    api_client,
    monkeypatch,
    r_u,
    get_worker_instruction_fi,
    get_project_scheme_fi,
    get_reservation_fi,
    media_type,
    is_gallery,
    has_object_policy,
):
    object_id = "e0kj309230e0203"
    media_field = {TYPE: media_type, VALUES: [object_id], BASENAME: "123123123.jpeg"}
    data = [{TYPE: GALLERY, VALUES: [media_field]}] if is_gallery else [media_field]
    project_scheme = get_project_scheme_fi(is_labour_exchange=False)
    parent_instance = get_worker_instruction_fi(project=project_scheme.project, instructions_data=data)
    company = parent_instance.project.company

    __get_target_policies_return = [company.id] if has_object_policy else []
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: __get_target_policies_return)

    response = __get_response(
        api_client, user=r_u, model_id=parent_instance.id, object_id=object_id, status_codes=PermissionDenied
    )
    assert response.data == {"detail": REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY}
