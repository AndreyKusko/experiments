import pytest
from django.forms import model_to_dict
from django.contrib.auth import get_user_model

from pg_logger.views import PgLogger, get_changed_values_data
from pg_logger.models import PgLog, PgLogLVL
from ma_saas.constants.report import ProcessedReportStatus
from ma_saas.constants.system import PgLogMsg
from companies.models.company_user import CompanyUser
from reports.models.processed_report import ProcessedReport

User = get_user_model()


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
def test__creating(get_processed_report_fi, r_cu: CompanyUser):
    pg_logger_qty = PgLog.objects.all().count()
    processed_report = get_processed_report_fi(status=ProcessedReportStatus.CREATED.value)

    pg_logger = PgLogger(object_model=ProcessedReport)
    new_data = {
        "status": ProcessedReportStatus.ACCEPTED.value,
    }
    changed_data = get_changed_values_data(old_data=model_to_dict(processed_report), new_data=new_data)
    pg_logger.info(
        instance=processed_report,
        msg=PgLogMsg.CHANGE_REPORT,
        user=r_cu.user,
        changed_data=changed_data,
    )

    pg_logs = PgLog.objects.all()
    assert pg_logger_qty < pg_logs.count()

    new_log = pg_logs.latest("id")
    assert new_log.user == r_cu.user
    assert new_log.message == PgLogMsg.CHANGE_REPORT

    assert new_log.params
    assert len(new_log.params["changed_data"]) == 2

    assert isinstance(new_log.params["changed_data"][0], dict)
    assert len(new_log.params["changed_data"][0]) == 1
    assert new_log.params["changed_data"][0]["status"] == ProcessedReportStatus.CREATED.value

    assert isinstance(new_log.params["changed_data"][1], dict)
    assert len(new_log.params["changed_data"][1]) == 1
    assert new_log.params["changed_data"][1]["status"] == ProcessedReportStatus.ACCEPTED.value


@pytest.mark.parametrize("r_cu", [pytest.lazy_fixture("cu_owner_fi")])
@pytest.mark.parametrize("log_level", PgLogLVL.names)
def test__log_levels(get_processed_report_fi, r_cu: CompanyUser, log_level: str):
    processed_report = get_processed_report_fi(status=ProcessedReportStatus.CREATED.value)
    pg_logger = PgLogger(object_model=ProcessedReport)
    log_with_lvl = getattr(pg_logger, log_level)
    log_with_lvl(instance=processed_report, msg=PgLogMsg.CHANGE_REPORT, user=r_cu.user)

    new_log = PgLog.objects.all().latest("id")

    assert new_log.level == getattr(PgLogLVL, log_level)
