import typing as tp
from typing import Callable

import pytest

from ma_saas.settings import REALM_ID


@pytest.fixture
def docshub_accept_document_response_fi() -> Callable:
    def create_instance(
        user_id, document_id
    ) -> tp.Tuple[tp.Dict[str, tp.Union[int, str]], tp.Dict[str, tp.Union[int, str]]]:
        return {
            "ext_user_id": user_id,
            "document": document_id,
            "version": 1,
            "created_at": "2021-06-25T11:05:00.180013Z",
        }

    return create_instance
