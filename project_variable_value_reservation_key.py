from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsTotallyActiveUser
from projects.models.contractor_project_territory_worker import \
    ContractorProjectTerritoryWorker
from projects.models.project_variable_value import (
    ProjectVariableValue, ProjectVariableValueModelName)
from tasks.models.reservation import Reservation
from tasks.permissions.reservation import IsAllowedToReservation

_make_key = lambda key, model_name, model_id: f"{key}_{model_name}_{model_id}"


def make_project_variable_values_map(pvvs):
    pvv_map = {_make_key(pvv.project_variable.key, pvv.model_name, pvv.model_id): pvv.value for pvv in pvvs}
    # pvv_map = {_make_key(pvv.project_variable['key'], pvv['model_name'], pvv['model_id']): pvv.value for pvv in pvvs}
    pvv_map_keys = set(pvv_map.keys())
    return pvv_map, pvv_map_keys


def _get_value(reservation, key, pvv_map, pvv_map_keys):
    if gen_key := _make_key(key, 'reservation', reservation.id) in pvv_map_keys:
        return pvv_map[gen_key]
    if gen_key := _make_key(key, 'schedule_time_slot', reservation.schedule_time_slot.id) in pvv_map_keys:
        return pvv_map[gen_key]
    if gen_key := _make_key(key, 'project_territory', reservation.geo_point.project_territory.id) in pvv_map_keys:
        return pvv_map[gen_key]
    if gen_key := _make_key(key, 'project_scheme', reservation.schedule_time_slot.project_scheme.id) in pvv_map_keys:
        return pvv_map[gen_key]
    if gen_key := _make_key(key, 'project', reservation.schedule_time_slot.project_scheme.project.id) in pvv_map_keys:
        return pvv_map[gen_key]
    return


class ReservationSerializer(serializers.ModelSerializer):
    keys = serializers.SerializerMethodField(read_only=True)
    _query_keys = None
    _pvv_map = None
    _pvv_map_keys = None
    class Meta:
        model = Reservation
        fields = ["id", "keys"]

    def set_project_variable_value_data(self):
        raw_keys = self.context['request'].GET.get('project_variable__key__in')
        keys = raw_keys.split(',') if raw_keys else []
        if not self._pvv_map or not self._pvv_map_keys or not  self._query_keys:
            project_variable_values = ProjectVariableValue.objects.select_related(
                'project_variable').filter(
                project_variable__key__in=keys,
                project_variable__project__in=self.instance.values_list('schedule_time_slot__project_scheme__project',
                                                                        flat=True)
            )
            pvv_map, pvv_map_keys = make_project_variable_values_map(project_variable_values)
            self._pvv_map = pvv_map
            self._pvv_map_keys = pvv_map_keys
            self._query_keys = keys

    def get_keys(self, obj):
        self.set_project_variable_value_data()
        return {key: _get_value(obj, key, self._pvv_map, self._pvv_map_keys) for key in self._query_keys}


class ReservationProjectVariableValueMapApiView(mixins.ListModelMixin, viewsets.GenericViewSet):
    __doc__ = f"""
    Значение переменной проекта
    
    Маппинг значений в поле model_name:
    ProjectVariableValueModelName map:_
    {dict((key, value) for key, value in ProjectVariableValueModelName.choices)}
    """

    model = Reservation
    serializer_class = ReservationSerializer
    permission_classes = (IsAuthenticated & IsTotallyActiveUser & IsAllowedToReservation,)
    queryset = model.objects.select_related(
        'schedule_time_slot',
        'geo_point',
        'geo_point__project_territory',
        'schedule_time_slot__project_scheme',
        'schedule_time_slot__project_scheme__project'
    )
    filter_backends = (DjangoFilterBackend,)

    lookup_field = ['key']
    filterset_fields = {
        "id": ["exact", "in"],
        "geo_point": ["exact", "in"],
        "geo_point__title": ["exact", "in"],
        "geo_point__address": ["exact", "in"],
        "project_territory": ["exact", "in"],
        "project_territory__reward": ["exact", "in", "gte", "lte"],
        "project_territory__project": ["exact", "in"],
        "project_territory__territory": ["exact", "in"],
        "project_territory_worker": ["exact", "in"],
        "project_territory_worker__company_user": ["exact", "in"],
        "project_territory_worker__company_user__status": ["exact", "in"],
        "active_since": ["gte", "lte", "gt", "lt"],
        "active_since_local": ["gte", "lte", "gt", "lt"],
        "active_till": ["gte", "lte", "gt", "lt"],
        "active_till_local": ["gte", "lte", "gt", "lt"],
        "schedule_time_slot": ["in", "exact"],
        "schedule_time_slot__active_since_date": ["gte", "lte", "gt", "lt"],
        "schedule_time_slot__active_since_time": ["gte", "lte", "gt", "lt"],
        "schedule_time_slot__active_since_date_local": ["gte", "lte", "gt", "lt"],
        "schedule_time_slot__active_since_time_local": ["gte", "lte", "gt", "lt"],
        "schedule_time_slot__active_till_date": ["gte", "lte", "gt", "lt"],
        "schedule_time_slot__active_till_time": ["gte", "lte", "gt", "lt"],
        "schedule_time_slot__active_till_date_local": ["gte", "lte", "gt", "lt"],
        "schedule_time_slot__active_till_time_local": ["gte", "lte", "gt", "lt"],
    "is_deleted": ["exact"],
    "deleted_at": ["gte", "lte"],
    }
