from django.contrib import admin

from EXPERIMENTS.pg_logger.models import PgLog


@admin.register(PgLog,)
class PgLogAdmin(admin.ModelAdmin,):
    """PgLog admin."""

    class Meta:
        model = PgLog


