import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_update, retrieve_response_instance
from ma_saas.constants.report import ProcessedReportStatus as PRS
from ma_saas.constants.report import ProcessedReportPartnerStatus
from ma_saas.constants.company import CPS, CUR, CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from ma_saas.constants.project import PPS
from clients.policies.interface import Policies
from reports.models.processed_report import ProcessedReport
from reports.serializers.processed_report_avaliable_client import ACCEPT_REPORTS_FORBIDDEN
from tests.test_app_reports.test_processed_reports_available_client.constants import PROCESSED_REPORTS_PATH

User = get_user_model()

__get_response = functools.partial(request_response_update, path=PROCESSED_REPORTS_PATH)


@pytest.mark.parametrize("instance", [pytest.lazy_fixture("processed_report_fi")])
def test__anonymous_user__unauthorised(api_client, instance):
    response = __get_response(api_client, instance.id, data={}, status_codes=NotAuthenticated)
    assert response.data["detail"] == NotAuthenticated.default_detail


def test__user_without_companies_got_nothing(
    api_client,
    user_fi,
    monkeypatch,
    get_company_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_processed_report_fi,
    get_project_scheme_partnership_fi,
    get_processed_report_form_fi,
):
    cp = get_company_partnership_fi(
        inviting_company=get_company_fi(),
        invited_company=get_company_fi(),
        invited_company_status=CPS.ACCEPT.value,
    )
    pp = get_project_partnership_fi(company_partnership=cp)
    psp = get_project_scheme_partnership_fi(project_partnership=pp)
    prf = get_processed_report_form_fi(project_scheme=psp.project_scheme)
    instance = get_processed_report_fi(processed_report_form=prf)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(
        Policies,
        "get_target_policies",
        lambda *a, **kw: [cp.inviting_company.id, cp.invited_company.id, pp.id],
    )
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    response = __get_response(api_client, instance.id, {}, user=user_fi, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__client_owner__client_company__without_policy__success(
    api_client,
    mock_policies_false,
    r_cu,
    monkeypatch,
    get_company_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_processed_report_fi,
    get_project_scheme_partnership_fi,
    get_processed_report_form_fi,
):
    cp = get_company_partnership_fi(
        inviting_company=get_company_fi(),
        invited_company=r_cu.company,
        invited_company_status=CPS.ACCEPT.value,
    )
    pp = get_project_partnership_fi(company_partnership=cp)
    psp = get_project_scheme_partnership_fi(project_partnership=pp)
    prf = get_processed_report_form_fi(project_scheme=psp.project_scheme)
    instance = get_processed_report_fi(processed_report_form=prf, status=PRS.ACCEPTED.value)
    response = __get_response(api_client, instance.id, {}, user=r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__not_client_company_owner__with_policy__fail(
    api_client,
    mock_policies_false,
    r_cu,
    monkeypatch,
    get_company_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_processed_report_fi,
    get_project_scheme_partnership_fi,
    get_processed_report_form_fi,
):
    cp = get_company_partnership_fi(
        inviting_company=r_cu.company,
        invited_company=get_company_fi(),
        invited_company_status=CPS.ACCEPT.value,
    )
    pp = get_project_partnership_fi(company_partnership=cp)
    psp = get_project_scheme_partnership_fi(project_partnership=pp)
    prf = get_processed_report_form_fi(project_scheme=psp.project_scheme)
    instance = get_processed_report_fi(processed_report_form=prf, status=PRS.ACCEPTED.value)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [pp.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
def test__not_accept_owner__client_company__fail(
    api_client,
    mock_policies_false,
    get_cu_fi,
    monkeypatch,
    get_company_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_processed_report_fi,
    get_project_scheme_partnership_fi,
    get_processed_report_form_fi,
    status,
):
    r_cu = get_cu_fi(role=CUR.OWNER, status=status.value)
    cp = get_company_partnership_fi(
        inviting_company=get_company_fi(),
        invited_company=r_cu.company,
        invited_company_status=CPS.ACCEPT.value,
    )
    pp = get_project_partnership_fi(company_partnership=cp)
    psp = get_project_scheme_partnership_fi(project_partnership=pp)
    prf = get_processed_report_form_fi(project_scheme=psp.project_scheme)
    instance = get_processed_report_fi(processed_report_form=prf, status=PRS.ACCEPTED.value)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [pp.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    response = __get_response(api_client, instance.id, {}, r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__client_company__with_policy__success(
    api_client,
    get_cu_fi,
    monkeypatch,
    get_company_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_processed_report_fi,
    get_project_scheme_partnership_fi,
    get_processed_report_form_fi,
    role,
):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    cp = get_company_partnership_fi(
        inviting_company=get_company_fi(),
        invited_company=r_cu.company,
        invited_company_status=CPS.ACCEPT.value,
    )
    pp = get_project_partnership_fi(company_partnership=cp)
    psp = get_project_scheme_partnership_fi(project_partnership=pp)
    prf = get_processed_report_form_fi(project_scheme=psp.project_scheme)
    instance = get_processed_report_fi(processed_report_form=prf, status=PRS.ACCEPTED.value)

    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)
    monkeypatch.setattr(Policies, "get_target_policies", lambda *a, **kw: [pp.id])
    monkeypatch.setattr(Policies, "list", lambda *a, **kw: [])

    response = __get_response(api_client, instance.id, {}, user=r_cu.user)
    assert response.data["id"] == instance.id


@pytest.mark.parametrize("role", NOT_OWNER_ROLES)
def test__not_owner__client_company__without_policy__fail(
    api_client,
    mock_policies_false,
    get_cu_fi,
    monkeypatch,
    get_company_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_processed_report_fi,
    get_project_scheme_partnership_fi,
    get_processed_report_form_fi,
    role,
):
    r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
    cp = get_company_partnership_fi(
        inviting_company=get_company_fi(),
        invited_company=r_cu.company,
        invited_company_status=CPS.ACCEPT.value,
    )
    pp = get_project_partnership_fi(company_partnership=cp)
    psp = get_project_scheme_partnership_fi(project_partnership=pp)
    prf = get_processed_report_form_fi(project_scheme=psp.project_scheme)
    instance = get_processed_report_fi(processed_report_form=prf, status=PRS.ACCEPTED.value)

    response = __get_response(api_client, instance.id, {}, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("invited_company_status", "inviting_company_status"),
    [
        *[(PPS.ACCEPT, s) for s in PPS if s not in (PPS.INVITE, PPS.ACCEPT)],
        *[(s, PPS.ACCEPT) for s in PPS if s != PPS.ACCEPT],
    ],
)
def test__not_active_project_partnership__fail(
    api_client,
    mock_policies_false,
    r_cu,
    monkeypatch,
    get_company_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_processed_report_fi,
    get_project_scheme_partnership_fi,
    get_processed_report_form_fi,
    invited_company_status,
    inviting_company_status,
):
    cp = get_company_partnership_fi(
        inviting_company=get_company_fi(),
        invited_company=r_cu.company,
        invited_company_status=CPS.ACCEPT.value,
    )
    pp = get_project_partnership_fi(
        company_partnership=cp,
        invited_company_status=invited_company_status.value,
        inviting_company_status=inviting_company_status.value,
    )
    psp = get_project_scheme_partnership_fi(project_partnership=pp)
    prf = get_processed_report_form_fi(project_scheme=psp.project_scheme)
    instance = get_processed_report_fi(processed_report_form=prf, status=PRS.ACCEPTED.value)

    response = __get_response(api_client, instance.id, {}, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("invited_company_status", "inviting_company_status"),
    [
        *[(CPS.ACCEPT, s) for s in CPS if s not in (CPS.INVITE, CPS.ACCEPT)],
        *[(s, CPS.ACCEPT) for s in CPS if s != CPS.ACCEPT],
    ],
)
def test__not_active_company_partnership__fail(
    api_client,
    mock_policies_false,
    r_cu,
    monkeypatch,
    get_company_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_processed_report_fi,
    get_project_scheme_partnership_fi,
    get_processed_report_form_fi,
    invited_company_status,
    inviting_company_status,
):
    cp = get_company_partnership_fi(
        inviting_company=get_company_fi(),
        invited_company=r_cu.company,
        invited_company_status=invited_company_status.value,
        inviting_company_status=inviting_company_status.value,
    )
    pp = get_project_partnership_fi(
        company_partnership=cp,
        invited_company_status=PPS.ACCEPT.value,
        inviting_company_status=PPS.ACCEPT.value,
    )
    psp = get_project_scheme_partnership_fi(project_partnership=pp)
    prf = get_processed_report_form_fi(project_scheme=psp.project_scheme)
    instance = get_processed_report_fi(processed_report_form=prf, status=PRS.ACCEPTED.value)

    response = __get_response(api_client, instance.id, {}, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("status", [s for s in PRS if s != PRS.ACCEPTED])
def test__not_accepted_report_status__fail(
    api_client,
    mock_policies_false,
    r_cu,
    monkeypatch,
    get_company_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_processed_report_fi,
    get_project_scheme_partnership_fi,
    get_processed_report_form_fi,
    status,
):
    cp = get_company_partnership_fi(
        inviting_company=get_company_fi(),
        invited_company=r_cu.company,
        invited_company_status=CPS.ACCEPT.value,
        inviting_company_status=CPS.ACCEPT.value,
    )
    pp = get_project_partnership_fi(
        company_partnership=cp,
        invited_company_status=PPS.ACCEPT.value,
        inviting_company_status=PPS.ACCEPT.value,
    )
    psp = get_project_scheme_partnership_fi(project_partnership=pp)
    prf = get_processed_report_form_fi(project_scheme=psp.project_scheme)
    instance = get_processed_report_fi(processed_report_form=prf, status=status.value)

    response = __get_response(api_client, instance.id, {}, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__partner_status_updating__if_partnership_field_forbidden__fail(
    api_client,
    mock_policies_false,
    r_cu,
    monkeypatch,
    get_company_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_processed_report_fi,
    get_project_scheme_partnership_fi,
    get_processed_report_form_fi,
):
    cp = get_company_partnership_fi(
        inviting_company=get_company_fi(),
        invited_company=r_cu.company,
        invited_company_status=CPS.ACCEPT.value,
    )
    pp = get_project_partnership_fi(company_partnership=cp)
    psp = get_project_scheme_partnership_fi(project_partnership=pp)
    psp.is_processed_reports_acceptance_allowed = False
    psp.save()

    prf = get_processed_report_form_fi(project_scheme=psp.project_scheme)
    instance = get_processed_report_fi(processed_report_form=prf, status=PRS.CREATED.value)
    instance.status = PRS.ACCEPTED.value
    instance.save()
    assert not instance.partner_status
    assert instance.partner_accepted_at is None

    new_partner_status = ProcessedReportPartnerStatus.ACCEPTED.value
    data = {"partner_status": new_partner_status}
    response = __get_response(api_client, instance.id, data, user=r_cu.user, status_codes=ValidationError)
    assert response.data == {"non_field_errors": [ACCEPT_REPORTS_FORBIDDEN]}
    pr = ProcessedReport.objects.get(id=instance.id)
    assert not pr.partner_status
    assert not pr.partner_accepted_at


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__partner_status_updating__success(
    api_client,
    mock_policies_false,
    r_cu,
    monkeypatch,
    get_company_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_processed_report_fi,
    get_project_scheme_partnership_fi,
    get_processed_report_form_fi,
):
    cp = get_company_partnership_fi(
        inviting_company=get_company_fi(),
        invited_company=r_cu.company,
        invited_company_status=CPS.ACCEPT.value,
    )
    pp = get_project_partnership_fi(company_partnership=cp)
    psp = get_project_scheme_partnership_fi(project_partnership=pp)
    psp.is_processed_reports_acceptance_allowed = True
    psp.save()

    prf = get_processed_report_form_fi(project_scheme=psp.project_scheme)
    instance = get_processed_report_fi(processed_report_form=prf, status=PRS.CREATED.value)
    instance.status = PRS.ACCEPTED.value
    instance.save()
    assert not instance.partner_status
    assert instance.partner_accepted_at is None

    new_partner_status = ProcessedReportPartnerStatus.ACCEPTED.value
    data = {"partner_status": new_partner_status}
    response = __get_response(api_client, instance.id, data, user=r_cu.user)
    response_instance = response.data
    assert response_instance.pop("id") == instance.id

    updated_instance = ProcessedReport.objects.get(id=instance.id)
    assert updated_instance.partner_accepted_at
    assert updated_instance.partner_status == new_partner_status

    assert response_instance.pop("partner_accepted_at")
    assert response_instance.pop("partner_status") == new_partner_status


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__partner_status_updating__if_not_accepted_status__fail(
    api_client,
    mock_policies_false,
    r_cu,
    monkeypatch,
    get_company_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_processed_report_fi,
    get_project_scheme_partnership_fi,
    get_processed_report_form_fi,
):
    cp = get_company_partnership_fi(
        inviting_company=get_company_fi(),
        invited_company=r_cu.company,
        invited_company_status=CPS.ACCEPT.value,
    )
    pp = get_project_partnership_fi(company_partnership=cp)
    psp = get_project_scheme_partnership_fi(project_partnership=pp)
    psp.is_processed_reports_acceptance_allowed = True
    psp.save()

    prf = get_processed_report_form_fi(project_scheme=psp.project_scheme)
    instance = get_processed_report_fi(processed_report_form=prf, status=PRS.CREATED.value)

    assert not instance.partner_status
    assert instance.partner_accepted_at is None

    new_partner_status = ProcessedReportPartnerStatus.ACCEPTED.value
    data = {"partner_status": new_partner_status}
    response = __get_response(api_client, instance.id, data, user=r_cu.user, status_codes=NotFound)
    assert response.data == {"detail": NotFound.default_detail}


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("is_partner_status", [True, False])
def test__response_data(
    api_client,
    mock_policies_false,
    r_cu,
    monkeypatch,
    get_company_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_processed_report_fi,
    get_project_scheme_partnership_fi,
    get_processed_report_form_fi,
    is_partner_status,
):
    cp = get_company_partnership_fi(
        inviting_company=get_company_fi(),
        invited_company=r_cu.company,
        invited_company_status=CPS.ACCEPT.value,
    )
    pp = get_project_partnership_fi(company_partnership=cp)
    psp = get_project_scheme_partnership_fi(
        project_partnership=pp, is_processed_reports_acceptance_allowed=True
    )
    prf = get_processed_report_form_fi(project_scheme=psp.project_scheme)
    instance = get_processed_report_fi(processed_report_form=prf)
    # instance.status = PRS.ACCEPTED.value
    if is_partner_status:
        instance.partner_status = ProcessedReportPartnerStatus.ACCEPTED.value
    instance.save()

    response = __get_response(api_client, instance.id, {}, user=r_cu.user)
    response_instance = response.data
    assert response_instance.pop("id") == instance.id
    if response_company_user := retrieve_response_instance(response_instance, "company_user", dict):
        assert response_company_user.pop("id")
        assert response_company_user.pop("user")
        assert response_company_user.pop("company")
        assert not response_company_user
    if response_prf := retrieve_response_instance(response_instance, "processed_report_form", dict):
        assert response_prf.pop("id") == prf.id
        assert response_prf.pop("fields_specs") == prf.fields_specs
        if response_project_scheme := retrieve_response_instance(response_prf, "project_scheme", dict):
            assert response_project_scheme.pop("id") == psp.project_scheme.id
            if response_project := retrieve_response_instance(response_project_scheme, "project", dict):
                assert response_project.pop("id") == pp.project.id
                assert response_project.pop("title") == pp.project.title
                assert not response_project
            assert not response_project_scheme
        assert not response_prf

    assert response_instance.pop("json_fields") == instance.json_fields
    assert response_instance.pop("comment") == instance.comment
    assert response_instance.pop("created_at")
    assert response_instance.pop("updated_at")

    if is_partner_status:
        assert response_instance.pop("partner_accepted_at")
        assert response_instance.pop("partner_status") == ProcessedReportPartnerStatus.ACCEPTED.value
    else:
        assert response_instance.pop("partner_accepted_at") is None
        assert response_instance.pop("partner_status") is None

    assert response_instance.pop("status") == PRS.ACCEPTED.value
    assert response_instance.pop("accepted_at")

    if response_worker_report := retrieve_response_instance(response_instance, "worker_report", dict):
        assert response_worker_report
    if response_updated_by := retrieve_response_instance(response_instance, "updated_by", dict):
        assert response_updated_by == {"user": {}, "company_user": {}}

    assert response_instance.pop("is_processed_reports_acceptance_allowed")
    assert not response_instance
