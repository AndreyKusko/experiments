import json

from aiokafka import AIOKafkaConsumer

from api.models import Service
# from clients.clickhouse import clickhouse_client
from main.settings import KAFKA_USERNAME, KAFKA_PASSWORD, kafka_options, KAFKA_HOST, KAFKA_TOPIC, IS_LOCAL


async def save_message(data: dict):
    # todo change to raw sql, there is a reason to use django only for debug o
    print('>>> save_message')
    print('data =', data)
    print('sf =', getattr(Service, data["service_instance"]))
    # instance = Event.objects.create(
    #     service_instance=getattr(Service, data["service_instance"]),
    #     instance_type=data["instance_type"],
    #     instance_id=data["data"]['id'],
    #     user_id=data["data"]["user_id"],
    #     company_id=data["data"]["company_id"],
    #     project_id=data["data"]["project_id"],
    #     created_at=data["data"]["created_at"],
    #
    # )
    # INSERT INTO {Event.Meta.db_table} VALUES ({dict(
    # INSERT INTO {CLICKHOUSE_DATABASE} VALUES ({dict(

    command = f'''
        INSERT INTO event VALUES ({dict(
        service_instance=getattr(Service, data["service_instance"]),
        instance_type=data["instance_type"],
        instance_id=data["data"]['id'],
        user_id=data["data"]["user_id"],
        company_id=data["data"]["company_id"],
        project_id=data["data"]["project_id"],
        created_at=data["data"]["created_at"],
    )});
    '''
    # r = clickhouse_client.command(command)
    # print('r =', r)
    # print('instance =', instance)
    return


class AnalyticConsumerThread:
    """
    Консюмер кафки, который читает сообщения из сервисов директа

    см пример сообщения в README.md
    """
    consumer = None
    async def start(self):
        self.consumer = AIOKafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_HOST,
            sasl_plain_username=KAFKA_USERNAME,
            sasl_plain_password=KAFKA_PASSWORD,
            consumer_timeout_ms=1000,
            **kafka_options,
        )
        await self.consumer.start()
        try:
            # Consume messages
            async for msg in self.consumer:
                if not msg.value:
                    continue
                await self.message(json.loads(msg.value))
        except KeyboardInterrupt:
            print("Detected Keyboard Interrupt. Cancelling.")
            pass
        except Exception as e:
            raise e
        finally:
            # Will leave consumer group; perform autocommit if enabled.
            await self.consumer.stop()

    async def message(self, message_data):
        print('>>> message')
        print('message_data =', message_data)
        try:
            ...
            # topic = TopicValueSchema(**message_data)
            # await self.process_value(topic)
        except Exception as e:
            if IS_LOCAL:
                raise e
            # capture_exception(e)


consumer = AnalyticConsumerThread()
