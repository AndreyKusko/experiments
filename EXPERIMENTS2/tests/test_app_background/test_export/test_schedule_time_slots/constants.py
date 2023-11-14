from tasks.models.schedule_time_slot import ScheduleTimeSlot
from ma_saas.constants.background_task import BackgroundTaskType

PATH = "/api/v1/export-schedule-time-slots/"
TASK_TYPE = BackgroundTaskType.EXPORT_SCHEDULE_TIME_SLOTS.value
MODEL_NAME = ScheduleTimeSlot._meta.concrete_model.__name__
MODEL_N_TYPE = dict(task_type=TASK_TYPE, model_name=MODEL_NAME)
