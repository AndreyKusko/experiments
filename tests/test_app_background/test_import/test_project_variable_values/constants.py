from ma_saas.constants.background_task import BackgroundTaskType
from projects.models.project_variable_value import ProjectVariableValue

PATH = "/api/v1/import-project-variable-values/"
TASK_TYPE = BackgroundTaskType.IMPORT_PROJECT_VARIABLE_VALUES.value
MODEL_NAME = ProjectVariableValue._meta.concrete_model.__name__
MODEL_N_TYPE = dict(task_type=TASK_TYPE, model_name=MODEL_NAME)
