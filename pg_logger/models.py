from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import JSONField

from companies.models.company_user import CompanyUser
from ma_saas.models.time import CreatedModel

User = get_user_model()


class PgLogLVL(models.IntegerChoices):
    """
    """

    debug = 1
    info = 2
    warning = 3
    error = 4
    critical = 5

PgLogLVL_map = dict(PgLogLVL.choices)


class PgLog(CreatedModel, models.Model):
    """
    Модель для лога в постресе.
    """

    level = models.IntegerField(choices=PgLogLVL.choices)

    user = models.ForeignKey(User, on_delete=models.PROTECT, blank=True, null=True)
    company_user = models.ForeignKey(CompanyUser, on_delete=models.PROTECT, blank=True, null=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    content_object = GenericForeignKey('content_type', 'object_id')
    object_id = models.PositiveIntegerField()

    message = models.CharField(max_length=256)
    params = JSONField()

