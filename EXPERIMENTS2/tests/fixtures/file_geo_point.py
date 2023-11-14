import pytest


@pytest.fixture
def geo_points__xlsx_file_fi():
    with open("tests/fixtures/files/import_geo_points/import_geo_points.xlsx", "rb") as file:
        yield file


@pytest.fixture
def geo_points__csv_file_fi():
    with open("tests/fixtures/files/import_geo_points/import_geo_points.csv", "rb") as file:
        yield file


@pytest.fixture
def geo_points_lost_req_field__xlsx_file_fi():
    with open(
        "tests/fixtures/files/import_geo_points/import_geo_points_lost_required_field.xlsx", "rb"
    ) as file:
        yield file


@pytest.fixture
def geo_points_lost_req_field__csv_file_fi():
    with open(
        "tests/fixtures/files/import_geo_points/import_geo_points_lost_required_field.csv", "rb"
    ) as file:
        yield file


@pytest.fixture
def geo_points_missed_required_headers__xlsx_file_fi():
    with open(
        "tests/fixtures/files/import_geo_points/import_geo_points_missed_required_headers.xlsx", "rb"
    ) as file:
        yield file


@pytest.fixture
def geo_points_missed_required_headers__csv_file_fi():
    with open(
        "tests/fixtures/files/import_geo_points/import_geo_points_missed_required_headers.csv", "rb"
    ) as file:
        yield file
