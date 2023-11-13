from geo_objects.models import GeoPoint
from ma_saas.constants.background_task import BackgroundTaskType

PATH = "/api/v1/export-geo-points/"
TASK_TYPE = BackgroundTaskType.EXPORT_GEO_POINTS.value
MODEL_NAME = GeoPoint._meta.concrete_model.__name__
MODEL_N_TYPE = dict(task_type=TASK_TYPE, model_name=MODEL_NAME)
