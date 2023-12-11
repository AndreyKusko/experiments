from datetime import datetime

from ma_saas.constants.system import DATETIME_FORMAT
from ma_saas.constants.company import CUR

# роли, которые в системе используют разную логику.
# Овнер всегда имеет доступ
# Менеджер имеет доступ только при наличии полюси
# Робочий имеет доступ на чтение при принадлежности
ROLES_WITH_DIFFERENT_LOGIC = [CUR.OWNER, CUR.PROJECT_MANAGER, CUR.WORKER]
NOT_WORKER_ROLES_WITH_DIFFERENT_LOGIC = [CUR.OWNER, CUR.PROJECT_MANAGER]
NOT_OWNER_ROLES_WND_NOT_WORKER_WITH_DIFFERENT_LOGIC = [CUR.PROJECT_MANAGER]

FAKE_TIME = datetime.strptime("2020-01-01T12:01:12.0100", DATETIME_FORMAT)
