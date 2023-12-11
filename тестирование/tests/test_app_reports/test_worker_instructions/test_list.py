import json
import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from tests.utils import request_response_list
from accounts.models import USER_IS_BLOCKED, NOT_TA_R_U__DELETED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from ma_saas.constants.system import TYPE, TITLE, VALUES, BASENAME, FILE_LINK
from ma_saas.constants.company import CUR, CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from clients.policies.interface import Policies
from companies.models.company_user import CompanyUser
from ma_saas.constants.worker_instruction import WorkerInstructionMediaType

User = get_user_model()

__get_response = functools.partial(request_response_list, path="/api/v1/worker-instructions/")


def test__anonymous_user__fail(api_client):
    response = __get_response(api_client, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


def test__user_without_companies__fail(api_client, mock_policies_false, user_fi: User):
    response = __get_response(api_client, user_fi)
    assert not response.data


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("qty", (1, 3))
def test__accepted_owner__success(api_client, mock_policies_false, get_worker_instruction_fi, r_cu, qty):
    [get_worker_instruction_fi(company=r_cu.company) for _ in range(qty)]
    response = __get_response(api_client, r_cu.user)
    assert len(response.data) == qty


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
@pytest.mark.parametrize("qty", (3,))
def test__not_accepted_owner__fail(
    api_client, monkeypatch, get_worker_instruction_fi, get_cu_fi, status, qty
):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    instances = [get_worker_instruction_fi(company=r_cu.company) for _ in range(qty)]
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [i.id for i in instances])
    response = __get_response(api_client, r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
@pytest.mark.parametrize("qty", (3,))
def test__not_owner__without_policies__fail(
    api_client, mock_policies_false, get_worker_instruction_fi, get_cu_fi, role, qty
):

    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    [get_worker_instruction_fi(company=r_cu.company) for _ in range(qty)]
    response = __get_response(api_client, r_cu.user)
    assert response.data == []


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
@pytest.mark.parametrize("qty", (3,))
def test__not_owner__with_policies__success(
    api_client, monkeypatch, get_worker_instruction_fi, get_cu_fi, role, qty
):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])

    [get_worker_instruction_fi(company=r_cu.company) for _ in range(qty)]

    response = __get_response(api_client, r_cu.user)
    assert len(response.data) == qty


@pytest.mark.xfail
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("is_user", "field", "err_text"),
    (
        (True, "is_blocked", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_BLOCKED)),
        (True, "is_deleted", NOT_TA_R_U__DELETED),
        (False, "is_deleted", REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY),
    ),
)
@pytest.mark.parametrize("is_policy", [True, False])
def test__not_ta__cu__fail(
    api_client, monkeypatch, r_cu, get_worker_instruction_fi, is_policy, is_user, field, err_text
):
    get_worker_instruction_fi(company=r_cu.company)
    __get_target_policies_return = [r_cu.company.id] if is_policy else []
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: __get_target_policies_return)

    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()

        response = __get_response(api_client, r_cu.user, status_codes=PermissionDenied)
        assert response.data == {"detail": err_text}

    else:
        setattr(r_cu, field, True)
        r_cu.save()

        response = __get_response(api_client, r_cu.user)
        assert response.data == []


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("qty", (1, 3))
def test__response_data__via_project_scheme(
    api_client, mock_policies_false, get_worker_instruction_fi, get_project_scheme_fi, r_cu, qty
):
    instructions_data = [
        {TYPE: WorkerInstructionMediaType.DOCUMENT, VALUES: ["e0kj309230e0203"], BASENAME: "123123123.jpeg"},
        {TYPE: "text", VALUES: ["some fries motherfucker"], TITLE: "Samuel Mc'Donald"},
        {TYPE: "list", VALUES: ["golang", "python", "java"], TITLE: "lng to learn"},
    ]
    instances = []
    for _ in range(qty):
        project_scheme = get_project_scheme_fi(company=r_cu.company)
        instances.append(
            get_worker_instruction_fi(project_scheme=project_scheme, instructions_data=instructions_data)
        )

    instances.reverse()

    response = __get_response(api_client, r_cu.user)
    for index, response_instance in enumerate(response.data):

        created_instance_id = response_instance.pop("id")
        assert created_instance_id
        assert response_instance.pop("title") is None
        assert response_instance.pop("project_variables_keys") == []
        assert response_instance.pop("project_scheme") == {
            "id": instances[index].project_scheme.id,
            "title": instances[index].project_scheme.title,
            "color": instances[index].project_scheme.color,
        }
        assert response_instance.pop("project") == {
            "id": instances[index].project_scheme.project.id,
        }

        response_instructions = response_instance.pop("data")
        instances[index].data = instances[index].data

        assert response_instructions
        if response_instructions:
            assert len(response_instructions) == len(instances[index].data) == 3
            # assert response_instructions == instances[index].data
            # assert response_instructions == instructions_data
            assert instances[index].data == instructions_data
            assert len(response_instructions[0]) == 4

            instruction1, instruction2, instruction3 = 0, 1, 2

            response_instruction_3 = response_instructions[instruction3]
            assert response_instruction_3
            if response_instruction_3:
                created_instance_3i_type = instances[index].data[instruction3].get(TYPE)
                del response_instructions[instruction3]
                assert response_instruction_3.pop(TYPE) == created_instance_3i_type
                created_instance_3i_title = instances[index].data[instruction3].get(TITLE)
                assert response_instruction_3.pop(TITLE) == created_instance_3i_title
                assert response_instruction_3.pop(VALUES) == instances[index].data[instruction3].get(VALUES)

            assert not response_instruction_3

            response_instruction_2 = response_instructions[instruction2]
            assert response_instruction_2
            if response_instruction_2:
                created_instance_2i_type = instances[index].data[instruction2].get(TYPE)
                del response_instructions[instruction2]
                assert response_instruction_2.pop(TYPE) == created_instance_2i_type
                created_instance_2i_values = instances[index].data[instruction2].get(VALUES)
                assert len(created_instance_2i_values) == 1
                assert response_instruction_2.pop(VALUES) == created_instance_2i_values
                created_instance_2i_title = instances[index].data[instruction2].get(TITLE)
                assert response_instruction_2.pop(TITLE) == created_instance_2i_title
            assert not response_instruction_2

            response_instruction_1 = response_instructions[instruction1]
            assert response_instruction_1
            if response_instruction_1:
                created_instance_1i_type = instances[index].data[instruction1].get(TYPE)
                del response_instructions[instruction1]
                assert response_instruction_1.pop(TYPE) == created_instance_1i_type
                created_instance_1i_basename = instances[index].data[instruction1].get(BASENAME)
                assert response_instruction_1.pop(BASENAME) == created_instance_1i_basename
                created_instance_1i_values = instances[index].data[instruction1].get(VALUES)
                assert len(created_instance_1i_values) == 1
                assert response_instruction_1.pop(VALUES) == created_instance_1i_values
                assert response_instruction_1.pop(FILE_LINK)
            assert not response_instruction_1
        assert not response_instructions

        assert not response_instance
