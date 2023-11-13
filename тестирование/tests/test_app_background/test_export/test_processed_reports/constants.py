from reports.models.processed_report import ProcessedReport
from ma_saas.constants.background_task import BackgroundTaskType

PATH = "/api/v1/export-processed-reports/"
TASK_TYPE = BackgroundTaskType.EXPORT_PROCESSED_REPORTS.value
MODEL_NAME = ProcessedReport._meta.concrete_model.__name__
MODEL_N_TYPE = dict(task_type=TASK_TYPE, model_name=MODEL_NAME)
