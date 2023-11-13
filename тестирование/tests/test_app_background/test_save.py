from typing import Callable

import pytest
from rest_framework.exceptions import ValidationError

from background.models import COMPANY_USER_MUST_BELONG_TO_COMPANY, BackgroundTask
from reports.models.worker_report import WorkerReport
from companies.models.company_user import CompanyUser
from ma_saas.constants.background_task import BackgroundTaskType, BackgroundTaskStatus


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__save__success(api_client, r_cu: CompanyUser, get_background_task_fi: Callable):
    instance = BackgroundTask.objects.create(
        company_user=r_cu,
        company=r_cu.company,
        task_type=BackgroundTaskType.UPDATE_WORKER_REPORT_STATUS.value,
        model_name=WorkerReport._meta.concrete_model.__name__,
        status=BackgroundTaskStatus.PENDING,
    )

    assert instance


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__different_cu_company(
    api_client, r_cu: CompanyUser, get_background_task_fi: Callable, get_company_fi
):
    try:
        BackgroundTask.objects.create(
            company_user=r_cu,
            company=get_company_fi(),
            task_type=BackgroundTaskType.UPDATE_WORKER_REPORT_STATUS.value,
            model_name=WorkerReport._meta.concrete_model.__name__,
            status=BackgroundTaskStatus.PENDING,
        )
    except ValidationError as e:
        assert e.detail[0] == COMPANY_USER_MUST_BELONG_TO_COMPANY
