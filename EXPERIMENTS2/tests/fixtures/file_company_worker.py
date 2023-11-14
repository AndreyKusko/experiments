import pytest


@pytest.fixture
def workers__phone__xlsx_file_fi():
    with open(
        "tests/fixtures/files/import_company_workers/import_workers_with_phone_only.xlsx", "rb"
    ) as file:
        yield file


@pytest.fixture
def workers__phone__first_name__last_name__xlsx_file_fi():
    with open(
        "tests/fixtures/files/import_company_workers/import_workers_with_phone_firstname_lastname.xlsx", "rb"
    ) as file:
        yield file


@pytest.fixture
def workers__phone__xls_file_fi():
    with open("tests/fixtures/files/import_company_workers/import_workers_with_phone_only.xls", "rb") as file:
        yield file


@pytest.fixture
def workers__phone__txt_file_fi():
    with open("tests/fixtures/files/import_company_workers/import_workers.txt", "rb") as file:
        yield file


@pytest.fixture
def workers__phone__csv_file_fi():
    with open("tests/fixtures/files/import_company_workers/import_workers_with_phone_only.csv", "rb") as file:
        yield file


@pytest.fixture
def workers__phone__first_name__last_name__csv_file_fi():
    with open(
        "tests/fixtures/files/import_company_workers/import_workers_with_phone_firstname_lastname.csv", "rb"
    ) as file:
        yield file


@pytest.fixture
def workers__phones__docx_file_fi():
    with open("tests/fixtures/files/import_company_workers/import_workers.docx", "rb") as file:
        yield file
