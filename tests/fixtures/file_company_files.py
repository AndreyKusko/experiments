import pytest


@pytest.fixture
def company_files__file_fi():
    with open("tests/fixtures/files/import_company_files/company_files.zip", "rb") as file:
        yield file


@pytest.fixture
def company_files_non_root_dir__file_fi():
    with open("tests/fixtures/files/import_company_files/company_files_non_root_dir.zip", "rb") as file:
        yield file


@pytest.fixture
def company_files_wrong_archive_extension__file_fi():
    with open(
        "tests/fixtures/files/import_company_files/company_files_wrong_archive_extension.tar",
        "rb",
    ) as file:
        yield file


@pytest.fixture
def company_files_wrong_inside_files_extensions__file_fi():
    with open(
        "tests/fixtures/files/import_company_files/company_files_wrong_inside_files_extensions.zip",
        "rb",
    ) as file:
        yield file
