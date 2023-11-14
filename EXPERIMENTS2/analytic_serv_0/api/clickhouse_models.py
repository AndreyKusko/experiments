from django_clickhouse.clickhouse_models import ClickHouseModel
from django_clickhouse.engines import MergeTree
from infi.clickhouse_orm import fields

from api.models import Event


class ClickHouseEvent(ClickHouseModel):
    django_model = Event

    # Uncomment the line below if you want your models to be synced automatically
    sync_enabled = True

    id = fields.UInt32Field()
    instance_type = fields.StringField()
    instance_id = fields.UInt32Field()
    user_id = fields.UInt32Field()
    company_id = fields.UInt32Field()
    project_id = fields.UInt32Field()

    created_at = fields.DateTime64Field()
    event_type = fields.UInt32Field()

    engine = MergeTree('created_at', ('created_at',))
