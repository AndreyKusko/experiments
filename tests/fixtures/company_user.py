import typing as tp
from typing import Callable

import pytest
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from tests.utils import get_random_email, get_random_phone
from companies.models.company import Company
from ma_saas.constants.company import CUR, CUS
from companies.models.company_user import CompanyUser
from clients.billing.interfaces.worker import WorkerBilling

User = get_user_model()


@pytest.fixture
def new_company_user_data(get_user_fi, get_company_fi) -> Callable:
    def return_data(
        user: tp.Optional[User] = None,
        company: tp.Optional[Company] = None,
        role: tp.Optional[str] = CUR.WORKER,
        status: tp.Optional[str] = CUS.ACCEPT.value,
        _is_relations_ids: bool = True,
    ) -> tp.Dict[str, tp.Any]:
        if role == CUR.WORKER:
            contact = dict(phone=get_random_phone())
        else:
            contact = dict(email=get_random_email())
        user = user or get_user_fi(**contact)

        company = company or get_company_fi(title=get_random_string())
        data = {"user": user.id, "status": status}
        relation_data = {"company": company, "user": user}
        role_data = {"role": role}
        if _is_relations_ids:
            relation_data = {k: v.id for k, v in relation_data.items()}
        return {**data, **relation_data, **role_data}

    return return_data


@pytest.fixture
def get_cu_fi(monkeypatch, new_company_user_data: Callable) -> Callable[..., CompanyUser]:
    def create_instance(*args, **kwargs) -> CompanyUser:
        monkeypatch.setattr(WorkerBilling, "create_u2_account", lambda *args, **kwargs: None)
        monkeypatch.setattr(WorkerBilling, "create_u1_account", lambda *args, **kwargs: None)
        monkeypatch.setattr(CompanyUser, "create_policies", lambda *a, **kw: None)
        monkeypatch.setattr(CompanyUser, "activate_policies", lambda *a, **kw: None)

        data = new_company_user_data(_is_relations_ids=False, *args, **kwargs)
        status = data.pop("status", None)
        data["status"] = CUS.INVITE.value

        instance = CompanyUser.objects.create(**data)
        if status != CUS.INVITE.value:
            instance.status = status
            instance.save()
        return instance

    return create_instance


@pytest.fixture
def cu_owner_fi(monkeypatch, get_cu_fi):
    monkeypatch.setattr(CompanyUser, "create_policies", lambda *a, **kw: None)
    monkeypatch.setattr(CompanyUser, "activate_policies", lambda *a, **kw: None)
    return get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)


@pytest.fixture
def cu_manager_fi(get_cu_fi):
    return get_cu_fi(role=CUR.PROJECT_MANAGER, status=CUS.ACCEPT.value)


@pytest.fixture
def cu_worker_fi(get_cu_fi):
    return get_cu_fi(status=CUS.ACCEPT.value, role=CUR.WORKER)


@pytest.fixture
def get_cu_owner_fi(get_cu_fi):
    def get_or_create_instance(status: tp.Optional[int] = CUS.ACCEPT.value, *args, **kwargs):
        return get_cu_fi(status=status, role=CUR.OWNER, *args, **kwargs)

    return get_or_create_instance


@pytest.fixture
def get_cu_worker_fi(get_cu_fi):
    def get_or_create_instance(status: tp.Optional[int] = CUS.ACCEPT.value, *args, **kwargs):
        return get_cu_fi(status=status, role=CUR.WORKER, *args, **kwargs)

    return get_or_create_instance


@pytest.fixture
def get_cu_manager_fi(get_cu_fi):
    def get_or_create_instance(status: tp.Optional[int] = CUS.ACCEPT.value, *args, **kwargs):
        return get_cu_fi(status=status, role=CUR.PROJECT_MANAGER, *args, **kwargs)

    return get_or_create_instance
