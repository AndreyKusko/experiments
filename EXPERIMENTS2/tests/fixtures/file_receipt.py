import pytest


@pytest.fixture
def transaction_receipt__jpg_file_fi():
    with open("tests/fixtures/files/receipts/transaction_receipt.jpg", "rb") as file:
        yield file
