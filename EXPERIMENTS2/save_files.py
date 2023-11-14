

with open("/opt/ass.xlsx", "wb") as file:
    binary_file.write(file)


def apply_task(self, instance):
    # self._task_function.apply_async(args=[instance.id], queue=settings.CELERY_QUEUE)
    # todo revert
    self._task_function.run(instance.id)


file, filename = generate_xlsx_file(worksheets=worksheets, background_task=background_task)
# todo revert
# with open(f"/opt/{filename}", "wb") as binary_file:
with open(f"/Users/andy/Documents/work/media/{filename}", "wb") as binary_file:
    binary_file.write(file)
# export_file_to_obj_store(background_task=background_task, file=file, filename=filename)


with open("/opt/ass.xlsx", "wb") as binary_file:
    binary_file.write(file)
# export_file_to_obj_store(background_task=background_task, file=file, filename=filename)

if r_cu:
    # сохраняем скоуп инициатора по модели (instance.model_name) для проверки полиси
    scope_type, scope_id = self.get_scope(instance, r_cu)
    if not (scope_type and scope_id):
        scope_type = ServicesModelsName.COMPANY
        scope_id = r_cu.company_id
    instance.params = dict(**instance.params, scope_type=scope_type, scope_id=scope_id)
    instance.save()


l = 0
for i in [["7",".",".",".","4",".",".",".","."],[".",".",".","8","6","5",".",".","."],[".","1",".","2",".",".",".",".","."],[".",".",".",".",".","9",".",".","."],[".",".",".",".","5",".","5",".","."],[".",".",".",".",".",".",".",".","."],[".",".",".",".",".",".","2",".","."],[".",".",".",".",".",".",".",".","."],[".",".",".",".",".",".",".",".","."]]:
    l+=1
    if l == 4 or l == 7:
        print(' ')
    print(i[0:3],i[3:6],i[6:])


def for_zip_export__remember_zip_as_bytes__and__remove_archive(main_folder_path):
    """
    Запомнить зип в опертивку в виде байтов и удалить его из папки

    Запомненные байты будут посланы в обжстор
    """
    zip_file_path = f"{main_folder_path}.zip"
    buf = io.BytesIO()
    with open(zip_file_path, "rb") as file_data:
        buf.write(file_data.read())
    buf.seek(0)
    # os.remove(zip_file_path)
    return buf


with open('/Users/andy/Documents/work/madirect-backend/tests/fixtures/files/import_territories.xlsx', r) as file:
    self.reader = file
@staticmethod
def get_file_content_from_obj_store(file_id):
    # todo revert
    with open("/Users/andreycheutin/Desktop/import_reservations__via_geo_point_and_project_scheme_with_time__with_user_phone1.xlsx", "rb") as file:
        return file.read()
    url = MEDIA_STORE_GET_OBJ_LINK.format(file_id)
    response = requests.get(url=url, headers={"X-Meta-Fetch": "1"})
    return response.content


@update_background_task_deco
def process_export_transactions_receipts_task(background_task: BackgroundTask):
    queryset = WorkerReportsTransaction.objects.none()

    f = WorkerReport.objects.get(id=1)
    s = WorkerReport.objects.get(id=2)
    # ff = WorkerReportsTransaction(worker_report=f, id=1)
    # queryset |= WorkerReportsTransaction(worker_report=f, id=1)
    # queryset |= WorkerReportsTransaction(worker_report=s, id=2)

    # queryset._result_cache.append(ff)
    # queryset._result_cache.append(ss)

    if ids := background_task.params.get(BackgroundTaskParamsKeys.IDS):
        queryset = queryset.filter(id__in=ids)

    if background_task.is_zip_file:
        serializer = ZipWorkerReportsTransactionsSerializer(instance=queryset, many=True)
        file, filename = generate_zip_with_structure_file(serializer=serializer, background_task=background_task)
    elif background_task.is_xlsx_file:
        result_for_archive_export = list()
        temporary_folder_path, folder_path = for_zip_folders__get_temporary_folders_path(background_task)
        # if self_employed:= queryset.filter(worker_report__is_self_employed=True):
        if self_employed := [WorkerReportsTransaction(worker_report=f, id=1)]:
            # if background_task.is_zip_file:
                # serializer = ZipWorkerReportsTransactionsSerializer(instance=self_employed, many=True)
                # file, filename = generate_zip_with_structure_file(serializer=serializer, background_task=background_task)
            # elif background_task.is_xlsx_file:
            serializer = XLSXWorkerReportsTransactionsSerializer(instance=self_employed, many=True)
            worksheets = [TransactionReceiptsWorksheetData("transactions", serializer=serializer)]
            file, filename = generate_xlsx_file(worksheets=worksheets, background_task=background_task)
            result_for_archive_export.append(File(content=file, file_name=f'самозанятые {filename}', path=folder_path))
        # if self_employed:= queryset.filter(worker_report__is_self_employed=False):
        if self_employed := [WorkerReportsTransaction(worker_report=s, id=2)]:
            serializer = XLSXWorkerReportsTransactionsSerializer(instance=self_employed, many=True)
            worksheets = [TransactionReceiptsWorksheetData("transactions", serializer=serializer)]
            file, filename = generate_xlsx_file(worksheets=worksheets, background_task=background_task)
            result_for_archive_export.append(File(content=file, file_name=f'не самозанытые {filename}', path=folder_path))
        file = make_zip_archive(files=result_for_archive_export, temporary_folder_path=temporary_folder_path)
        filename = f"{background_task.task_type}({background_task.id}) {background_task.created_at}.zip"
    else:
        raise Exception('unprocessable output file type')

    # todo revert
    export_file_to_obj_store(background_task=background_task, file=file, filename=filename)

    return background_task


# картинка со скачиванием
"https://primamediamts.servicecdn.ru/f/big/2319/2318195.jpeg?11aed3be0776b4c1f0ae84eeedff2ee2"
# картинка без скачивания (для чеков подходит)
"https://img.freepik.com/free-psd/google-icon-isolated-3d-render-illustration_47987-9777.jpg?w=2000"


"""
f = (
    WorkerReport.objects.existing()
    .filter(
        schedule_time_slot=OuterRef('id'),
        geo_point__in=queryset.values('geo_point'),
        status__in=NICE_STATUSES_WORKER_REPORT_IS_COUNTED,
        created_at__year=now.year, created_at__month=now.month, created_at__day=now.day,
    ).order_by()
    .annotate(
        total=Func(F('id'), function='Count')
    ).values('total')
)
s = (
    ScheduleTimeSlot.objects.existing()
    .filter(id__in=queryset.values_list('schedule_time_slot', flat=True))
    .annotate(total=Subquery(f))
    .values('id', 'max_reports_qty_per_day', 'max_reports_qty', 'total')
    .exclude(max_reports_qty_per_day=F('total'), max_reports_qty_per_day__gt=0)
    .values_list("id", flat=True)
)
"""
