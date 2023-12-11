import psycopg2
import pytest
from django.core.management import call_command
from django.db import connections
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def run_sql(sql):
    conn = psycopg2.connect(database="postgres")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(sql)
    conn.close()


@pytest.yield_fixture(scope="session")
def django_db_setup(django_db_blocker):
    """Test session DB setup."""

    from django.conf import settings

    test_database_name = "test_saas"
    settings.DATABASES["default"]["NAME"] = test_database_name

    run_sql(f"DROP DATABASE IF EXISTS {test_database_name}")
    run_sql(f"CREATE DATABASE {test_database_name}")
    with django_db_blocker.unblock():
        call_command("migrate", "--noinput")
    """DROP USER IF EXISTS "test_user" """
    """DROP USER IF EXISTS "my_user" """
    """DROP USER IF EXISTS "django" """
    """ALTER USER ma WITH NOCREATEDB;"""
    run_sql(
        f"""
        DO
        $do$
        BEGIN
           IF NOT EXISTS (
              SELECT FROM pg_catalog.pg_roles  -- SELECT list can be empty for this
              WHERE  rolname='{settings.DATABASES['default']['USER']}') THEN
              CREATE ROLE {settings.DATABASES['default']['USER']};
           END IF;
        END
        $do$;
        """
    )
    run_sql(
        f"GRANT ALL PRIVILEGES ON DATABASE {test_database_name} TO {settings.DATABASES['default']['USER']}"
    )
    yield
    for connection in connections.all():
        connection.close()

    run_sql(f"DROP DATABASE {test_database_name}")
