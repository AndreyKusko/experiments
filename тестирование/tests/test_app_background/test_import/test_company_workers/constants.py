from companies.models.company_user import CompanyUser
from ma_saas.constants.background_task import BackgroundTaskType

PATH = "/api/v1/import-company-workers/"
TASK_TYPE = BackgroundTaskType.IMPORT_COMPANY_WORKERS.value
MODEL_NAME = CompanyUser._meta.concrete_model.__name__
MODEL_N_TYPE = dict(task_type=TASK_TYPE, model_name=MODEL_NAME)
