import json
import typing as tp
from typing import Callable

import pytest
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from background.models import BackgroundTask
from companies.models.company import Company
from ma_saas.constants.company import CUR, CUS
from reports.models.worker_report import WorkerReport
from companies.models.company_user import CompanyUser
from ma_saas.constants.background_task import BackgroundTaskType, BackgroundTaskStatus
from projects.models.project_territory import ProjectTerritory

User = get_user_model()


@pytest.fixture
def new_background_task_data(get_company_fi, get_cu_fi) -> Callable:
    def return_data(
        model_name: str = None,
        company: tp.Optional[Company] = None,
        company_user: tp.Optional[CompanyUser] = None,
        status: tp.Optional[ProjectTerritory] = BackgroundTaskStatus.PENDING.value,
        params: tp.Optional[dict] = None,
        input_files: tp.Optional[list] = None,
        result: tp.Optional[dict] = None,
        output_files: tp.Optional[list] = None,
        is_output_files: bool = False,
        failures: tp.Optional[dict] = None,
        task_type: tp.Optional[int] = None,
    ) -> tp.Dict[str, tp.Any]:
        """
        Для заполнения файлов на выдачу нужно послать их (output_files)
            или обязательно оба аргумента is_output_files and task_type
        """
        if not company:
            if company_user:
                company = company_user.company
            else:
                company = get_company_fi()

        company_user = company_user or get_cu_fi(company=company, role=CUR.OWNER, status=CUS.ACCEPT.value)
        model_name = model_name or WorkerReport._meta.concrete_model.__name__
        task_type = task_type or BackgroundTaskType.UPDATE_WORKER_REPORT_STATUS.value
        if output_files or (is_output_files and task_type):
            output_files = output_files or [get_random_string()]
        else:
            output_files = []
        data = {
            "company": company.id,
            "company_user": company_user.id,
            "model_name": model_name,
            "status": status,
            "task_type": task_type,
            "params": json.dumps(params or dict()),
            "input_files": json.dumps(input_files or list()),
            "result": json.dumps(result or list()),
            "output_files": json.dumps(output_files),
            "failures": json.dumps(failures or list()),
        }
        return data

    return return_data


@pytest.fixture
def get_background_task_fi(new_background_task_data: Callable) -> Callable[..., BackgroundTask]:
    def get_or_create_instance(*args, **kwargs) -> BackgroundTask:
        data = new_background_task_data(*args, **kwargs)
        data["input_files"] = json.loads(data["input_files"])
        data["params"] = json.loads(data["params"])
        data["result"] = json.loads(data["result"])
        data["output_files"] = json.loads(data["output_files"])
        data["failures"] = json.loads(data["failures"])
        company = Company.objects.get(id=data.pop("company"))
        company_user = CompanyUser.objects.get(id=data.pop("company_user"))
        instance = BackgroundTask.objects.create(company=company, company_user=company_user, **data)
        return instance

    return get_or_create_instance


@pytest.fixture
def background_task_fi(get_background_task_fi: Callable) -> BackgroundTask:
    return get_background_task_fi()
