import pytest


@pytest.fixture
def document__docx_file_fi():
    with open("tests/fixtures/files/documents/document.docx", "rb") as file:
        yield file


@pytest.fixture
def document__doc_file_fi():
    with open("tests/fixtures/files/documents/document.doc", "rb") as file:
        yield file


@pytest.fixture
def document__pdf_file_fi():
    with open("tests/fixtures/files/documents/document.pdf", "rb") as file:
        yield file


@pytest.fixture
def document__txt_file_fi():
    with open("tests/fixtures/files/documents/document.txt", "rb") as file:
        yield file
