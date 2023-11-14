import clickhouse_connect
from sqlalchemy import create_engine, MetaData

from main.settings import CLICKHOUSE_DATABASE, CLICKHOUSE_PASSWORD, CLICKHOUSE_USERNAME, CLICKHOUSE_HOST, \
    CLICKHOUSE_OPTIONS, CLICKHOUSE_PORT, CLICKHOUSE_URI

from clickhouse_sqlalchemy import (
    Table, make_session, get_declarative_base, types, engines
)

#
# clickhouse_client = clickhouse_connect.get_client(
#     host=CLICKHOUSE_HOST,
#     port=CLICKHOUSE_PORT,
#     # port=8443,
#     username=CLICKHOUSE_USERNAME,
#     password=CLICKHOUSE_PASSWORD,
#     database=CLICKHOUSE_DATABASE,
#     settings=CLICKHOUSE_OPTIONS,
#     # connect_timeout=15,
# )
# #
# # clickhouse_client.command(
# # """
# # CREATE TABLE event_record (
# # service_instance String,
# # model_id UInt32,
# # value String,
# # metric Float64
# # ) ENGINE MergeTree ORDER BY key
# # """
# # )
# #
# # service_instance = Column(types.String, max_length=16, help_text="dev, stage, prod")
# # model_id = Column(types.Int32, max_length=255, null=True, blank=True)
# # created_at = Column(types.DateTime, null=True, blank=True)
#
#
# engine = create_engine(CLICKHOUSE_URI)
# session = make_session(engine)
# metadata = MetaData(bind=engine)
# Base = get_declarative_base(metadata=metadata)
