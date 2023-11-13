import functools

import pytest
import requests
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_create
from accounts.models import USER_IS_BLOCKED, USER_IS_DELETED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from tests.mocked_instances import MockResponse
from companies.models.company import COMPANY_IS_DELETED, NOT_TA_COMPANY_REASON
from ma_saas.constants.system import TYPE, TITLE, VALUES, BASENAME
from ma_saas.constants.company import NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_REASON, NOT_TA_RCU_MUST_BE_ACCEPT, CompanyUser
from reports.models.worker_instruction import (
    WORKER_INSTRUCTION_PROJECT_DUPLICATION_ERROR,
    WORKER_INSTRUCTION_PROJECT_SCHEME_DUPLICATION_ERROR,
    WorkerInstruction,
)
from ma_saas.constants.worker_instruction import (
    GALLERY,
    WORKER_INSTRUCTION_MEDIA_TYPES,
    WorkerInstructionMediaType,
)

User = get_user_model()

__get_response = functools.partial(request_response_create, path="/api/v1/worker-instructions/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, {}, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__acccepted_owner__success(api_client, mock_policies_false, r_cu, new_worker_instruction_data):
    data = new_worker_instruction_data(company=r_cu.company)
    response = __get_response(api_client, data=data, user=r_cu.user)
    assert WorkerInstruction.objects.filter(id=response.data["id"]).exists()
    assert response.data.get("id")


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_owner__fail(
    api_client, monkeypatch, get_cu_owner_fi, new_worker_instruction_data, status
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu = get_cu_owner_fi(status=status.value)
    data = new_worker_instruction_data(company=r_cu.company)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__without_policy__fail(
    api_client, monkeypatch, get_cu_fi, new_worker_instruction_data, role
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)

    r_cu = get_cu_fi(role=role)
    data = new_worker_instruction_data(company=r_cu.company)
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data["detail"] == PermissionDenied.default_detail


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__with_policy__success(
    api_client, monkeypatch, get_cu_fi, new_worker_instruction_data, role
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    r_cu = get_cu_fi(role=role)
    data = new_worker_instruction_data(company=r_cu.company)
    response = __get_response(api_client, data, r_cu.user)
    assert response.data["id"]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("is_user", "field", "err_text"),
    (
        (True, "is_blocked", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_BLOCKED)),
        (True, "is_deleted", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_DELETED)),
        (False, "is_deleted", REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY),
    ),
)
@pytest.mark.parametrize("has_object_policy", [True, False])
def test__not_ta__cu__fail(
    api_client, monkeypatch, r_cu, new_worker_instruction_data, has_object_policy, is_user, field, err_text
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    data = new_worker_instruction_data(company=r_cu.company)
    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()
    else:
        setattr(r_cu, field, True)
        r_cu.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": err_text}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_company__fail(api_client, monkeypatch, r_cu, new_worker_instruction_data):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

    data = new_worker_instruction_data(company=r_cu.company)
    r_cu.company.is_deleted = True
    r_cu.company.save()
    response = __get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {
        "detail": NOT_TA_RCU_REASON.format(reason=NOT_TA_COMPANY_REASON.format(reason=COMPANY_IS_DELETED))
    }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__duplicates__with_project_only__fails(
    api_client, monkeypatch, r_cu, get_project_fi, new_worker_instruction_data
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    project = get_project_fi(company=r_cu.company)
    data = new_worker_instruction_data(project=project)

    __get_response(api_client, data=data, user=r_cu.user)
    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == [WORKER_INSTRUCTION_PROJECT_DUPLICATION_ERROR.format(project_id=project.id)]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__duplicates__with_project_scheme__fails(
    api_client, monkeypatch, r_cu, get_project_scheme_fi, new_worker_instruction_data
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    project_scheme = get_project_scheme_fi(company=r_cu.company)
    data = new_worker_instruction_data(project_scheme=project_scheme)
    __get_response(api_client, data=data, user=r_cu.user)

    response = __get_response(api_client, data=data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == [
        WORKER_INSTRUCTION_PROJECT_SCHEME_DUPLICATION_ERROR.format(project_scheme_id=project_scheme.id)
    ]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__with_project_scheme__response_data(
    api_client, monkeypatch, r_cu, get_project_scheme_fi, new_worker_instruction_data
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)

    instructions_data = [
        {TYPE: WorkerInstructionMediaType.DOCUMENT, BASENAME: "123123123.jpeg"},
        {TYPE: "text", VALUES: ["some fries motherfucker"], TITLE: "Samuel Mc'Donald"},
        {TYPE: "list", TITLE: "lng to learn"},
    ]
    project_scheme = get_project_scheme_fi(company=r_cu.company)
    data = new_worker_instruction_data(project_scheme=project_scheme, instructions_data=instructions_data)
    response = __get_response(api_client, data=data, user=r_cu.user)
    response_instance = response.data

    created_instance_id = response_instance.pop("id")
    assert created_instance_id
    created_instance = WorkerInstruction.objects.get(id=created_instance_id)

    assert response_instance.pop("project_scheme") == {"id": project_scheme.id}
    assert response_instance.pop("project") == {}

    response_instructions = response_instance.pop("data")
    assert response_instructions
    if response_instructions:
        assert len(created_instance.data) == len(response_instructions)
        assert response_instructions == created_instance.data
        assert response_instructions == instructions_data
        instruction1, instruction2, instruction3 = 0, 1, 2

        response_instruction_3 = response_instructions[instruction3]
        assert response_instruction_3
        if response_instruction_3:
            created_instance_3i_type = created_instance.data[instruction3].get(TYPE)
            del response_instructions[instruction3]
            assert response_instruction_3.pop(TYPE) == created_instance_3i_type
            created_instance_3i_title = created_instance.data[instruction3].get(TITLE)
            assert response_instruction_3.pop(TITLE) == created_instance_3i_title
        assert not response_instruction_3

        response_instruction_2 = response_instructions[instruction2]
        assert response_instruction_2
        if response_instruction_2:
            created_instance_2i_type = created_instance.data[instruction2].get(TYPE)
            del response_instructions[instruction2]
            assert response_instruction_2.pop(TYPE) == created_instance_2i_type
            created_instance_2i_values = created_instance.data[instruction2].get(VALUES)
            assert len(created_instance_2i_values) == 1
            assert response_instruction_2.pop(VALUES) == created_instance_2i_values
            created_instance_2i_title = created_instance.data[instruction2].get(TITLE)
            assert response_instruction_2.pop(TITLE) == created_instance_2i_title
        assert not response_instruction_2

        response_instruction_1 = response_instructions[instruction1]
        assert response_instruction_1
        if response_instruction_1:
            created_instance_1i_type = created_instance.data[instruction1].get(TYPE)
            del response_instructions[instruction1]
            assert response_instruction_1.pop(TYPE) == created_instance_1i_type
            created_instance_1i_basename = created_instance.data[instruction1].get(BASENAME)
            assert response_instruction_1.pop(BASENAME) == created_instance_1i_basename
        assert not response_instruction_1
    assert not response_instructions

    assert not response_instance


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__with_project_scheme__response_data(
    api_client, monkeypatch, r_cu, get_project_fi, new_worker_instruction_data
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)

    instructions_data = [
        {TYPE: WorkerInstructionMediaType.DOCUMENT, BASENAME: "123123123.jpeg"},
        {TYPE: "text", VALUES: ["some fries motherfucker"], TITLE: "Samuel Mc'Donald"},
        {TYPE: "list", TITLE: "lng to learn"},
    ]
    project = get_project_fi(company=r_cu.company)
    data = new_worker_instruction_data(project=project, instructions_data=instructions_data)
    response = __get_response(api_client, data=data, user=r_cu.user)
    response_instance = response.data

    created_instance_id = response_instance.pop("id")
    assert created_instance_id
    created_instance = WorkerInstruction.objects.get(id=created_instance_id)

    assert response_instance.pop("title") is None
    assert response_instance.pop("project_scheme") == {}
    assert response_instance.pop("project_variables_keys") == []
    assert response_instance.pop("project") == {"id": project.id}

    response_instructions = response_instance.pop("data")
    assert response_instructions
    if response_instructions:
        assert len(created_instance.data) == len(response_instructions)
        instruction1, instruction2, instruction3 = 0, 1, 2

        response_instruction_3 = response_instructions[instruction3]
        assert response_instruction_3
        if response_instruction_3:
            created_instance_3i_type = created_instance.data[instruction3].get(TYPE)
            del response_instructions[instruction3]
            assert response_instruction_3.pop(TYPE) == created_instance_3i_type
            created_instance_3i_title = created_instance.data[instruction3].get(TITLE)
            assert response_instruction_3.pop(TITLE) == created_instance_3i_title
        assert not response_instruction_3

        response_instruction_2 = response_instructions[instruction2]
        assert response_instruction_2
        if response_instruction_2:
            created_instance_2i_type = created_instance.data[instruction2].get(TYPE)
            del response_instructions[instruction2]
            assert response_instruction_2.pop(TYPE) == created_instance_2i_type
            created_instance_2i_values = created_instance.data[instruction2].get(VALUES)
            assert len(created_instance_2i_values) == 1
            assert response_instruction_2.pop(VALUES) == created_instance_2i_values
            created_instance_2i_title = created_instance.data[instruction2].get(TITLE)
            assert response_instruction_2.pop(TITLE) == created_instance_2i_title
        assert not response_instruction_2

        response_instruction_1 = response_instructions[instruction1]
        assert response_instruction_1
        if response_instruction_1:
            created_instance_1i_type = created_instance.data[instruction1].get(TYPE)
            del response_instructions[instruction1]
            assert response_instruction_1.pop(TYPE) == created_instance_1i_type
            created_instance_1i_basename = created_instance.data[instruction1].get(BASENAME)
            assert response_instruction_1.pop(BASENAME) == created_instance_1i_basename
        assert not response_instruction_1
    assert not response_instructions

    assert not response_instance


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("media_type", WORKER_INSTRUCTION_MEDIA_TYPES)
def test__media_fields__response_data(
    api_client, monkeypatch, r_cu, get_project_fi, new_worker_instruction_data, media_type
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)

    instructions_data = [{TYPE: media_type, BASENAME: "123123123.jpeg"}]
    project = get_project_fi(company=r_cu.company)
    data = new_worker_instruction_data(project=project, instructions_data=instructions_data)
    response = __get_response(api_client, data=data, user=r_cu.user)
    response_instance = response.data

    created_instance_id = response_instance.pop("id")
    assert created_instance_id
    created_instance = WorkerInstruction.objects.get(id=created_instance_id)

    response_instructions = response_instance.pop("data")
    assert response_instructions
    if response_instructions:
        assert len(created_instance.data) == len(response_instructions)
        instruction1 = 0
        response_instruction_1 = response_instructions[instruction1]
        assert response_instruction_1
        if response_instruction_1:
            created_instance_1i_type = created_instance.data[instruction1].get(TYPE)
            del response_instructions[instruction1]
            assert response_instruction_1.pop(TYPE) == created_instance_1i_type == media_type
            created_instance_1i_basename = created_instance.data[instruction1].get(BASENAME)
            assert response_instruction_1.pop(BASENAME) == created_instance_1i_basename
        assert not response_instruction_1
    assert not response_instructions


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("media_type", WORKER_INSTRUCTION_MEDIA_TYPES)
def test__gallery_media_fields__response_data(
    api_client, monkeypatch, r_cu, get_project_fi, new_worker_instruction_data, media_type
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)

    MEDIA_FIELD = {TYPE: media_type, BASENAME: "123123123.jpeg"}
    instructions_data = [{TYPE: GALLERY, VALUES: [MEDIA_FIELD]}]
    project = get_project_fi(company=r_cu.company)
    data = new_worker_instruction_data(project=project, instructions_data=instructions_data)
    response = __get_response(api_client, data=data, user=r_cu.user)
    response_instance = response.data

    created_instance_id = response_instance.pop("id")
    assert created_instance_id
    created_instance = WorkerInstruction.objects.get(id=created_instance_id)

    response_instructions = response_instance.pop("data")
    gallery_instruction_index, media_instruction_index = 0, 0
    assert response_instructions
    if response_instructions:
        assert len(created_instance.data) == len(response_instructions)
        response_gallery_instruction = response_instructions[gallery_instruction_index]
        assert response_gallery_instruction

        assert (
            response_gallery_instruction.pop(TYPE)
            == created_instance.data[gallery_instruction_index].get(TYPE)
            == GALLERY
        )
        response_media_instruction = response_gallery_instruction.pop(VALUES)[media_instruction_index]
        assert not response_gallery_instruction
        created_instance_gallery_instruction = created_instance.data[gallery_instruction_index]
        created_instance_media_instruction = created_instance_gallery_instruction[VALUES][
            media_instruction_index
        ]

        assert (
            response_media_instruction.pop(TYPE) == media_type == created_instance_media_instruction.get(TYPE)
        )
        assert response_media_instruction.pop(BASENAME) == created_instance_media_instruction.get(BASENAME)

        assert not response_media_instruction
    assert response_instructions == [{}]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("media_type", ["image"])
def test__not_media_type_no_values__response_data(
    api_client, monkeypatch, r_cu, get_project_fi, new_worker_instruction_data, media_type
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)

    instructions_data = [{TYPE: media_type, BASENAME: "123123123.jpeg"}]
    project = get_project_fi(company=r_cu.company)
    data = new_worker_instruction_data(project=project, instructions_data=instructions_data)
    response = __get_response(api_client, data=data, user=r_cu.user)
    response_instance = response.data

    created_instance_id = response_instance.pop("id")
    assert created_instance_id
    created_instance = WorkerInstruction.objects.get(id=created_instance_id)

    response_instructions = response_instance.pop("data")
    assert response_instructions
    if response_instructions:
        assert len(created_instance.data) == len(response_instructions)
        instruction1 = 0
        response_instruction_1 = response_instructions[instruction1]
        assert response_instruction_1
        if response_instruction_1:
            created_instance_1i_type = created_instance.data[instruction1].get(TYPE)
            del response_instructions[instruction1]
            assert response_instruction_1.pop(TYPE) == created_instance_1i_type == media_type
            created_instance_1i_basename = created_instance.data[instruction1].get(BASENAME)
            assert response_instruction_1.pop(BASENAME) == created_instance_1i_basename
            assert VALUES not in response_instruction_1
        assert not response_instruction_1
    assert not response_instructions
