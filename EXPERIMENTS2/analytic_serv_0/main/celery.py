from __future__ import absolute_import, unicode_literals

from celery import Celery
import os

from django.apps import apps

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
celery_app = Celery("main")

celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()

