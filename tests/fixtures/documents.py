import typing as tp
from typing import Callable

import pytest

from ma_saas.settings import REALM_ID


@pytest.fixture
def docshub_document_response_fi() -> Callable:
    def create_instance(company_id: int, version: int = 2) -> tp.Dict[str, tp.Union[int, str]]:
        return {
            "id": 75,
            "doc_type": "law",
            "title": "Тестовое общение",
            "is_active": True,
            "version": version,
            "description": "ы",
            "key": "testovoe_obschenie",
            "realm_id": REALM_ID,
            "company_id": company_id,
            "created_at": "2021-06-24T15:55:02.487789Z",
            "updated_at": "2021-06-24T15:55:02.495507Z",
            "file_url": "https://docshub.millionagents.com/media/documents/75/%D0%91%D0%B5%D0%B7_%D0%BD%D0%B0%D0%B7%D0%B2%D0%B0%D0%BD%D0%B8%D1%8F.pdf",
            "is_accepted": False,
        }

    return create_instance


@pytest.fixture
def docshub_single_documents_response_fi() -> Callable:
    def create_instance(company_id: int, version: int = 2) -> tp.List[tp.Dict[str, tp.Union[int, str]]]:
        return [
            {
                "id": 75,
                "doc_type": "law",
                "title": "Тестовое общение",
                "is_active": True,
                "version": version,
                "description": "ы",
                "key": "testovoe_obschenie",
                "realm_id": REALM_ID,
                "company_id": company_id,
                "created_at": "2021-06-24T15:55:02.487789Z",
                "updated_at": "2021-06-24T15:55:02.495507Z",
                "file_url": "https://docshub.millionagents.com/media/documents/75/%D0%91%D0%B5%D0%B7_%D0%BD%D0%B0%D0%B7%D0%B2%D0%B0%D0%BD%D0%B8%D1%8F.pdf",
                "is_accepted": False,
            }
        ]

    return create_instance


@pytest.fixture
def docshub_multiple_documents_response_fi() -> Callable:
    def create_instance(company_id: int) -> tp.List[tp.Dict[str, tp.Union[int, str]]]:
        return [
            {
                "id": 75,
                "doc_type": "law",
                "title": "Тестовое общение",
                "is_active": True,
                "version": 1,
                "description": "ы",
                "key": "testovoe_obschenie",
                "realm_id": REALM_ID,
                "company_id": company_id,
                "created_at": "2021-06-24T15:55:02.487789Z",
                "updated_at": "2021-06-24T15:55:02.495507Z",
                "file_url": "https://docshub.millionagents.com/media/documents/75/%D0%91%D0%B5%D0%B7_%D0%BD%D0%B0%D0%B7%D0%B2%D0%B0%D0%BD%D0%B8%D1%8F.pdf",
                "is_accepted": False,
            },
            {
                "id": 69,
                "doc_type": "law",
                "title": "Тестовое общение",
                "is_active": True,
                "version": 1,
                "description": "ы",
                "key": "testovoe_obschenie",
                "realm_id": REALM_ID,
                "company_id": company_id,
                "created_at": "2021-06-24T15:55:02.487789Z",
                "updated_at": "2021-06-24T15:55:02.495507Z",
                "file_url": "https://docshub.millionagents.com/media/documents/75/%D0%91%D0%B5%D0%B7_%D0%BD%D0%B0%D0%B7%D0%B2%D0%B0%D0%BD%D0%B8%D1%8F.pdf",
                "is_accepted": False,
            },
        ]

    return create_instance
