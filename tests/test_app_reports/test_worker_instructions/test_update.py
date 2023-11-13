import functools

import pytest
import requests
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_update
from accounts.models import USER_IS_BLOCKED, USER_IS_DELETED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from tests.mocked_instances import MockResponse
from projects.models.project import PROJECT_STATUS_MUST_BE_SETUP_OR_ACTIVE
from ma_saas.constants.system import TYPE, TITLE, VALUES, BASENAME, FILE_LINK
from ma_saas.constants.company import CUR, CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from ma_saas.constants.project import (
    ACTIVE_OR_SETUP_PROJECT_STATUS,
    NOT_ACTIVE_OR_SETUP_PROJECT_STATUS,
    ProjectStatus,
)
from clients.policies.interface import Policies
from clients.objects_store.views import get_media_link
from proxy.views.media_permission import WORKER_INSTRUCTION
from companies.models.company_user import CompanyUser
from reports.models.worker_instruction import WorkerInstruction
from ma_saas.constants.worker_instruction import (
    GALLERY,
    WORKER_INSTRUCTION_MEDIA_TYPES,
    WorkerInstructionMediaType,
)

User = get_user_model()

__get_response = functools.partial(request_response_update, path="/api/v1/worker-instructions/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("project_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, {}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accepted_owner__without_policy__success(
    api_client, mock_policies_false, r_cu, get_worker_instruction_fi
):
    instance = get_worker_instruction_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, {}, r_cu.user)
    assert response.data.get("id")


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted__company_owner__without_policy__fail(
    api_client, mock_policies_false, get_cu_fi, get_worker_instruction_fi, status
):
    r_cu = get_cu_fi(status=status, role=CUR.OWNER)
    instance = get_worker_instruction_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__accepted__not_owner__without_policy__fail(
    api_client, mock_policies_false, get_cu_fi, get_worker_instruction_fi, role
):
    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)
    instance = get_worker_instruction_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__accepted__not_owner__with_policy__success(
    api_client, monkeypatch, get_cu_fi, get_worker_instruction_fi, role
):
    r_cu = get_cu_fi(status=CUS.ACCEPT.value, role=role)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    instance = get_worker_instruction_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, {}, r_cu.user)
    assert response.data.get("id")


@pytest.mark.parametrize("status", NOT_ACTIVE_OR_SETUP_PROJECT_STATUS)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__update_if_status_not_setup_or_active__fail(
    api_client,
    mock_policies_false,
    r_cu,
    get_project_fi,
    get_worker_instruction_fi,
    status,
):
    project = get_project_fi(company=r_cu.company, status=status)
    instance = get_worker_instruction_fi(project=project)

    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=ValidationError)
    assert response.data == {"non_field_errors": [PROJECT_STATUS_MUST_BE_SETUP_OR_ACTIVE]}


@pytest.mark.parametrize("status", ACTIVE_OR_SETUP_PROJECT_STATUS)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__update_if_status_setup__success(
    api_client, mock_policies_false, r_cu, get_project_fi, get_worker_instruction_fi, status
):
    project = get_project_fi(company=r_cu.company, status=status)
    instance = get_worker_instruction_fi(project=project)
    response = __get_response(api_client, instance.id, data={}, user=r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("is_user", "field", "has_object_policy", "err_text"),
    (
        (True, "is_blocked", True, NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_BLOCKED)),
        (True, "is_deleted", True, NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_DELETED)),
        (False, "is_deleted", True, REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY),
        (True, "is_blocked", False, NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_BLOCKED)),
        (True, "is_deleted", False, NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_DELETED)),
    ),
)
def test__not_ta__cu__fail(
    api_client, monkeypatch, r_cu, get_worker_instruction_fi, has_object_policy, is_user, field, err_text
):
    __get_target_policies_return = [r_cu.company.id] if has_object_policy else []
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: __get_target_policies_return)

    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    instance = get_worker_instruction_fi(company=r_cu.company)
    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()
    else:
        setattr(r_cu, field, True)
        r_cu.save()
    response = __get_response(
        api_client, instance.id, {}, r_cu.user, status_codes={PermissionDenied, NotFound}
    )
    assert response.data == {"detail": err_text}, f"response.data = {response.data}"


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_project__fail(
    api_client, mock_policies_false, r_cu, get_project_fi, get_worker_instruction_fi
):
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    project.is_deleted = True
    project.save()
    instance = get_worker_instruction_fi(project=project)
    response = __get_response(api_client, instance.id, {}, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data__via_project_scheme(
    api_client,
    mock_policies_false,
    r_cu,
    get_project_fi,
    get_project_scheme_fi,
    get_worker_instruction_fi,
    new_worker_instruction_data,
):
    instruction_data = [
        {TYPE: WorkerInstructionMediaType.DOCUMENT, VALUES: ["e0kj309230e0203"], BASENAME: "123123123.jpeg"},
        {TYPE: "text", VALUES: ["some fries motherfucker"], TITLE: "Samuel Mc'Donald"},
        {TYPE: "list", VALUES: ["golang", "python", "java"], TITLE: "lng to learn"},
    ]
    project_scheme = get_project_scheme_fi(company=r_cu.company)
    instance = get_worker_instruction_fi(project_scheme=project_scheme)
    assert instance.data == []
    data = new_worker_instruction_data(project_scheme=project_scheme, instructions_data=instruction_data)
    response = __get_response(api_client, instance_id=instance.id, data=data, user=r_cu.user)
    updated_instance = WorkerInstruction.objects.get(id=instance.id)
    response_instance = response.data
    updated_instance_id = response_instance.pop("id")
    assert updated_instance_id
    assert response_instance.pop("project_scheme") == {
        "id": instance.project_scheme.id,
        "title": instance.project_scheme.title,
        "color": instance.project_scheme.color,
    }
    assert response_instance.pop("title") is None
    assert response_instance.pop("project_variables_keys") == []
    assert response_instance.pop("project") == {"id": instance.project_scheme.project.id}
    response_instructions = response_instance.pop("data")
    assert response_instructions
    if response_instructions:
        assert len(updated_instance.data) == len(response_instructions) == 3 != len(instance.data)
        assert response_instructions != updated_instance.data
        assert len(response_instructions[0]) == 4
        instruction1, instruction2, instruction3 = 0, 1, 2
        response_instruction_3 = response_instructions[instruction3]
        assert response_instruction_3
        if response_instruction_3:
            updated_instance_3i_type = updated_instance.data[instruction3].get(TYPE)
            del response_instructions[instruction3]
            assert response_instruction_3.pop(TYPE) == updated_instance_3i_type
            updated_instance_3i_title = updated_instance.data[instruction3].get(TITLE)
            assert response_instruction_3.pop(TITLE) == updated_instance_3i_title
            assert response_instruction_3.pop(VALUES) == updated_instance.data[instruction3].get(VALUES)
        assert not response_instruction_3
        response_instruction_2 = response_instructions[instruction2]
        assert response_instruction_2
        if response_instruction_2:
            updated_instance_2i_type = updated_instance.data[instruction2].get(TYPE)
            del response_instructions[instruction2]
            assert response_instruction_2.pop(TYPE) == updated_instance_2i_type
            updated_instance_2i_values = updated_instance.data[instruction2].get(VALUES)
            assert len(updated_instance_2i_values) == 1
            assert response_instruction_2.pop(VALUES) == updated_instance_2i_values
            updated_instance_2i_title = updated_instance.data[instruction2].get(TITLE)
            assert response_instruction_2.pop(TITLE) == updated_instance_2i_title
        assert not response_instruction_2
        response_instruction_1 = response_instructions[instruction1]
        assert response_instruction_1
        if response_instruction_1:
            updated_instance_1i_type = updated_instance.data[instruction1].get(TYPE)
            del response_instructions[instruction1]
            assert response_instruction_1.pop(TYPE) == updated_instance_1i_type
            updated_instance_1i_basename = updated_instance.data[instruction1].get(BASENAME)
            assert response_instruction_1.pop(BASENAME) == updated_instance_1i_basename
            updated_instance_1i_values = updated_instance.data[instruction1].get(VALUES)
            assert len(updated_instance_1i_values) == 1
            assert response_instruction_1.pop(VALUES) == updated_instance_1i_values
            updated_instance_1i_link = updated_instance.data[instruction1].get(VALUES)[0]
            assert response_instruction_1.pop(FILE_LINK) == get_media_link(
                instance_name=WORKER_INSTRUCTION,
                model_id=updated_instance.id,
                objstore_id=updated_instance_1i_link,
            )
        assert not response_instruction_1
    assert not response_instructions
    assert not response_instance


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data__via_project(
    api_client,
    mock_policies_false,
    r_cu,
    get_project_fi,
    get_worker_instruction_fi,
    new_worker_instruction_data,
):
    instruction_data = [
        {TYPE: WorkerInstructionMediaType.DOCUMENT, VALUES: ["e0kj309230e0203"], BASENAME: "123123123.jpeg"},
        {TYPE: "text", VALUES: ["some fries motherfucker"], TITLE: "Samuel Mc'Donald"},
        {TYPE: "list", VALUES: ["golang", "python", "java"], TITLE: "lng to learn"},
    ]
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance = get_worker_instruction_fi(project=project)
    assert instance.data == []
    data = new_worker_instruction_data(project=project, instructions_data=instruction_data)
    response = __get_response(api_client, instance_id=instance.id, data=data, user=r_cu.user)
    updated_instance = WorkerInstruction.objects.get(id=instance.id)
    response_instance = response.data
    updated_instance_id = response_instance.pop("id")
    assert updated_instance_id
    assert response_instance.pop("title") is None
    assert response_instance.pop("project_scheme") is None
    assert response_instance.pop("project") == {"id": project.id}
    assert response_instance.pop("project_variables_keys") == []
    response_instructions = response_instance.pop("data")
    assert response_instructions
    if response_instructions:
        assert len(updated_instance.data) == len(response_instructions) == 3 != len(instance.data)
        assert response_instructions != updated_instance.data
        assert len(response_instructions[0]) == 4
        instruction1, instruction2, instruction3 = 0, 1, 2
        response_instruction_3 = response_instructions[instruction3]
        assert response_instruction_3
        if response_instruction_3:
            updated_instance_3i_type = updated_instance.data[instruction3].get(TYPE)
            del response_instructions[instruction3]
            assert response_instruction_3.pop(TYPE) == updated_instance_3i_type
            updated_instance_3i_title = updated_instance.data[instruction3].get(TITLE)
            assert response_instruction_3.pop(TITLE) == updated_instance_3i_title
            assert response_instruction_3.pop(VALUES) == updated_instance.data[instruction3].get(VALUES)
        assert not response_instruction_3
        response_instruction_2 = response_instructions[instruction2]
        assert response_instruction_2
        if response_instruction_2:
            updated_instance_2i_type = updated_instance.data[instruction2].get(TYPE)
            del response_instructions[instruction2]
            assert response_instruction_2.pop(TYPE) == updated_instance_2i_type
            updated_instance_2i_values = updated_instance.data[instruction2].get(VALUES)
            assert len(updated_instance_2i_values) == 1
            assert response_instruction_2.pop(VALUES) == updated_instance_2i_values
            updated_instance_2i_title = updated_instance.data[instruction2].get(TITLE)
            assert response_instruction_2.pop(TITLE) == updated_instance_2i_title
        assert not response_instruction_2
        response_instruction_1 = response_instructions[instruction1]
        assert response_instruction_1
        if response_instruction_1:
            updated_instance_1i_type = updated_instance.data[instruction1].get(TYPE)
            del response_instructions[instruction1]
            assert response_instruction_1.pop(TYPE) == updated_instance_1i_type
            updated_instance_1i_basename = updated_instance.data[instruction1].get(BASENAME)
            assert response_instruction_1.pop(BASENAME) == updated_instance_1i_basename
            updated_instance_1i_values = updated_instance.data[instruction1].get(VALUES)
            assert len(updated_instance_1i_values) == 1
            assert response_instruction_1.pop(VALUES) == updated_instance_1i_values
            updated_instance_1i_link = updated_instance.data[instruction1].get(VALUES)[0]
            assert response_instruction_1.pop(FILE_LINK) == get_media_link(
                instance_name=WORKER_INSTRUCTION,
                model_id=updated_instance.id,
                objstore_id=updated_instance_1i_link,
            )
        assert not response_instruction_1
    assert not response_instructions
    assert not response_instance


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("media_type", WORKER_INSTRUCTION_MEDIA_TYPES)
def test__update_media_fields__response_data(
    monkeypatch,
    api_client,
    mock_policies_false,
    r_cu,
    get_project_fi,
    get_worker_instruction_fi,
    new_worker_instruction_data,
    media_type,
):
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    instruction_data = [{TYPE: media_type, BASENAME: "123123123.jpeg"}]
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance = get_worker_instruction_fi(project=project)
    assert instance.data == []
    data = new_worker_instruction_data(project=project, instructions_data=instruction_data)
    response = __get_response(api_client, instance_id=instance.id, data=data, user=r_cu.user)
    updated_instance = WorkerInstruction.objects.get(id=instance.id)
    response_instance = response.data
    updated_instance_id = response_instance.pop("id")
    assert updated_instance_id
    assert response_instance.pop("title") is None
    assert response_instance.pop("project_variables_keys") == []
    assert response_instance.pop("project_scheme") is None
    assert response_instance.pop("project") == {"id": project.id}
    response_instructions = response_instance.pop("data")
    assert response_instructions
    if response_instructions:
        assert len(updated_instance.data) == len(response_instructions) == 1 != len(instance.data)
        assert len(response_instructions[0]) == 2
        instruction1 = 0
        response_instruction_1 = response_instructions[instruction1]
        assert response_instruction_1
        if response_instruction_1:
            updated_instance_1i_type = updated_instance.data[instruction1].get(TYPE)
            del response_instructions[instruction1]
            assert response_instruction_1.pop(TYPE) == updated_instance_1i_type
            updated_instance_1i_basename = updated_instance.data[instruction1].get(BASENAME)
            assert response_instruction_1.pop(BASENAME) == updated_instance_1i_basename
            updated_instance_1i_values = updated_instance.data[instruction1].get(VALUES)
            assert updated_instance_1i_values is None
        assert not response_instruction_1
    assert not response_instructions
    assert not response_instance


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("media_type", WORKER_INSTRUCTION_MEDIA_TYPES)
def test__gallery_fields__response_data(
    monkeypatch,
    api_client,
    mock_policies_false,
    r_cu,
    get_project_fi,
    get_worker_instruction_fi,
    new_worker_instruction_data,
    media_type,
):
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    media_field_data = {TYPE: media_type, BASENAME: "123123123.jpeg"}
    instructions_data = [{TYPE: GALLERY, VALUES: [media_field_data]}]
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance = get_worker_instruction_fi(project=project)
    assert instance.data == []
    data = new_worker_instruction_data(project=project, instructions_data=instructions_data)
    response = __get_response(api_client, instance_id=instance.id, data=data, user=r_cu.user)
    updated_instance = WorkerInstruction.objects.get(id=instance.id)
    response_instance = response.data
    updated_instance_id = response_instance.pop("id")
    assert updated_instance_id
    assert response_instance.pop("title") is None
    assert response_instance.pop("project_scheme") is None
    assert response_instance.pop("project") == {"id": project.id}
    gallery_instruction_index, media_instruction_index = 0, 0
    response_instructions = response_instance.pop("data")
    assert response_instructions
    if response_instructions:
        assert len(updated_instance.data) == len(response_instructions) == 1 != len(instance.data)
        assert len(response_instructions[0]) == 2
        assert len(response_instructions[0][VALUES][0]) == 2
        instruction1 = 0
        response_instruction_1 = response_instructions[instruction1]
        assert response_instruction_1
        if response_instruction_1:
            assert len(updated_instance.data) == len(response_instructions)
            response_gallery_instruction = response_instructions[gallery_instruction_index]
            assert response_gallery_instruction
            assert GALLERY == response_gallery_instruction.pop(TYPE)
            assert GALLERY == updated_instance.data[gallery_instruction_index].get(TYPE)
            response_media_instruction = response_gallery_instruction.pop(VALUES)[media_instruction_index]
            assert not response_gallery_instruction
            created_instance_gallery_instruction = updated_instance.data[gallery_instruction_index]
            created_instance_media_instruction = created_instance_gallery_instruction[VALUES][
                media_instruction_index
            ]
            assert response_media_instruction.pop(TYPE) == media_type
            assert media_type == created_instance_media_instruction.get(TYPE)
            assert response_media_instruction.pop(BASENAME) == created_instance_media_instruction.get(
                BASENAME
            )
            assert not response_media_instruction
        assert response_instructions == [{}]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("media_type", ["image"])
def test__not_media_type_no_values__response_data(
    monkeypatch,
    api_client,
    mock_policies_false,
    r_cu,
    get_project_fi,
    get_worker_instruction_fi,
    new_worker_instruction_data,
    media_type,
):
    monkeypatch.setattr(requests, "get", MockResponse, raising=True)
    instruction_data = [{TYPE: media_type, BASENAME: "123123123.jpeg"}]
    project = get_project_fi(company=r_cu.company, status=ProjectStatus.SETUP.value)
    instance = get_worker_instruction_fi(project=project)
    assert instance.data == []
    data = new_worker_instruction_data(project=project, instructions_data=instruction_data)
    response = __get_response(api_client, instance_id=instance.id, data=data, user=r_cu.user)
    updated_instance = WorkerInstruction.objects.get(id=instance.id)
    response_instance = response.data
    updated_instance_id = response_instance.pop("id")
    assert updated_instance_id
    assert response_instance.pop("title") is None
    assert response_instance.pop("project_scheme") is None
    assert response_instance.pop("project") == {"id": project.id}
    assert response_instance.pop("project_variables_keys") == []
    response_instructions = response_instance.pop("data")
    assert response_instructions
    if response_instructions:
        assert len(updated_instance.data) == len(response_instructions) == 1 != len(instance.data)
        assert response_instructions == updated_instance.data
        assert len(response_instructions[0]) == 2
        instruction1 = 0
        response_instruction_1 = response_instructions[instruction1]
        assert response_instruction_1
        if response_instruction_1:
            updated_instance_1i_type = updated_instance.data[instruction1].get(TYPE)
            del response_instructions[instruction1]
            assert response_instruction_1.pop(TYPE) == updated_instance_1i_type
            updated_instance_1i_basename = updated_instance.data[instruction1].get(BASENAME)
            assert response_instruction_1.pop(BASENAME) == updated_instance_1i_basename
            assert VALUES not in updated_instance.data[instruction1]
            assert VALUES not in response_instruction_1
        assert not response_instruction_1
    assert not response_instructions
    assert not response_instance
