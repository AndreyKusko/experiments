import typing as tp
from typing import Callable

import pytest
from django.contrib.auth import get_user_model

from projects.models.project import Project
from ma_saas.constants.project import ProjectJobApplicationStatus
from projects.models.project_job_application import ProjectJobApplication

User = get_user_model()


@pytest.fixture
def new_project_job_application_data() -> Callable:
    def return_data(
        project: tp.Optional[Project] = None,
        user: tp.Optional[User] = None,
        status: tp.Optional[int] = ProjectJobApplicationStatus.ACCEPT.value,
    ) -> tp.Dict[str, tp.Any]:
        return {"project": project.id, "user": user.id, "status": status}

    return return_data


@pytest.fixture
def get_project_job_application_fi(
    new_project_job_application_data: Callable,
) -> Callable[..., ProjectJobApplication]:
    def get_or_create_instance(*args, **kwargs) -> ProjectJobApplication:
        data = new_project_job_application_data(*args, **kwargs)
        data["project"] = Project.objects.get(id=data["project"])
        data["user"] = User.objects.get(id=data["user"])
        instance = ProjectJobApplication.objects.create(**data)
        return instance

    return get_or_create_instance
