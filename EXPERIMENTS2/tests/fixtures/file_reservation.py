import pytest


@pytest.fixture
def import_reservations__via_schedule_time_slots_with_time__with_user_id__file_fi():
    with open(
        "tests/fixtures/files/import_reservations/import_reservations__via_schedule_time_slots_with_time__with_user_id.xlsx",
        "rb",
    ) as file:
        yield file


@pytest.fixture
def import_reservations__via_schedule_time_slot__without_time__with_user_id__file_fi():
    with open(
        "tests/fixtures/files/import_reservations/import_reservations__via_schedule_time_slot__without_time__with_user_id.xlsx",
        "rb",
    ) as file:
        yield file


@pytest.fixture
def import_reservations__via_geo_point_and_project_scheme_with_time__with_user_phone__file_fi():
    with open(
        "tests/fixtures/files/import_reservations/import_reservations__via_geo_point_and_project_scheme_with_time__with_user_phone.xlsx",
        "rb",
    ) as file:
        yield file


@pytest.fixture
def import_reservations__without_sts_or_gp__fail__file_fi():
    with open(
        "tests/fixtures/files/import_reservations/import_reservations__without_sts_or_gp__fail.xlsx", "rb"
    ) as file:
        yield file


@pytest.fixture
def import_reservations__without_user__fail__file_fi():
    with open(
        "tests/fixtures/files/import_reservations/import_reservations__without_user__fail.xlsx", "rb"
    ) as file:
        yield file


@pytest.fixture
def import_reservations__invalid_format__file_fi():
    with open(
        "tests/fixtures/files/import_reservations/import_reservations__invalid_format.doc", "rb"
    ) as file:
        yield file
