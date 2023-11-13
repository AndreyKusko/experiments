import json
import typing as tp

import pytest
from django.forms import model_to_dict

from clients.policies.interface import Policies
from reports.models.processed_report import ProcessedReport
from tests.fixtures.processed_report_form import CREATED_AT_FIELDS, APPROVED_AT_FIELDS
from tests.test_app_reports.test_processed_reports.test_create.test_common import __get_response


@pytest.mark.parametrize("processed_report_form_field", CREATED_AT_FIELDS + APPROVED_AT_FIELDS)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_manager_fi")])
def test__auto_time_fields_do_not_display(
    api_client,
    monkeypatch,
    get_project_territory_fi,
    get_processed_report_form_fi,
    new_processed_report_data_fi,
    processed_report_form_field: tp.Dict[str, tp.Any],
    r_cu,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [r_cu.company.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    pt = get_project_territory_fi(company=r_cu.company)
    prf = get_processed_report_form_fi(project=pt.project, fields_specs={"2": processed_report_form_field})
    data = new_processed_report_data_fi(company_user=r_cu, project_territory=pt, processed_report_form=prf)
    data.pop("company_user")
    response = __get_response(api_client, data, r_cu.user)
    created_instance_data = model_to_dict(ProcessedReport.objects.get(id=response.data["id"]))
    assert len(response.data["json_fields"]) == len(created_instance_data["json_fields"]) == 0
    assert response.data["json_fields"] == json.loads(data["json_fields"])
