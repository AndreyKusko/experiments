import functools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied

from tests.utils import request_response_create, retrieve_response_instance
from accounts.models import USER_IS_BLOCKED, USER_IS_DELETED, NOT_TA_REQUESTING_USER_REASON
from ma_saas.utils.queryset import REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY
from projects.models.project import PROJECT_IS_DELETED, NOT_TA_PROJECT_REASON
from companies.models.company import COMPANY_IS_DELETED, NOT_TA_COMPANY_REASON
from ma_saas.constants.company import CUR, CUS, NOT_ACCEPT_CUS, NOT_OWNER_ROLES
from ma_saas.constants.company import CompanyPartnershipStatus as CPS
from ma_saas.constants.project import ProjectPartnershipStatus as PPS
from clients.policies.interface import Policies
from companies.models.company_user import NOT_TA_RCU_REASON, NOT_TA_RCU_MUST_BE_ACCEPT, CompanyUser
from projects.models.project_scheme import NOT_TA_PROJECT_SCHEME_REASON
from projects.models.project_scheme_partnership import (
    PROJECT_SCHEME_PARTNERSHIP__ACCEPTANCE__ERR,
    PROJECT_SCHEME_PARTNERSHIP__PROJECT_SCHEME__N__PROJECT_PARTNERSHIP__ERR,
    ProjectSchemePartnership,
)

User = get_user_model()

_get_response = functools.partial(request_response_create, path="/api/v1/project-scheme-partnership/")


def test__anonymous_user__fail(api_client):
    response = _get_response(api_client, {}, status_codes=NotAuthenticated)
    assert response.data == {"detail": NotAuthenticated.default_detail}


class TestOwner:
    @staticmethod
    @pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
    def test__accepted_owner__inviting_company__without_policy__success(
        api_client,
        mock_policies_false,
        r_cu,
        get_project_scheme_fi,
        get_company_partnership_fi,
        get_project_partnership_fi,
        get_company_fi,
        new_project_scheme_partnership_data,
    ):
        invited_company = get_company_fi()
        cp = get_company_partnership_fi(inviting_company=r_cu.company, invited_company=invited_company)
        pp = get_project_partnership_fi(company_partnership=cp)
        project_scheme = get_project_scheme_fi(project=pp.project)
        data = new_project_scheme_partnership_data(project_scheme=project_scheme, project_partnership=pp)
        response = _get_response(api_client, data, r_cu.user)
        assert response.data["id"]

    @staticmethod
    @pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
    def test__accepted_owner__invited_company__without_policy__success(
        api_client,
        mock_policies_false,
        r_cu,
        get_project_scheme_fi,
        get_company_partnership_fi,
        get_project_partnership_fi,
        get_company_fi,
        get_project_fi,
        new_project_scheme_partnership_data,
    ):
        ing_company = get_company_fi()
        project = get_project_fi(company=r_cu.company)
        cp = get_company_partnership_fi(invited_company=r_cu.company, inviting_company=ing_company)
        pp = get_project_partnership_fi(company_partnership=cp, project=project)
        project_scheme = get_project_scheme_fi(project=pp.project)
        data = new_project_scheme_partnership_data(project_scheme=project_scheme, project_partnership=pp)
        response = _get_response(api_client, data, r_cu.user)
        assert response.data["id"]

    @staticmethod
    @pytest.mark.parametrize("status", NOT_ACCEPT_CUS)
    def test__not_accepted_owner__fail(
        api_client,
        monkeypatch,
        get_project_scheme_fi,
        get_company_partnership_fi,
        get_project_partnership_fi,
        get_company_fi,
        get_cu_fi,
        new_project_scheme_partnership_data,
        status,
    ):
        monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

        r_cu = get_cu_fi(role=CUR.OWNER, status=status)
        invited_company = get_company_fi()
        cp = get_company_partnership_fi(inviting_company=r_cu.company, invited_company=invited_company)
        pp = get_project_partnership_fi(company_partnership=cp)
        project_scheme = get_project_scheme_fi(project=pp.project)
        data = new_project_scheme_partnership_data(project_scheme=project_scheme, project_partnership=pp)
        response = _get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
        assert response.data == {"detail": NOT_TA_RCU_MUST_BE_ACCEPT}


class TestUnique:
    @staticmethod
    @pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
    def test__same__scheme__n__project_partnership__unique__fail(
        api_client,
        mock_policies_false,
        r_cu,
        get_project_scheme_fi,
        get_company_partnership_fi,
        get_project_partnership_fi,
        get_company_fi,
        new_project_scheme_partnership_data,
        get_project_scheme_partnership_fi,
    ):
        invited_company = get_company_fi()
        cp = get_company_partnership_fi(
            inviting_company=r_cu.company,
            invited_company=invited_company,
            invited_company_status=CPS.ACCEPT.value,
            inviting_company_status=CPS.ACCEPT.value,
        )
        pp = get_project_partnership_fi(
            company_partnership=cp,
            invited_company_status=PPS.ACCEPT.value,
            inviting_company_status=PPS.ACCEPT.value,
        )
        project_scheme = get_project_scheme_fi(project=pp.project)
        data = new_project_scheme_partnership_data(
            project_scheme=project_scheme,
            project_partnership=pp,
            is_processed_reports_acceptance_allowed=False,
        )
        _duplicate_instance = get_project_scheme_partnership_fi(
            project_scheme=project_scheme,
            project_partnership=pp,
            is_processed_reports_acceptance_allowed=False,
        )
        response = _get_response(api_client, data, r_cu.user, status_codes=ValidationError)
        assert response.data == {
            "project_partnership": [PROJECT_SCHEME_PARTNERSHIP__PROJECT_SCHEME__N__PROJECT_PARTNERSHIP__ERR]
        }

    @staticmethod
    @pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
    @pytest.mark.parametrize(
        (
            "project_invited_company_status",
            "project_inviting_company_status",
            "company_invited_company_status",
            "company_inviting_company_status",
        ),
        [
            (PPS.ACCEPT, PPS.ACCEPT, CPS.ACCEPT, CPS.ACCEPT),
            (PPS.INVITE, PPS.ACCEPT, CPS.ACCEPT, CPS.ACCEPT),
            (PPS.INVITE, PPS.ACCEPT, CPS.INVITE, CPS.ACCEPT),
        ],
    )
    def test__report_acceptance_per__scheme__uniq__fail(
        api_client,
        mock_policies_false,
        r_cu,
        get_project_scheme_fi,
        get_company_partnership_fi,
        get_project_partnership_fi,
        get_company_fi,
        new_project_scheme_partnership_data,
        get_project_scheme_partnership_fi,
        project_invited_company_status,
        project_inviting_company_status,
        company_invited_company_status,
        company_inviting_company_status,
    ):
        invited_company = get_company_fi()
        cp_statuses = dict(
            invited_company_status=company_invited_company_status.value,
            inviting_company_status=company_inviting_company_status.value,
        )
        pp_statuses = dict(
            invited_company_status=project_invited_company_status.value,
            inviting_company_status=project_inviting_company_status.value,
        )

        cp = get_company_partnership_fi(
            inviting_company=r_cu.company, invited_company=invited_company, **cp_statuses
        )

        pp = get_project_partnership_fi(company_partnership=cp, **pp_statuses)
        ps = get_project_scheme_fi(project=pp.project)
        data = new_project_scheme_partnership_data(
            project_scheme=ps, project_partnership=pp, is_processed_reports_acceptance_allowed=True
        )

        another_company = get_company_fi()
        another_cp = get_company_partnership_fi(
            inviting_company=r_cu.company, invited_company=another_company, **cp_statuses
        )
        another_pp = get_project_partnership_fi(
            project=ps.project, company_partnership=another_cp, **pp_statuses
        )
        assert another_pp != pp
        assert another_pp.company_partnership.invited_company != pp.project.company
        _duplicate_instance = get_project_scheme_partnership_fi(
            project_scheme=ps, project_partnership=another_pp, is_processed_reports_acceptance_allowed=True
        )
        # assert _duplicate_instance.partner_company == another_company
        response = _get_response(api_client, data, r_cu.user, status_codes=ValidationError)
        assert response.data == {
            "is_processed_reports_acceptance_allowed": [PROJECT_SCHEME_PARTNERSHIP__ACCEPTANCE__ERR]
        }

    @staticmethod
    @pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
    @pytest.mark.parametrize("is_processed_reports_acceptance_allowed", [True, False])
    @pytest.mark.parametrize(
        ("invited_company_status", "inviting_company_status"),
        [(PPS.CANCEL, PPS.ACCEPT), (PPS.ACCEPT, PPS.CANCEL)],
    )
    def test__project_partnership_invite_status__unique__allowed(
        api_client,
        mock_policies_false,
        r_cu,
        get_project_scheme_fi,
        get_company_partnership_fi,
        get_project_partnership_fi,
        get_company_fi,
        new_project_scheme_partnership_data,
        get_project_scheme_partnership_fi,
        invited_company_status,
        inviting_company_status,
        is_processed_reports_acceptance_allowed,
    ):
        invited_company = get_company_fi()
        cp = get_company_partnership_fi(inviting_company=r_cu.company, invited_company=invited_company)
        pp = get_project_partnership_fi(company_partnership=cp)
        project_scheme = get_project_scheme_fi(project=pp.project)
        data = new_project_scheme_partnership_data(
            project_scheme=project_scheme,
            project_partnership=pp,
            is_processed_reports_acceptance_allowed=False,
        )
        pp.invited_company_status = invited_company_status.value
        pp.inviting_company_status = inviting_company_status.value
        pp.save()

        another_pp = get_project_partnership_fi(company_partnership=cp, project=pp.project)
        _duplicate_instance = get_project_scheme_partnership_fi(
            project_scheme=project_scheme,
            project_partnership=another_pp,
            is_processed_reports_acceptance_allowed=is_processed_reports_acceptance_allowed,
        )
        response = _get_response(api_client, data, r_cu.user)
        created_pps = (
            ProjectSchemePartnership.objects.existing().exclude(id=_duplicate_instance.id).filter(**data)
        )
        assert len(created_pps) == 1
        assert response.data["id"] == created_pps.first().id

    @staticmethod
    @pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
    @pytest.mark.parametrize(
        ("invited_company_status", "inviting_company_status"),
        [
            (CPS.CANCEL, CPS.ACCEPT),
            (CPS.ACCEPT, CPS.CANCEL),
        ],
    )
    def test__company_partnership_invite__status_accept_false__unique__allowed(
        api_client,
        mock_policies_false,
        r_cu,
        get_project_scheme_fi,
        get_company_partnership_fi,
        get_project_partnership_fi,
        get_company_fi,
        new_project_scheme_partnership_data,
        get_project_scheme_partnership_fi,
        invited_company_status,
        inviting_company_status,
    ):
        invited_company = get_company_fi()
        cp = get_company_partnership_fi(inviting_company=r_cu.company, invited_company=invited_company)
        pp = get_project_partnership_fi(company_partnership=cp)
        ps = get_project_scheme_fi(project=pp.project)
        is_acceptance = dict(is_processed_reports_acceptance_allowed=False)
        duplicate = get_project_scheme_partnership_fi(
            project_scheme=ps, project_partnership=pp, **is_acceptance
        )
        cp.invited_company_status = invited_company_status.value
        cp.inviting_company_status = inviting_company_status.value
        cp.save()

        another_cp = get_company_partnership_fi(
            inviting_company=r_cu.company, invited_company=invited_company
        )
        another_pp = get_project_partnership_fi(company_partnership=another_cp, project=pp.project)
        data = new_project_scheme_partnership_data(
            project_scheme=ps, project_partnership=another_pp, **is_acceptance
        )

        response = _get_response(api_client, data, r_cu.user)
        created_pps = ProjectSchemePartnership.objects.existing().exclude(id=duplicate.id).filter(**data)
        assert len(created_pps) == 1
        assert response.data["id"] == created_pps.first().id


class TestNotOwner:
    @staticmethod
    @pytest.mark.parametrize("role", NOT_OWNER_ROLES)
    def test__not_owner_without_policy__fail(
        api_client,
        monkeypatch,
        get_project_scheme_fi,
        get_company_partnership_fi,
        get_project_partnership_fi,
        get_company_fi,
        get_cu_fi,
        new_project_scheme_partnership_data,
        role,
    ):
        monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: False)

        r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
        invited_company = get_company_fi()
        cp = get_company_partnership_fi(inviting_company=r_cu.company, invited_company=invited_company)
        pp = get_project_partnership_fi(company_partnership=cp)
        project_scheme = get_project_scheme_fi(project=pp.project)
        data = new_project_scheme_partnership_data(project_scheme=project_scheme, project_partnership=pp)
        response = _get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
        assert response.data == {"detail": PermissionDenied.default_detail}

    @staticmethod
    @pytest.mark.parametrize("role", NOT_OWNER_ROLES)
    def test__not_owner__with_policy__success(
        api_client,
        monkeypatch,
        get_project_scheme_fi,
        get_company_partnership_fi,
        get_project_partnership_fi,
        get_company_fi,
        get_cu_fi,
        new_project_scheme_partnership_data,
        role,
    ):
        monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

        r_cu = get_cu_fi(role=role, status=CUS.ACCEPT.value)
        invited_company = get_company_fi()
        cp = get_company_partnership_fi(inviting_company=r_cu.company, invited_company=invited_company)
        pp = get_project_partnership_fi(company_partnership=cp)
        project_scheme = get_project_scheme_fi(project=pp.project)
        data = new_project_scheme_partnership_data(project_scheme=project_scheme, project_partnership=pp)
        response = _get_response(api_client, data, r_cu.user)
        assert response.data["id"]


class TestResponseData:
    @staticmethod
    @pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
    def test__ing_company__response_data(
        api_client,
        mock_policies_false,
        r_cu,
        get_project_scheme_fi,
        get_company_partnership_fi,
        get_project_partnership_fi,
        get_company_fi,
        new_project_scheme_partnership_data,
    ):
        invited_company = get_company_fi()
        cp = get_company_partnership_fi(inviting_company=r_cu.company, invited_company=invited_company)
        pp = get_project_partnership_fi(company_partnership=cp)
        project_scheme = get_project_scheme_fi(project=pp.project)
        data = new_project_scheme_partnership_data(project_scheme=project_scheme, project_partnership=pp)
        response = _get_response(api_client, data, r_cu.user)

        response_instance = response.data
        instance_id = response_instance.pop("id")
        created_instance = ProjectSchemePartnership.objects.get(id=instance_id)
        if response_project_scheme := retrieve_response_instance(response_instance, "project_scheme", dict):
            created_instance_scheme = created_instance.project_scheme
            assert response_project_scheme.pop("id") == created_instance_scheme.id == project_scheme.id

            assert response_project_scheme.pop("title") == created_instance_scheme.title
            assert created_instance_scheme.title == project_scheme.title

            assert response_project_scheme.pop("is_labour_exchange") == project_scheme.is_labour_exchange
            assert created_instance_scheme.is_labour_exchange == project_scheme.is_labour_exchange

            assert not response_project_scheme
        assert (
            response_instance.pop("is_processed_reports_acceptance_allowed")
            == created_instance.is_processed_reports_acceptance_allowed
        )
        if response_pp := retrieve_response_instance(response_instance, "project_partnership", dict):
            created_instance_pp = created_instance.project_partnership
            assert response_pp.pop("id") == created_instance_pp.id == pp.id
            if response_partner_company := retrieve_response_instance(response_pp, "partner_company", dict):
                assert response_partner_company.pop("id") == created_instance_pp.partner_company.id
                assert response_partner_company.pop("title") == created_instance_pp.partner_company.title
                assert not response_partner_company
            if response_project := retrieve_response_instance(response_pp, "project", dict):
                assert response_project.pop("id") == created_instance_pp.project.id == pp.project.id
                assert response_project.pop("title") == created_instance_pp.project.title == pp.project.title
                if response_company := retrieve_response_instance(response_project, "company", dict):
                    created_instance_c = created_instance_pp.project.company

                    assert response_company.pop("id") == created_instance_c.id == pp.project.company.id
                    assert pp.project.company.id == r_cu.company.id

                    assert response_company.pop("title") == pp.project.company.title
                    assert pp.project.company.title == r_cu.company.title == created_instance_c.title

                    assert not response_company
                assert not response_project
            assert not response_pp
        assert response_instance.pop("created_at")
        assert response_instance.pop("updated_at")
        assert not response_instance

    @staticmethod
    @pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
    def test__ed_company__response_data(
        api_client,
        mock_policies_false,
        r_cu,
        get_project_scheme_fi,
        get_project_fi,
        get_company_partnership_fi,
        get_project_partnership_fi,
        get_company_fi,
        new_project_scheme_partnership_data,
    ):
        ing_company = get_company_fi()
        project = get_project_fi(company=r_cu.company)
        cp = get_company_partnership_fi(invited_company=r_cu.company, inviting_company=ing_company)
        pp = get_project_partnership_fi(company_partnership=cp, project=project)
        project_scheme = get_project_scheme_fi(project=pp.project)
        data = new_project_scheme_partnership_data(project_scheme=project_scheme, project_partnership=pp)
        response = _get_response(api_client, data, r_cu.user)

        response_instance = response.data
        instance_id = response_instance.pop("id")
        created_instance = ProjectSchemePartnership.objects.get(id=instance_id)
        if response_scheme := retrieve_response_instance(response_instance, "project_scheme", dict):
            created_instance_scheme = created_instance.project_scheme
            assert response_scheme.pop("id") == created_instance_scheme.id == project_scheme.id
            assert response_scheme.pop("title") == created_instance_scheme.title == project_scheme.title
            assert response_scheme.pop("is_labour_exchange") == created_instance_scheme.is_labour_exchange
            assert created_instance_scheme.is_labour_exchange == project_scheme.is_labour_exchange

            assert not response_scheme
        assert (
            response_instance.pop("is_processed_reports_acceptance_allowed")
            == created_instance.is_processed_reports_acceptance_allowed
        )
        if response_pp := retrieve_response_instance(response_instance, "project_partnership", dict):
            created_instance_pp = created_instance.project_partnership
            assert response_pp.pop("id") == created_instance_pp.id == pp.id
            if response_partner_company := retrieve_response_instance(response_pp, "partner_company", dict):
                assert response_partner_company.pop("id") == created_instance_pp.partner_company.id
                assert response_partner_company.pop("title") == created_instance_pp.partner_company.title
                assert not response_partner_company
            if response_project := retrieve_response_instance(response_pp, "project", dict):
                assert response_project.pop("id") == created_instance_pp.project.id == pp.project.id
                assert response_project.pop("title") == created_instance_pp.project.title == pp.project.title
                if response_company := retrieve_response_instance(response_project, "company", dict):
                    created_instance_c = created_instance_pp.project.company

                    assert response_company.pop("id") == created_instance_c.id == pp.project.company.id
                    assert pp.project.company.id == r_cu.company.id

                    assert response_company.pop("title") == pp.project.company.title
                    assert pp.project.company.title == r_cu.company.title == created_instance_c.title

                    assert not response_company
                assert not response_project
            assert not response_pp
        assert response_instance.pop("created_at")
        assert response_instance.pop("updated_at")
        assert not response_instance


class TestDeletedParentsDeleted:
    @staticmethod
    @pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
    def test__deleted_company__fail(
        api_client,
        monkeypatch,
        r_cu,
        get_project_scheme_fi,
        get_company_partnership_fi,
        get_project_partnership_fi,
        get_company_fi,
        new_project_scheme_partnership_data,
    ):
        monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

        invited_company = get_company_fi()
        cp = get_company_partnership_fi(inviting_company=r_cu.company, invited_company=invited_company)
        pp = get_project_partnership_fi(company_partnership=cp)
        project_scheme = get_project_scheme_fi(project=pp.project)
        data = new_project_scheme_partnership_data(project_scheme=project_scheme, project_partnership=pp)

        r_cu.company.is_deleted = True
        r_cu.company.save()
        response = _get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
        assert response.data == {
            "detail": NOT_TA_RCU_REASON.format(reason=NOT_TA_COMPANY_REASON.format(reason=COMPANY_IS_DELETED))
        }

    @staticmethod
    @pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
    def test__deleted_project__fail(
        api_client,
        monkeypatch,
        r_cu,
        get_project_scheme_fi,
        get_company_partnership_fi,
        get_project_partnership_fi,
        get_company_fi,
        new_project_scheme_partnership_data,
    ):
        monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: True)

        invited_company = get_company_fi()
        cp = get_company_partnership_fi(inviting_company=r_cu.company, invited_company=invited_company)
        pp = get_project_partnership_fi(company_partnership=cp)
        project_scheme = get_project_scheme_fi(project=pp.project)
        data = new_project_scheme_partnership_data(project_scheme=project_scheme, project_partnership=pp)

        pp.project.is_deleted = True
        pp.project.save()
        response = _get_response(api_client, data, r_cu.user, status_codes=ValidationError)
        assert response.data == {
            "project_scheme": [
                NOT_TA_PROJECT_SCHEME_REASON.format(
                    reason=NOT_TA_PROJECT_REASON.format(reason=PROJECT_IS_DELETED)
                )
            ]
        }


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize(
    ("is_user", "field", "err_text"),
    (
        (True, "is_blocked", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_BLOCKED)),
        (True, "is_deleted", NOT_TA_REQUESTING_USER_REASON.format(reason=USER_IS_DELETED)),
        (False, "is_deleted", REQUESTING_USER_NOT_BELONG_TO_INSTANCE_COMPANY),
    ),
)
@pytest.mark.parametrize("has_object_policy", [True, False])
def test__not_ta__cu__fail(
    api_client,
    monkeypatch,
    r_cu,
    get_project_scheme_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    get_company_fi,
    new_project_scheme_partnership_data,
    has_object_policy,
    is_user,
    field,
    err_text,
):
    monkeypatch.setattr(Policies, "has_object_policy", lambda *a, **kw: has_object_policy)
    monkeypatch.setattr(CompanyUser, "delete_policies", lambda *a, **kw: None)

    invited_company = get_company_fi()
    cp = get_company_partnership_fi(inviting_company=r_cu.company, invited_company=invited_company)
    pp = get_project_partnership_fi(company_partnership=cp)
    project_scheme = get_project_scheme_fi(project=pp.project)
    data = new_project_scheme_partnership_data(project_scheme=project_scheme, project_partnership=pp)

    if is_user:
        setattr(r_cu.user, field, True)
        r_cu.user.save()
    else:
        setattr(r_cu, field, True)
        r_cu.save()
    response = _get_response(api_client, data, r_cu.user, status_codes=PermissionDenied)
    assert response.data == {"detail": err_text}
