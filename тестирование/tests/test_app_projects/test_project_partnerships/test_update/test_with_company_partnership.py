import pytest
from rest_framework.exceptions import ValidationError

from ma_saas.constants.company import CPS
from ma_saas.constants.project import PPS
from projects.models.project_partnership import ProjectPartnership
from companies.models.company_partnership import (
    COMPANY_PARTNERSHIP_INVITED_STATUS_MUST_BE_ACCEPT,
    COMPANY_PARTNERSHIP_INVITING_STATUS_MUST_BE_ACCEPT,
)
from tests.test_app_projects.test_project_partnerships.test_update.test_common import __get_response


@pytest.mark.parametrize(("cps_invited_status", "cps_inviting_status"), [(CPS.ACCEPT, CPS.ACCEPT)])
@pytest.mark.parametrize(
    ("pps_old_ed_status", "pps_new_ed_status", "pps_inviting_status"),
    [
        (PPS.ACCEPT, PPS.CANCEL, PPS.INVITE),
        (PPS.ACCEPT, PPS.CANCEL, PPS.ACCEPT),
        (PPS.ACCEPT, PPS.CANCEL, PPS.CANCEL),
        (PPS.INVITE, PPS.ACCEPT, PPS.INVITE),
        (PPS.INVITE, PPS.ACCEPT, PPS.ACCEPT),
        (PPS.INVITE, PPS.ACCEPT, PPS.CANCEL),
        (PPS.INVITE, PPS.CANCEL, PPS.INVITE),
        (PPS.INVITE, PPS.CANCEL, PPS.ACCEPT),
        (PPS.INVITE, PPS.CANCEL, PPS.CANCEL),
    ],
)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__update_invited_pps__with_accept_cps_statuses__success(
    api_client,
    mock_policies_false,
    r_cu,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    cps_invited_status,
    cps_inviting_status,
    pps_old_ed_status,
    pps_new_ed_status,
    pps_inviting_status,
):
    project = get_project_fi()
    cp = get_company_partnership_fi(
        invited_company=r_cu.company,
        inviting_company=project.company,
        invited_company_status=cps_invited_status.value,
        inviting_company_status=cps_inviting_status.value,
    )
    pp_data = {"project": project, "company_partnership": cp}
    instance = get_project_partnership_fi(
        **pp_data,
        invited_company_status=pps_old_ed_status.value,
        inviting_company_status=pps_inviting_status.value
    )
    assert instance.invited_company_status == pps_old_ed_status
    assert instance.invited_company_status != pps_new_ed_status
    data = {"invited_company_status": pps_new_ed_status.value}
    response = __get_response(api_client, instance.id, data, user=r_cu.user)
    updated_instance = ProjectPartnership.objects.get(id=instance.id)
    assert response.data["id"] == instance.id
    assert updated_instance.invited_company_status != pps_old_ed_status
    assert updated_instance.invited_company_status == pps_new_ed_status


@pytest.mark.parametrize(
    ("cps_invited_status", "cps_inviting_status"), [(CPS.ACCEPT, CPS.ACCEPT), (CPS.INVITE, CPS.ACCEPT)]
)
@pytest.mark.parametrize(
    ("pps_old_inviting_status", "pps_new_inviting_status", "pps_invited_status"),
    [
        (PPS.ACCEPT, PPS.CANCEL, PPS.INVITE),
        (PPS.ACCEPT, PPS.CANCEL, PPS.ACCEPT),
        (PPS.ACCEPT, PPS.CANCEL, PPS.CANCEL),
    ],
)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__update_inviting_pps__with_accept_cps_statuses__success(
    api_client,
    mock_policies_false,
    r_cu,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    cps_invited_status,
    cps_inviting_status,
    pps_old_inviting_status,
    pps_new_inviting_status,
    pps_invited_status,
):
    assert pps_old_inviting_status != pps_new_inviting_status

    project = get_project_fi(company=r_cu.company)
    cp = get_company_partnership_fi(
        invited_company=r_cu.company,
        invited_company_status=cps_invited_status.value,
        inviting_company_status=cps_inviting_status.value,
    )
    pp_data = {"project": project, "company_partnership": cp}
    instance = get_project_partnership_fi(
        **pp_data,
        invited_company_status=pps_invited_status.value,
        inviting_company_status=pps_old_inviting_status.value
    )
    assert instance.inviting_company_status == pps_old_inviting_status
    assert instance.inviting_company_status != pps_new_inviting_status
    data = {"inviting_company_status": pps_new_inviting_status.value}
    response = __get_response(api_client, instance.id, data, user=r_cu.user)
    updated_instance = ProjectPartnership.objects.get(id=instance.id)
    assert response.data["id"] == instance.id
    assert updated_instance.inviting_company_status != pps_old_inviting_status.value
    assert updated_instance.inviting_company_status == pps_new_inviting_status.value


@pytest.mark.parametrize(
    ("cps_invited_status", "cps_inviting_status", "err_text"),
    [
        (CPS.CANCEL, CPS.CANCEL, COMPANY_PARTNERSHIP_INVITED_STATUS_MUST_BE_ACCEPT),
        (CPS.CANCEL, CPS.ACCEPT, COMPANY_PARTNERSHIP_INVITED_STATUS_MUST_BE_ACCEPT),
        (CPS.ACCEPT, CPS.CANCEL, COMPANY_PARTNERSHIP_INVITING_STATUS_MUST_BE_ACCEPT),
        # (CPS.INVITE, CPS.ACCEPT, COMPANY_PARTNERSHIP_INVITED_STATUS_MUST_BE_ACCEPT),
    ],
)
@pytest.mark.parametrize(
    ("pps_old_ed_status", "pps_new_ed_status", "pps_inviting_status"),
    [
        (PPS.INVITE, PPS.ACCEPT, PPS.INVITE),
        (PPS.INVITE, PPS.ACCEPT, PPS.ACCEPT),
        (PPS.INVITE, PPS.ACCEPT, PPS.CANCEL),
    ],
)
@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__accept_inviting_pps__with_invalid_cps_statuses__fail(
    api_client,
    mock_policies_false,
    r_cu,
    get_project_fi,
    get_company_partnership_fi,
    get_project_partnership_fi,
    cps_invited_status,
    cps_inviting_status,
    err_text,
    pps_old_ed_status,
    pps_new_ed_status,
    pps_inviting_status,
):
    assert pps_old_ed_status != pps_new_ed_status
    project = get_project_fi()
    cp = get_company_partnership_fi(
        invited_company=r_cu.company,
        inviting_company=project.company,
        inviting_company_status=cps_inviting_status.value,
        invited_company_status=cps_invited_status.value,
    )
    partnership_data = {"project": project, "company_partnership": cp}
    instance2 = get_project_partnership_fi(
        **partnership_data,
        invited_company_status=pps_old_ed_status.value,
        inviting_company_status=pps_inviting_status.value
    )
    assert instance2.invited_company_status == pps_old_ed_status
    assert instance2.invited_company_status != pps_new_ed_status
    data = {"invited_company_status": pps_new_ed_status.value}
    response = __get_response(api_client, instance2.id, data, r_cu.user, status_codes=ValidationError)
    assert response.data["non_field_errors"][0] == err_text
    updated_instance = ProjectPartnership.objects.get(id=instance2.id)
    assert updated_instance.invited_company_status == pps_old_ed_status
