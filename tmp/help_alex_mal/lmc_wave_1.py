import sys
import os
import io
import csv
from dataclasses import dataclass
from typing import Optional, Union
import csv
import json
import re
import pandas as pd

csv.field_size_limit(sys.maxsize)


def safe_get(collection, idx=0, default=None):
    try:
        return collection[idx]
    except (IndexError, KeyError):
        return default


def generate_csv(
        file_fields: list[str], values: list[dict], file_path: str
):
    string_io = io.StringIO()
    writer = csv.writer(string_io)
    writer.writerow(file_fields)
    [writer.writerow([value[ff] for ff in file_fields]) for value in values]

    with open(file_path, "wb") as f:
        f.write(string_io.getvalue().encode())


@dataclass
class GeoPoint:
    id: Optional[int]
    is_deleted: Optional[bool]
    deleted_at: Optional[str]
    project_territory: Optional[str]
    title: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    city: Optional[str]
    address: Optional[str]
    additional: Optional[dict]
    is_active: Optional[bool]
    reward: Optional[float]
    utc_offset: Optional[float]
    timezone_name: Optional[str]
    timezone: Optional[int]
    max_reports_qty: Optional[int]


@dataclass
class Report:
    id: Optional[int]
    is_deleted: Optional[bool]
    deleted_at: Optional[str]
    company_user: Optional[int]
    processed_report_form: Optional[int]
    processed_report_form_version: Optional[int]
    worker_report: Optional[int]
    status: Optional[int]
    created_at: Optional[str]
    partner_status: Optional[str]
    partner_accepted_at: Optional[str]
    json_fields: Optional[list]
    levels: Optional[list]
    comment: Optional[str]
    geo_point: GeoPoint


def parse_bool(value):
    if value.lower() in ('true', '1'):
        return True
    elif value.lower() in ('false', '0', ''):
        return False
    else:
        return None


def parse_float(value):
    try:
        return float(value)
    except ValueError:
        return None


def parse_int(value):
    try:
        return int(value)
    except ValueError:
        return None


def parse_record(row):
    print('>>> parse_record')
    pattern = re.compile('(?<!\\\\)\'')
    additional = row.get('GeoPoint_additional')
    print('additional 1=', additional)
    if additional:
        additional = pattern.sub('"', additional).replace("False", "false").replace("True", "true")
    print('additional 2=', additional)
    geo_point = GeoPoint(
        id=parse_int(row['GeoPoint_id']),
        is_deleted=parse_bool(row['GeoPoint_is_deleted']),
        deleted_at=row['GeoPoint_deleted_at'],
        project_territory=row['GeoPoint_project_territory'],
        title=row['GeoPoint_title'],
        lat=parse_float(row['GeoPoint_lat']),
        lon=parse_float(row['GeoPoint_lon']),
        city=row['GeoPoint_city'],
        address=row['GeoPoint_address'],
        additional=json.loads(additional),
        is_active=parse_bool(row['GeoPoint_is_active']),
        reward=parse_float(row['GeoPoint_reward']),
        utc_offset=parse_float(row['GeoPoint_utc_offset']),
        timezone_name=row['GeoPoint_timezone_name'],
        timezone=parse_int(row['GeoPoint_timezone']),
        max_reports_qty=parse_int(row['GeoPoint_max_reports_qty'])

    )

    json_fields = row['json_fields']
    levels = row['levels']
    record = Report(
        id=parse_int(row['id']),
        is_deleted=parse_bool(row['is_deleted']),
        deleted_at=row['deleted_at'],
        company_user=parse_int(row['company_user']),
        processed_report_form=parse_int(row['processed_report_form']),
        processed_report_form_version=parse_int(row['processed_report_form_version']),
        worker_report=parse_int(row['worker_report']),
        status=parse_int(row['status']),
        created_at=row.get('created_at'),
        partner_status=row['partner_status'],
        partner_accepted_at=row['partner_accepted_at'],
        json_fields=json.loads(json_fields),
        levels=json.loads(levels),
        comment=row['comment'],
        geo_point=geo_point
    )

    return record


def get_element(data, key):
    print(data.get("key"))

    if key in data:
        return data


def representation_value(value: Union[str, list]):
    if not value:
        return ""

    if type(value) is list:
        result = []
        for data in value:
            if not data:
                continue
            result.append(str(data))
        return "\n".join(result)

    return value


# type - in or key
def find_in_processed_report_element(item: list, key: str, type: str):
    for data in item:
        # print(data)
        if type == "key":
            if data.get("key") == key:
                return representation_value(data.get("values"))
        else:
            if key in data:
                return representation_value(data.get(key))


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: script.py <folder>")
        sys.exit(1)
    print(1)
    folder = args[0]
    out_folder = os.path.join(folder, "tmp", "background", "out")
    print(2)
    in_file_path = os.path.join(folder, 'raw_data.csv')
    out_file_path_csv = os.path.join(out_folder, "out.csv")
    out_file_path_xls = os.path.join(out_folder, "wave_1.xlsx")
    print(3)
    reports: list[Report] = []
    result: list[dict] = []
    # Открываем файл
    print(4)
    with open(in_file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            report = parse_record(row)
            reports.append(report)
    print(5)
    tmp_data = dict()
    reports_key = "reports_data"
    print('tmp_data 1=', tmp_data)
    for index, report in enumerate(reports):
        print('index =', index)
        print('report =', report)
        region_lmc = report.levels.get("1")
        if region_lmc:
            region_lmc = region_lmc[0].get("title")

        city_lmc = report.levels.get("2")
        if city_lmc:
            city_lmc = city_lmc[0].get("title")

        gp_key = report.geo_point.address
        print('gp_key =', gp_key)
        if not tmp_data.get(gp_key):
            tmp_data[gp_key] = {
                "Сеть": report.geo_point.title,
                "Регион": region_lmc,
                "Город": city_lmc,
                "Адрес": report.geo_point.address,
                "Дата визита": report.created_at,
            }
            tmp_data[gp_key][reports_key] = []

        # out_data = dict('')
        out_data = {
            # "Сеть": report.geo_point.title,
            # "Регион": region_lmc,
            # "Город": city_lmc,
            # "Адрес": report.geo_point.address,
            # "Дата визита": report.created_at,
            # "report_id": report.id,
            "test": 'test',
        }
        print('out_data =1', out_data)
        for data in report.json_fields:
            if type(data) is dict:
                continue
            out_data_child1 = {}
            out_data_child2 = {}
            out_data_child3 = {}
            out_data_child4 = {}
            if find_in_processed_report_element(data, "text-input-2258", "key"):
                out_data_child1 = {
                    "Оборудование 1": find_in_processed_report_element(data, "text-input-2258", "key"),
                    "Кол-во 1": find_in_processed_report_element(data, "number-input-156", "key"),
                    "Комментарий 1": find_in_processed_report_element(data, "select-input-370", "key"),
                    "Фото 1": find_in_processed_report_element(data, "photo-input-8594", "key"),
                }
            if find_in_processed_report_element(data, "branch-dictionary-content-5939", "key"):
                out_data_child2 = {
                    "Оборудование 2": find_in_processed_report_element(data, "branch-dictionary-content-5939", "key"),
                    "Кол-во 2": find_in_processed_report_element(data, "number-input-7033", "key"),
                    "Комментарий 2": find_in_processed_report_element(data, "select-input-6077", "key"),
                    "Фото 2": find_in_processed_report_element(data, "photo-input-9760", "key")
                }
            if find_in_processed_report_element(data, "branch-dictionary-content-6586", "key"):
                out_data_child3 = {
                    "Оборудование 3": find_in_processed_report_element(data, "branch-dictionary-content-6586", "key"),
                    "Кол-во 3": find_in_processed_report_element(data, "number-input-6812", "key"),
                    "Комментарий 3": find_in_processed_report_element(data, "select-input-6109", "key"),
                    "Фото 3": find_in_processed_report_element(data, "photo-input-5164", "key")
                }
            if find_in_processed_report_element(data, "branch-dictionary-content-2263", "key"):
                out_data_child4 = {
                    "Оборудование 4": find_in_processed_report_element(data, "branch-dictionary-content-2263", "key"),
                    "Кол-во 3": find_in_processed_report_element(data, "number-input-1831", "key"),
                    "Комментарий 3": find_in_processed_report_element(data, "select-input-587", "key"),
                    "Фото 3": find_in_processed_report_element(data, "photo-input-7953", "key")
                }
            # out_data.update(out_data_child)
            out_data = {**out_data, **out_data_child1, **out_data_child2, **out_data_child3, **out_data_child4}
        print('out_data =2', out_data)
        tmp_data[gp_key][reports_key].append(out_data)
        print('tmp_data 1 -> =', tmp_data)

    print('tmp_data 2 =', tmp_data)
    for gp_id, v in tmp_data.items():
        print('gp_id =', gp_id)
        print('v =', v)
        reports_data = v.pop(reports_key)
        report_data_first = reports_data[0]
        report_data_first = {f"волна 1 {k}": v for k, v in report_data_first.items()}
        report_data_last = reports_data[-1]
        report_data_last = {f"волна 2 {k}": v for k, v in report_data_last.items()}
        d = {**v, **report_data_first, **report_data_last}
        print('d =', d)
        result.append(d)
    print('result =', result)
    generate_csv(list(result[0].keys()), result, out_file_path_csv)
    data = pd.read_csv(out_file_path_csv)
    data.to_excel(out_file_path_xls, index=False)
    os.remove(out_file_path_csv)


if __name__ == "__main__":
    main()
