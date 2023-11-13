import typing as tp
from typing import Callable

import pytest
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from projects.models.specialisation import Specialisation
from projects.models.project_questionnaire import ProjectQuestionnaire

User = get_user_model()


@pytest.fixture
def new_project_questionnaire_data(get_user_fi, get_specialisation_fi) -> Callable:
    def return_data(
        user: tp.Optional[User] = None,
        specialisations: tp.Optional[Specialisation] = None,
        media_json: tp.Optional[list] = None,
        text: tp.Optional[str] = None,
        _is_relations_ids: bool = True,
    ) -> tp.Dict[str, tp.Any]:
        user = user or get_user_fi()
        specialisations = specialisations or [get_specialisation_fi()]
        media_json = media_json or []
        text = text or get_random_string()

        data = {"user": user, "specialisations": specialisations, "media_json": media_json, "text": text}

        relation_data = {
            "user": user,
        }
        if _is_relations_ids:
            relation_data = {k: v.id for k, v in relation_data.items() if v}
        specialisations_data = {"specialisations": specialisations}
        if _is_relations_ids:
            specialisations_data = {"specialisations": [s.id for s in specialisations]}
        return {**data, **relation_data, **specialisations_data}

    return return_data


@pytest.fixture
def get_project_questionnaire_fi(
    monkeypatch, new_project_questionnaire_data: Callable
) -> Callable[..., ProjectQuestionnaire]:
    def create_instance(*args, **kwargs) -> ProjectQuestionnaire:
        data = new_project_questionnaire_data(*args, _is_relations_ids=False, **kwargs)
        specialisations = data.pop("specialisations")

        instance = ProjectQuestionnaire.objects.create(**data)
        instance.specialisations.set(specialisations)
        instance.save()

        return instance

    return create_instance


@pytest.fixture
def project_questionnaire_fi(get_project_questionnaire_fi) -> ProjectQuestionnaire:
    return get_project_questionnaire_fi()
