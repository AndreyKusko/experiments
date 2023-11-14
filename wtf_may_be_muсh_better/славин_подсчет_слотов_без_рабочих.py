class ProjectTerritoryAggregateDataApiView(APIView):
    __doc__ = f"""
    Количество таймслотов в проекто-территориях совсем без рабочих по дням.

    По-идее при наступлении времени выполнения, у тамслотов должен быть свой исполнитель. 

    Параметр project_scheme в запросе опционален
    Примеры запроса:
        curl --location --request GET 'http://127.0.0.1:8000/api/v1/project-territory-aggregate-data/?project_territory__in=1968,1969&active_till_local=2022-04-02T00:00:00.00&active_since_local=2022-03-01T00:00:00.00' --header 'Accept: application/json' --header 'authorization: Token e6c098b3c72e9525be787a86366fe591254af55e' 
        curl --location --request GET 'http://127.0.0.1:8000/api/v1/project-territory-aggregate-data/?project_territory__in=1968,1969&project_scheme=68259&active_till_local=2022-04-02T00:00:00.00&active_since_local=2022-03-01T00:00:00.00' --header 'Accept: application/json' --header 'authorization: Token e6c098b3c72e9525be787a86366fe591254af55e'

    Пример ответа:
    {'{"1968": {"2022-03-22": {"schedule_time_slots_without_workers_qty": 0, "schedule_time_slots_with_workers_qty": 1, "worker_reports_qty": 1,}, "2022-03-29": {"schedule_time_slots_without_workers_qty": 0, "schedule_time_slots_with_workers_qty": 1, "worker_reports_qty": 0}}}'}
    1968 - id проекто-территории 
    2022-3-22 - день по счету от начала периода
    """
    model = ProjectTerritory

    permission_classes = (IsAuthenticated & IsTotallyActiveUser,)
    queryset = model.objects.defer(
        "created_at", "updated_at", "is_deleted", "project_id", "territory_id", "is_active", "reward"
    )

    def get(self, request, *args, **kwargs):
        user = self.request.user
        accepted_cus = user.companies_users.existing().accepted().filter(user__is_blocked=False)
        owners_companies = accepted_cus.owners().values_list("company", flat=True)

        pts_ids, project_scheme_id, active_since_local, active_till_local = retrieve_query_params(
            request.query_params
        )
        if project_scheme_id:
            check_project_scheme_access(user, owners_companies, project_scheme_id)

        clean_pts_ids = get_and_check_project_territories_ids(self.queryset, user, owners_companies, pts_ids)
        if not clean_pts_ids:
            raise PermissionDenied()
        row = get_data_from_database(
            clean_pts_ids=clean_pts_ids,
            project_scheme_id=project_scheme_id,
            active_since_local=active_since_local,
            active_till_local=active_till_local,
        )
        response_data = form_response_data(row)

        return Response(response_data)




def get_data_from_database(
    clean_pts_ids: List[str], project_scheme_id: str, active_since_local: str, active_till_local: str
):
    active_since_local = dt.datetime.strptime(active_since_local, DATETIME_FORMAT_WITH_SPACE_WITHOUT_MS)
    active_till_local = dt.datetime.strptime(active_till_local, DATETIME_FORMAT_WITH_SPACE_WITHOUT_MS)
    query_srt = f"""
    SELECT 
        gp.project_territory_id,
        EXTRACT(YEAR FROM st.active_since_date_local) AS year,
        EXTRACT(MONTH FROM st.active_since_date_local) AS month,
        EXTRACT(DAY FROM st.active_since_date_local) AS day,
        (COUNT(1) FILTER 
            (WHERE NOT EXISTS(
                SELECT 1 FROM tasks_reservation tr 
                    WHERE tr.schedule_time_slot_id = st.id 
                    AND tr.is_deleted = false
            ))
        ) AS schedule_time_slots_without_workers_qty,
        (COUNT(1) FILTER 
            (WHERE EXISTS(
                SELECT 1 FROM tasks_reservation tr 
                    WHERE tr.schedule_time_slot_id = st.id
                    AND tr.is_deleted = false
            ))
        ) AS schedule_time_slots_with_workers_qty,
        (COUNT(1) FILTER 
            (WHERE EXISTS(
                SELECT 1 FROM reports_workerreport wr 
                    WHERE wr.schedule_time_slot_id = st.id
                    AND wr.is_deleted = false
            ))
        ) AS worker_reports_qty
    FROM tasks_scheduletimeslot st
        INNER JOIN geo_objects_geopoint gp ON st.geo_point_id = gp.id 
        WHERE gp.project_territory_id IN ({','.join(map(str, clean_pts_ids))}) 
            {{scheme_query}}
            AND st.active_since_date_local >= '{str(active_since_local.date())}' 
            AND st.active_till_date_local <= '{str(active_till_local.date())}'
            AND st.is_deleted = false
    GROUP BY gp.project_territory_id, 
        EXTRACT(MONTH FROM st.active_since_date_local),
        EXTRACT(YEAR FROM st.active_since_date_local),
        EXTRACT(DAY FROM st.active_since_date_local)
    ;
    """

    optional_query_str = f"AND st.project_scheme_id = {str(project_scheme_id)} " if project_scheme_id else ""
    query_srt = query_srt.format(scheme_query=optional_query_str)
    with connection.cursor() as cursor:
        cursor.execute(query_srt)
        row = cursor.fetchall()
    return row




"""
как он примерно должен был выглядеть. 

Только нужно еще доделать фильтрация на отсутсвие резерваций
и это займет не больше 10 строк и читабельно, а не 40+ и гребучий язык sql
"""

queryset = queryset.filter(reservations__isnull=True) \
    .annotate(day=TruncDay('active_since')) \
    .values('day') \
    .annotate(qty=Count('company_user__user__id')) \
    .values('company_user__user_id', 'day', 'qty')
