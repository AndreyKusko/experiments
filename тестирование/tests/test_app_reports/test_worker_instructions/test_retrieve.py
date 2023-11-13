import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, NotAuthenticated, PermissionDenied

from tests.utils import request_response_get
from accounts.models import USER_IS_BLOCKED, USER_IS_DELETED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from ma_saas.constants.system import TYPE, TITLE, VALUES, BASENAME, FILE_LINK
from ma_saas.constants.company import CUR, NOT_ACCEPT_CUS
from clients.policies.interface import Policies
from companies.models.company_user import CompanyUser
from ma_saas.constants.worker_instruction import WorkerInstructionMediaType

User = get_user_model()

__get_response = functools.partial(request_response_get, path="/api/v1/worker-instructions/")


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("processed_report_form_fi")])
def test__anonymous_user__fail(api_client, instance):
    response = __get_response(api_client, instance.id, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_worker_fi")])
def test__related_pt_worker__without_policy__without_reservation__fail(
    api_client, mock_policies_false, r_cu, get_pt_worker_fi, get_worker_instruction_fi
):
    ptw = get_pt_worker_fi(company_user=r_cu)
    instance = get_worker_instruction_fi(project=ptw.project_territory.project)
    response = __get_response(api_client, instance.id, r_cu.user)
    assert response.data.get("id")


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_worker_fi")])
def test__related_pt_worker__without_policy__with_reservation__success(
    api_client,
    mock_policies_false,
    r_cu,
    get_pt_worker_fi,
    get_reservation_fi,
    get_worker_instruction_fi,
):
    ptw = get_pt_worker_fi(company_user=r_cu)
    get_reservation_fi(project_territory_worker=ptw)
    instance = get_worker_instruction_fi(project=ptw.project_territory.project)
    response = __get_response(api_client, instance.id, r_cu.user)
    assert response.data["id"]


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__manager_without_permission__fail(
    monkeypatch,
    api_client,
    mock_policies_false,
    r_cu,
    get_worker_instruction_fi,
):
    instance = get_worker_instruction_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.xfail
@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accepted_contractor_owner__fail(
    api_client, mock_policies_false, get_cu_fi, get_worker_instruction_fi, status
):
    r_cu = get_cu_fi(status=status.value, role=CUR.OWNER)
    instance = get_worker_instruction_fi(company=r_cu.company)
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


@pytest.mark.xfail
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__deleted_cu__fail(api_client, monkeypatch, mock_policies_false, r_cu, get_worker_instruction_fi):
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    instance = get_worker_instruction_fi(company=r_cu.company)
    r_cu.is_deleted = True
    r_cu.save()
    response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
    assert response.data["detail"] == NotFound.default_detail


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
    api_client, monkeypatch, r_cu, get_project_fi, has_object_policy, is_user, field, err_text
):
    __get_target_policies_return = [r_cu.company.id] if has_object_policy else []
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: __get_target_policies_return)

    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    instance = get_project_fi(company=r_cu.company)
    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()
        response = __get_response(api_client, instance.id, r_cu.user, status_codes=PermissionDenied)
        assert response.data == {"detail": err_text}
    else:
        setattr(r_cu, field, True)
        r_cu.save()
        response = __get_response(api_client, instance.id, r_cu.user, status_codes=NotFound)
        assert response.data["detail"] == NotFound.default_detail


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data__via_project(api_client, mock_policies_false, r_cu, get_worker_instruction_fi):

    instruction_data = [
        {TYPE: WorkerInstructionMediaType.DOCUMENT, VALUES: ["e0kj309230e0203"], BASENAME: "123123123.jpeg"},
        {TYPE: "text", VALUES: ["some fries motherfucker"], TITLE: "Samuel Mc'Donald"},
        {TYPE: "list", VALUES: ["golang", "python", "java"], TITLE: "lng to learn"},
    ]
    instance = get_worker_instruction_fi(company=r_cu.company, instructions_data=instruction_data)
    response = __get_response(api_client, instance.id, r_cu.user)
    response_instance = response.data

    created_instance_id = response_instance.pop("id")
    assert created_instance_id

    assert response_instance.pop("title") is None
    assert response_instance.pop("project_scheme") is None
    assert response_instance.pop("project_variables_keys") == []
    assert response_instance.pop("project") == {"id": instance.project.id}

    response_instructions = response_instance.pop("data")
    instance.data = instance.data
    assert response_instructions
    if response_instructions:
        assert len(instance.data) == len(response_instructions) == 3
        # assert response_instructions == instance.data
        assert response_instructions != instance
        assert len(response_instructions[0]) == 4

        instruction1, instruction2, instruction3 = 0, 1, 2

        response_instruction_3 = response_instructions[instruction3]
        assert response_instruction_3
        if response_instruction_3:
            created_instance_3i_type = instance.data[instruction3].get(TYPE)
            del response_instructions[instruction3]
            assert response_instruction_3.pop(TYPE) == created_instance_3i_type
            created_instance_3i_title = instance.data[instruction3].get(TITLE)
            assert response_instruction_3.pop(TITLE) == created_instance_3i_title
            assert response_instruction_3.pop(VALUES) == instance.data[instruction3].get(VALUES)

        assert not response_instruction_3

        response_instruction_2 = response_instructions[instruction2]
        assert response_instruction_2
        if response_instruction_2:
            created_instance_2i_type = instance.data[instruction2].get(TYPE)
            del response_instructions[instruction2]
            assert response_instruction_2.pop(TYPE) == created_instance_2i_type
            created_instance_2i_values = instance.data[instruction2].get(VALUES)
            assert len(created_instance_2i_values) == 1
            assert response_instruction_2.pop(VALUES) == created_instance_2i_values
            created_instance_2i_title = instance.data[instruction2].get(TITLE)
            assert response_instruction_2.pop(TITLE) == created_instance_2i_title
        assert not response_instruction_2

        response_instruction_1 = response_instructions[instruction1]
        assert response_instruction_1
        if response_instruction_1:
            created_instance_1i_type = instance.data[instruction1].get(TYPE)
            del response_instructions[instruction1]
            assert response_instruction_1.pop(TYPE) == created_instance_1i_type
            created_instance_1i_basename = instance.data[instruction1].get(BASENAME)
            assert response_instruction_1.pop(BASENAME) == created_instance_1i_basename
            created_instance_1i_values = instance.data[instruction1].get(VALUES)
            assert len(created_instance_1i_values) == 1
            assert response_instruction_1.pop(VALUES) == created_instance_1i_values
            assert response_instruction_1.pop(FILE_LINK)
        assert not response_instruction_1
    assert not response_instructions

    assert not response_instance


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__response_data__via_project_scheme(
    api_client, mock_policies_false, r_cu, get_worker_instruction_fi, get_project_scheme_fi
):

    instruction_data = [
        {TYPE: WorkerInstructionMediaType.DOCUMENT, VALUES: ["e0kj309230e0203"], BASENAME: "123123123.jpeg"},
        {TYPE: "text", VALUES: ["some fries motherfucker"], TITLE: "Samuel Mc'Donald"},
        {TYPE: "list", VALUES: ["golang", "python", "java"], TITLE: "lng to learn"},
    ]
    project_scheme = get_project_scheme_fi(company=r_cu.company)
    instance = get_worker_instruction_fi(project_scheme=project_scheme, instructions_data=instruction_data)
    response = __get_response(api_client, instance.id, r_cu.user)
    response_instance = response.data

    created_instance_id = response_instance.pop("id")
    assert created_instance_id

    assert response_instance.pop("project_scheme") == {
        "id": project_scheme.id,
        "title": project_scheme.title,
        "color": project_scheme.color,
    }
    assert response_instance.pop("project") == {
        "id": project_scheme.project.id,
    }
    assert response_instance.pop("title") is None
    assert response_instance.pop("project_variables_keys") == []

    response_instructions = response_instance.pop("data")
    instance.data = instance.data
    assert response_instructions
    if response_instructions:
        assert len(instance.data) == len(response_instructions) == 3
        # assert response_instructions == instance.data
        assert response_instructions != instance
        assert len(response_instructions[0]) == 4

        instruction1, instruction2, instruction3 = 0, 1, 2

        response_instruction_3 = response_instructions[instruction3]
        assert response_instruction_3
        if response_instruction_3:
            created_instance_3i_type = instance.data[instruction3].get(TYPE)
            del response_instructions[instruction3]
            assert response_instruction_3.pop(TYPE) == created_instance_3i_type
            created_instance_3i_title = instance.data[instruction3].get(TITLE)
            assert response_instruction_3.pop(TITLE) == created_instance_3i_title
            assert response_instruction_3.pop(VALUES) == instance.data[instruction3].get(VALUES)

        assert not response_instruction_3

        response_instruction_2 = response_instructions[instruction2]
        assert response_instruction_2
        if response_instruction_2:
            created_instance_2i_type = instance.data[instruction2].get(TYPE)
            del response_instructions[instruction2]
            assert response_instruction_2.pop(TYPE) == created_instance_2i_type
            created_instance_2i_values = instance.data[instruction2].get(VALUES)
            assert len(created_instance_2i_values) == 1
            assert response_instruction_2.pop(VALUES) == created_instance_2i_values
            created_instance_2i_title = instance.data[instruction2].get(TITLE)
            assert response_instruction_2.pop(TITLE) == created_instance_2i_title
        assert not response_instruction_2

        response_instruction_1 = response_instructions[instruction1]
        assert response_instruction_1
        if response_instruction_1:
            created_instance_1i_type = instance.data[instruction1].get(TYPE)
            del response_instructions[instruction1]
            assert response_instruction_1.pop(TYPE) == created_instance_1i_type
            created_instance_1i_basename = instance.data[instruction1].get(BASENAME)
            assert response_instruction_1.pop(BASENAME) == created_instance_1i_basename
            created_instance_1i_values = instance.data[instruction1].get(VALUES)
            assert len(created_instance_1i_values) == 1
            assert response_instruction_1.pop(VALUES) == created_instance_1i_values
            assert response_instruction_1.pop(FILE_LINK)
        assert not response_instruction_1
    assert not response_instructions

    assert not response_instance
