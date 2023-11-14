from django.contrib import admin

from api.clickhouse_models import ClickHouseEvent
from api.models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    class Meta:
        model = Event

    list_display = [
        'id',
        'service_instance',
        'event_type',
        'instance_type',
        'company_id',
        'project_id',
        'user_id',
        'created_at'
    ]
    list_display_link = ['id']
    readonly_fields = ['created_at']




# Event.objects.create()

che = ClickHouseEvent.objects.all()
print('che =', che)

qty = ClickHouseEvent.objects.all().count()
print('qty =', qty)