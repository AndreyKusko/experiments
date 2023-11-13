import pytest


@pytest.fixture
def project_variable_values__xlsx_file_fi():
    with open(
        "tests/fixtures/files/import_project_variable_values/import_project_variable_values.xlsx", "rb"
    ) as file:
        yield file


@pytest.fixture
def project_variable_values__xls_file_fi():
    with open(
        "tests/fixtures/files/import_project_variable_values/import_project_variable_values.xls", "rb"
    ) as file:
        yield file


@pytest.fixture
def project_variable_values__missed_required_header__xlsx_file_fi():
    with open(
        "tests/fixtures/files/import_project_variable_values/import_project_variable_values__missed_required_header.xlsx",
        "rb",
    ) as file:
        yield file


@pytest.fixture
def project_variable_values__missed_required_field__xlsx_file_fi():
    with open(
        "tests/fixtures/files/import_project_variable_values/import_project_variable_values__missed_required_field.xlsx",
        "rb",
    ) as file:
        yield file
