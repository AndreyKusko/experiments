from companies.models.company_file import CompanyFile
from ma_saas.constants.background_task import BackgroundTaskType

PATH = "/api/v1/import-company-files/"
TASK_TYPE = BackgroundTaskType.IMPORT_COMPANY_FILES.value
MODEL_NAME = CompanyFile._meta.concrete_model.__name__
MODEL_N_TYPE = dict(task_type=TASK_TYPE, model_name=MODEL_NAME)
