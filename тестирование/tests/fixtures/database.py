import pytest
from django.db import connections
from django.conf import settings

from ma_saas.settings import DATABASES


@pytest.fixture(scope="session")
def django_db_setup():
    settings.DATABASES = DATABASES
    yield

    for connection in connections.all():
        connection.close()
