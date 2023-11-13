from http.client import responses

import pytest
from rest_framework import status as status_code
from django.contrib.auth import get_user_model

from tests.utils import get_authorization_token
from ma_saas.constants.system import Callable
from projects.models.territory import Territory
from companies.models.company_user import CompanyUser

User = get_user_model()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__method__fail(api_client, get_territory_fi: Callable, r_cu: CompanyUser):
    territory = get_territory_fi(company=r_cu.company)
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.delete(f"/api/v1/territories/{territory.id}/")
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED
    assert response.status_text == responses[status_code.HTTP_405_METHOD_NOT_ALLOWED]


def test__model_is_fake_delete_allow_create_new_model(api_client, get_territory_fi: Callable):
    instance = get_territory_fi()
    fields = {f: getattr(instance, f) for f in ["inviting_company", "title"]}
    instance.is_deleted = True
    instance.save()
    assert Territory.objects.filter(**fields, is_deleted=True).count() == 1
    assert get_territory_fi(**fields)
    assert Territory.objects.existing().filter(**fields).count() == 1
