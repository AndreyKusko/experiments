from tasks.models.reservation import Reservation
from ma_saas.constants.background_task import BackgroundTaskType

PATH = "/api/v1/import-reservations/"
TASK_TYPE = BackgroundTaskType.IMPORT_RESERVATIONS.value
MODEL_NAME = Reservation._meta.concrete_model.__name__
MODEL_N_TYPE = dict(task_type=TASK_TYPE, model_name=MODEL_NAME)
