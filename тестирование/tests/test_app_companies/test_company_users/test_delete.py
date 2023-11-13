from http.client import responses

from rest_framework import status as status_code
from django.contrib.auth import get_user_model

from tests.utils import get_authorization_token
from ma_saas.constants.company import CUR, CUS
from companies.models.company_user import CompanyUser
from clients.billing.interfaces.worker import WorkerBilling

User = get_user_model()


def test__method__fail(api_client, get_cu_fi):
    r_cu = get_cu_fi(role=CUR.OWNER, status=CUS.ACCEPT.value)
    instance = get_cu_fi(company=r_cu.company)
    api_client.credentials(HTTP_AUTHORIZATION=get_authorization_token(r_cu.user))
    response = api_client.delete(f"/api/v1/company-users/{instance.id}/")
    assert response.status_code == status_code.HTTP_405_METHOD_NOT_ALLOWED
    assert response.status_text == responses[status_code.HTTP_405_METHOD_NOT_ALLOWED]
    assert response.data["detail"] == 'Method "DELETE" not allowed.'


def test__model_is_fake_delete_allow_create_new_model(api_client, monkeypatch, get_cu_fi):
    monkeypatch.setattr(WorkerBilling, "create_u2_account", lambda *args, **kwargs: None)
    monkeypatch.setattr(WorkerBilling, "create_u1_account", lambda *args, **kwargs: None)

    monkeypatch.setattr(CompanyUser, "create_policies", lambda *a, **kw: None)
    monkeypatch.setattr(CompanyUser, "activate_policies", lambda *a, **kw: None)
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    instance = get_cu_fi()
    fields = {f: getattr(instance, f) for f in ["company", "user"]}
    instance.is_deleted = True
    instance.save()
    assert CompanyUser.objects.filter(**fields, is_deleted=True).count() == 1
    assert get_cu_fi(**fields)
    assert CompanyUser.objects.existing().filter(**fields).count() == 1
