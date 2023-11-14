from django.db.models import Func

# from clickhouse_backend import models
from django.db import models as django_model
from django_clickhouse.models import ClickHouseSyncModel
from django.db import models


class Service(django_model.IntegerChoices):
    """
    Маппинг статусов Компани-Юзера.

    Хранит соотношения текстовго значения и числа, хранящегося в базе данных.

    Имеется ограничение для очередности о изменений статусов для фронта.
    Смотреть COMPANY_USER_STATUS_UPDATING_SEQUENCE_MAP.
    """

    MaDirect_local = 1
    MaDirect_dev = 2
    MaDirect_test = 3
    MaDirect_stage = 4
    MaDirect_prod = 5


class EventType(django_model.IntegerChoices):
    """
    Маппинг статусов Компани-Юзера.

    Хранит соотношения текстовго значения и числа, хранящегося в базе данных.

    Имеется ограничение для очередности о изменений статусов для фронта.
    Смотреть COMPANY_USER_STATUS_UPDATING_SEQUENCE_MAP.
    """

    NOTHING = 1
    CREATE = 2
    UPDATE = 3
    DELETE = 4
    LOADED = 5


class Event(ClickHouseSyncModel):
    # service = models.StringField(max_length=32, help_text="dev, stage, prod")
    service_instance = models.IntegerField(
        choices=Service.choices,
        default=Service.MaDirect_dev.value,
        help_text=
        """
            MaDirect_local = 1
            MaDirect_dev = 2
            MaDirect_test = 3
            MaDirect_stage = 4
            MaDirect_prod = 5
        """
    )
    instance_type = models.CharField(max_length=255, help_text="Название сущности")
    instance_id = models.IntegerField(blank=True, null=True)
    user_id = models.IntegerField(blank=True, null=True)
    company_id = models.IntegerField(blank=True, null=True)
    project_id = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    event_type = models.IntegerField(
        choices=EventType.choices, default=EventType.NOTHING.value,
                                   help_text="created, updated, deleted")
