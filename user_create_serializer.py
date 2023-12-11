from ma_saas.utils import system


class UserCreateUpdateSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ("id", "phone", "first_name", "last_name", "email", "companies_users")

    def create(self, data):
        data.pop("creator")
        companies_users = data.pop("companies_users")

        entity = User.objects.create(**data)
        password = User.objects.make_random_password()

        if companies_users is not None:
            for cu in companies_users:
                company = Company.objects.get(pk=cu["company"]["id"])
                cu.pop("company")

                cu = CompanyUser.objects.create(user=entity, company=company, **cu)

                if cu.role == "worker":
                    sms_text = "Вы приглашены как полевой сотрудник в компанию "
                    sms_text += company.title
                    sms_text += (
                        ". Для принятия участия в работе, войдите в приложение MillionAgents SAAS"
                    )
                    sms_text += " с логином " + entity.phone + " и паролем " + password
                    Sms(sms_text, entity.phone).send()
                elif cu.role == "manager" or cu.role == "admin":
                    Email(
                        "Приглашение на работу в компанию " + company.title,
                        "welcome.html",
                        "noreply@millionagents.com",
                        entity.email,
                        {
                            "company_name": company.title,
                            "email": entity.email,
                            "password": password,
                        },
                    ).send()

        entity.set_password(password)
        entity.save()

        return entity



"""
WIP SAAS-769 Правки полиси (бэк)

https://millionagents.atlassian.net/browse/SAAS-769

- перенести проверки активности сущностей из 
- добавить фильтры и поиск по юзернейму в админке
- количество пользователей на одной страничке в админке увеличено до 150

1) приглашать новых пользователей company_user/create
2) пофикшено ранее. Удалять пользователей company_user/delete
3) Просмотр выплат billing/read - требуются эндпоинты
4) Доступ в раздел фоновые процессы background_task/read - требуется перепроверить
5) Создание фоновых процессов background_task/create - требуется перепроверить
6) Удаление исполнителей worker_user/delete - пофиксил
7) Приглашение исполнителя в проекто-территорию worker_user/create - требуется проверить заново
8) Одобрение отчетов исполнителя worker_report/update, Создание отчетов менеджера manager_report/create - было пофикшено 3 марта
9) Чтение отчетов менеджера manager_report/read - требуется проверка заново
10) Удаление Гео-Точек geo_point/delete - тут нужно фронт переделать. Метод на удаление есть.
11) Удаление проекто-территории project_territory/delete - требуется повторная проверка
12) Создание проекто-территории project_territory/create - требуется повторная проверка
13) Экспорт отчетов manager_report/export - я перевел все в пермишенах только на овнера, тесты работают. Дорабатывал тут логику. требуется повторная проверка.
14) Убрать "Просмотр компаний company/read" - в полюсях убрал, на деве и проде
15) Настройка прав пользователей user_policy/all - это фронтовая задача?
16) Пригласить нового исполнителя worker_user/create - а право на менеджера требуется?
17) Импорт пользователей company_user/import - а я понял, company_user/create делится на 2
18) иерархия 2 уровня: оунер и все остальные. - ну это фронт, только тут требудется пройтись посмотреть скорее всего при праве на редактирование, можно отредактировать овнера.
"""


def get_queryset(self, *args, **kwargs):
    queryset = super().get_queryset(*args, **kwargs)
    now = system.get_now()

    # today = now.replace(hour=00, minute=00, second=00, microsecond=00)

    # project_schemes_ids =
    # project_territory_ids =
    # time_intervals =
    sts_queryset = ScheduleTimeSlot.objects.existing().filter(
        active_since__gte=now, geo_point__project_territory_id=OuterRef("id"),
    )
    wr_queryset = WorkerReport.objects.existing().filter(
        schedule_time_slot__geo_point__project_territory_id=OuterRef("id"),
    )
    pr_queryset = ProcessedReport.objects.existing().filter(
        worker_report__schedule_time_slot__geo_point__project_territory_id=OuterRef("id"),
    )
    queryset = queryset.annotate(
        schedule_time_slots_without_workers_qty=Subquery(
            sts_queryset.filter(reservations__isnull=True)
                .values("geo_point__project_territory")
                .annotate(cnt=Count("pk"))
                .values("cnt"),
            output_field=models.IntegerField(),
        ),
        schedule_time_slots_with_workers_qty=Subquery(
            sts_queryset.filter(reservations__isnull=False)
                .values("geo_point__project_territory")
                .annotate(cnt=Count("pk"))
                .values("cnt"),
            output_field=models.IntegerField(),
        ),
        worker_reports_qty=Subquery(
            wr_queryset.values("schedule_time_slot__geo_point__project_territory")
                .annotate(cnt=Count("pk"))
                .values("cnt"),
            output_field=models.IntegerField(),
        ),
        processed_reports_qty=Subquery(
            pr_queryset.values("worker_report__schedule_time_slot__geo_point__project_territory")
                .annotate(cnt=Count("pk"))
                .values("cnt"),
            output_field=models.IntegerField(),
        ),
    )

    return queryset




    # def get(self, request, *args, **kwargs):
    #     user = self.request.user
    #     accepted_cus = user.companies_users.existing().accepted().filter(user__is_blocked=False)
    #     owners_companies = accepted_cus.owners().values_list("company", flat=True)
    #
    #     ps = Policies()
    #     ps_data = dict(user_id=user.id, action_target=PolicyTargets.PROJECT, action_type=READ_ACTION_TYPES)
    #     policy_project_ids = ps.get_target_policies(**ps_data, scope_type=PolicyTargets.PROJECT)
    #     policy_project_territories_ids = ps.get_target_policies(
    #         **ps_data, scope_type=PolicyTargets.PROJECT_TERRITORY
    #     )
    #
    #     project_territories_ids, project_scheme, since, till = retrieve_query_params(request.query_params)
    #     queryset = self.queryset.filter(
    #         Q(project__company__in=owners_companies)
    #         | Q(project__in=policy_project_ids)
    #         | Q(id__in=policy_project_territories_ids),
    #         id__in=project_territories_ids
    #     )
    #     queryset = add_annotations_to_queryset(queryset, project_scheme,since, till,)
    #     return Response(queryset.values())


def add_annotations_to_queryset(queryset, project_scheme, since, till):
    print('project_scheme =', project_scheme)
    sts_queryset = ScheduleTimeSlot.objects \
        .existing().filter(
        project_scheme_id=project_scheme,
        active_since__gte=since,
        active_till__lte=till
    )
    sts_queryset = sts_queryset.filter(
        geo_point__project_territory__id=OuterRef("pk"),
    ).values()
    wr_queryset = WorkerReport.objects.existing() \
        .filter(
        created_at__lte=since,
        created_at__gte=till,
        schedule_time_slot__geo_point__project_territory__id=OuterRef("id"),
        schedule_time_slot__project_scheme__id=project_scheme
    ).values()
    pr_queryset = ProcessedReport.objects.existing() \
        .filter(
        created_at__lte=since, created_at__gte=till,
        worker_report__schedule_time_slot__geo_point__project_territory__id=OuterRef("id"),
        worker_report__schedule_time_slot__project_scheme__id=project_scheme
    ).values()

    datetime_ranges = days_range(since, till)
    for index, (day_since, day_till) in enumerate(datetime_ranges):
        sts_queryset = sts_queryset.filter(active_since__lte=day_since, active_till__gte=day_till)
        queryset = queryset.annotate(
            **get_sts_without_workers_annotation(index, sts_queryset),
            **get_sts_with_workers_annotation(index, sts_queryset),
            **get_worker_reports_annotation(index, wr_queryset, day_since, day_till),
            **get_processed_reports_qty_annotation(index, pr_queryset, day_since, day_till),
        )
    return queryset


def get_sts_without_workers_annotation(index, sts_queryset):
    return {
        f"schedule_time_slots_without_workers_qty_day_{index}": Subquery(
            sts_queryset
                .filter(reservations__isnull=True)
                .values("geo_point__project_territory")
                .annotate(cnt=Count("pk"))
                .values("cnt"),
            output_field=models.IntegerField(),
        )
    }


def get_sts_with_workers_annotation(index, sts_queryset):
    return {
        f"schedule_time_slots_with_workers_qty_day_{index}": Subquery(
            sts_queryset
                .filter(reservations__isnull=False)
                .values("geo_point__project_territory")
                .annotate(cnt=Count("pk"))
                .values("cnt"),
            output_field=models.IntegerField(),
        )
    }


def get_worker_reports_annotation(index, wr_queryset, day_since, day_till):
    return {
        f"worker_reports_qty_day_{index}": Subquery(
            wr_queryset.filter(created_at__lte=day_since, created_at__gte=day_till)
                .values("schedule_time_slot__geo_point__project_territory")
                .annotate(cnt=Count("pk"))
                .values("cnt"),
            output_field=models.IntegerField(),
        )
    }


def get_processed_reports_qty_annotation(index, pr_queryset, day_since, day_till):
    return {
        f"processed_reports_qty_day_{index}": Subquery(
            pr_queryset.filter(created_at__lte=day_since, created_at__gte=day_till)
                .values("worker_report__schedule_time_slot__geo_point__project_territory")
                .annotate(cnt=Count("pk"))
                .values("cnt"),
            output_field=models.IntegerField(),
        )
    }


def days_range(since, till):
    start_day = since
    data = []
    for n in range(int((till - since).days)):
        next_start_data = since + timedelta(n)
        data.append((start_day, next_start_data))
        start_day = next_start_data
    return data[1:]


def retrieve_required_query_param(query_params: dict, name: str):
    if query_param := query_params.get(name):
        return query_param
    raise ValidationError(f"Значение {name} в строке поиска обязательно")



"""
SELECT 
gp.project_territory_id,
EXTRACT(DAY FROM st.active_since) AS day,
(COUNT(1) FILTER (WHERE NOT EXISTS(SELECT 1 FROM tasks_reservation tr WHERE tr.schedule_time_slot_id = st.id))) AS schedule_time_slots_without_workers_qty,
(COUNT(1) FILTER (WHERE EXISTS(SELECT 1 FROM tasks_reservation tr WHERE tr.schedule_time_slot_id = st.id))) AS schedule_time_slots_with_workers_qty,
(COUNT(1) FILTER (WHERE EXISTS(SELECT 1 FROM reports_workerreport wr WHERE wr.schedule_time_slot_id = st.id))) AS worker_reports_qty,
(COUNT(1) FILTER (WHERE EXISTS(SELECT 1 FROM reports_workerreport wr INNER JOIN reports_processedreport pr ON pr.worker_report_id = wr.id WHERE wr.schedule_time_slot_id = st.id))) AS processed_reports_qty
FROM tasks_scheduletimeslot st
INNER JOIN geo_objects_geopoint gp ON st.geo_point_id = gp.id
WHERE gp.project_territory_id IN (70) AND st.project_scheme_id = 2 AND st.active_since >= '2022-03-01 00:00:00' AND st.active_till < '2022-04-27 00:00:00'
GROUP BY gp.project_territory_id, EXTRACT(DAY FROM st.active_since);


SELECT 
  gp.project_territory_id,
  EXTRACT(DAY FROM st.active_since) AS day,
  (COUNT(1) FILTER (WHERE NOT EXISTS(SELECT 1 FROM tasks_reservation tr WHERE tr.schedule_time_slot_id = st.id))) AS schedule_time_slots_without_workers_qty,
  (COUNT(1) FILTER (WHERE EXISTS(SELECT 1 FROM tasks_reservation tr WHERE tr.schedule_time_slot_id = st.id))) AS schedule_time_slots_with_workers_qty,
  (COUNT(1) FILTER (WHERE EXISTS(SELECT 1 FROM reports_workerreport wr WHERE wr.schedule_time_slot_id = st.id))) AS worker_reports_qty,
  (COUNT(1) FILTER (WHERE EXISTS(SELECT 1 FROM reports_workerreport wr INNER JOIN reports_processedreport pr ON pr.worker_report_id = wr.id WHERE wr.schedule_time_slot_id = st.id))) AS processed_reports_qty
FROM tasks_scheduletimeslot st
INNER JOIN geo_objects_geopoint gp ON st.geo_point_id = gp.id
WHERE gp.project_territory_id IN (1968,1969) AND st.project_scheme_id = 68259 AND st.active_since >= '2022-03-01 00:00:00' AND st.active_till < '2022-04-27 00:00:00'
GROUP BY gp.project_territory_id, EXTRACT(DAY FROM st.active_since); 
"""



"""
SELECT 
  gp.project_territory_id,
  EXTRACT(MONTH FROM st.active_since_local) AS month,
  EXTRACT(DAY FROM st.active_since_local) AS day,
  (COUNT(1) FILTER (WHERE NOT EXISTS(SELECT 1 FROM tasks_reservation tr WHERE tr.schedule_time_slot_id = st.id))) AS schedule_time_slots_without_workers_qty,
  (COUNT(1) FILTER (WHERE EXISTS(SELECT 1 FROM tasks_reservation tr WHERE tr.schedule_time_slot_id = st.id))) AS schedule_time_slots_with_workers_qty,
  (COUNT(1) FILTER (WHERE EXISTS(SELECT 1 FROM reports_workerreport wr WHERE wr.schedule_time_slot_id = st.id))) AS worker_reports_qty,
  (COUNT(1) FILTER (WHERE EXISTS(SELECT 1 FROM reports_workerreport wr INNER JOIN reports_processedreport pr ON pr.worker_report_id = wr.id WHERE wr.schedule_time_slot_id = st.id))) AS processed_reports_qty
FROM tasks_scheduletimeslot st
INNER JOIN geo_objects_geopoint gp ON st.geo_point_id = gp.id
WHERE gp.project_territory_id IN (1968) 
AND st.project_scheme_id = 68258
AND st.active_since_local >= '2022-03-01 00:00:00' 
AND st.active_till_local <= '2022-04-03 00:00:00'
GROUP BY gp.project_territory_id, EXTRACT(DAY FROM st.active_since_local), EXTRACT(MONTH FROM st.active_since_local)
;



SELECT 
    gp.project_territory_id,
    EXTRACT(YEAR FROM st.active_since_local) AS year,
    EXTRACT(MONTH FROM st.active_since_local) AS month,
    EXTRACT(DAY FROM st.active_since_local) AS day,
    (COUNT(1) FILTER (WHERE NOT EXISTS(SELECT 1 FROM tasks_reservation tr WHERE tr.schedule_time_slot_id = st.id))) AS schedule_time_slots_without_workers_qty,
    (COUNT(1) FILTER (WHERE EXISTS(SELECT 1 FROM tasks_reservation tr WHERE tr.schedule_time_slot_id = st.id))) AS schedule_time_slots_with_workers_qty,
    (COUNT(1) FILTER (WHERE EXISTS(SELECT 1 FROM reports_workerreport wr WHERE wr.schedule_time_slot_id = st.id))) AS worker_reports_qty,
    (COUNT(1) FILTER (WHERE EXISTS(SELECT 1 FROM reports_workerreport wr INNER JOIN reports_processedreport pr ON pr.worker_report_id = wr.id WHERE wr.schedule_time_slot_id = st.id))) AS processed_reports_qty
FROM tasks_scheduletimeslot st
INNER JOIN geo_objects_geopoint gp ON st.geo_point_id = gp.id
WHERE gp.project_territory_id IN (1968) 
    AND st.project_scheme_id = 68258
    AND st.active_since_local >= '2022-03-01 00:00:00' 
    AND st.active_till_local <= '2022-04-03 00:00:00'
GROUP BY gp.project_territory_id, 
    EXTRACT(MONTH FROM st.active_since_local),
    EXTRACT(YEAR FROM st.active_since_local),
    EXTRACT(DAY FROM st.active_since_local)
;

"""





"""
# запрос с полем processed reports


SELECT 
    gp.project_territory_id,
    EXTRACT(YEAR FROM st.active_since_local) AS year,
    EXTRACT(MONTH FROM st.active_since_local) AS month,
    EXTRACT(DAY FROM st.active_since_local) AS day,
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
    ) AS worker_reports_qty,
    (COUNT(1) FILTER (
        WHERE EXISTS (
            SELECT 1 FROM reports_workerreport wr 
                INNER JOIN reports_processedreport pr ON pr.worker_report_id = wr.id 
                WHERE wr.schedule_time_slot_id = st.id
                AND wr.is_deleted = false
        )
    )) AS processed_reports_qty
FROM tasks_scheduletimeslot st
    INNER JOIN geo_objects_geopoint gp ON st.geo_point_id = gp.id 
    WHERE gp.project_territory_id IN ({','.join(map(str, clean_pts_ids))}) 
        {{scheme_query}}
        AND st.active_since_local >= '{str(active_since_local)}' 
        AND st.active_till_local <= '{str(active_till_local)}'
        AND st.is_deleted = false
GROUP BY gp.project_territory_id, 
    EXTRACT(MONTH FROM st.active_since_local),
    EXTRACT(YEAR FROM st.active_since_local),
    EXTRACT(DAY FROM st.active_since_local)
;





def form_response_data(row):
    response_data = {}
    for (
        project_territory_id,
        year,
        month,
        day,
        schedule_time_slots_without_workers_qty,
        schedule_time_slots_with_workers_qty,
        worker_reports_qty,
        processed_reports_qty,
    ) in row:
        if project_territory_id not in response_data.keys():
            response_data[project_territory_id] = {}

        response_data[project_territory_id][
            f"{int(year)}-{'{:02d}'.format(int(month))}-{'{:02d}'.format(int(day))}"
        ] = dict(
            schedule_time_slots_without_workers_qty=schedule_time_slots_without_workers_qty,
            schedule_time_slots_with_workers_qty=schedule_time_slots_with_workers_qty,
            worker_reports_qty=worker_reports_qty,
            processed_reports_qty=processed_reports_qty,
        )
    return response_data
"""