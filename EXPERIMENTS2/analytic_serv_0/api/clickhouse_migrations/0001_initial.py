
from django_clickhouse import migrations
# from django.db import migrations
from api.clickhouse_models import ClickHouseEvent


class Migration(migrations.Migration):
    operations = [
        migrations.CreateTable(ClickHouseEvent)
    ]
