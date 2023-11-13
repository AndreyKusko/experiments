from billing.models import BillingTransaction
from ma_saas.constants.background_task import BackgroundTaskType

PATH = "/api/v1/export-transactions-receipts/"
TASK_TYPE = BackgroundTaskType.EXPORT_TRANSACTIONS_RECEIPTS.value
MODEL_NAME = BillingTransaction._meta.concrete_model.__name__
MODEL_N_TYPE = dict(task_type=TASK_TYPE, model_name=MODEL_NAME)
