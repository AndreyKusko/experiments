import random
from typing import Callable

import pytest

from billing.models import WorkerReportsTransaction
from reports.models.worker_report import WorkerReport


@pytest.fixture
def get_worker_report_transaction_fi() -> Callable:
    def create_instance(worker_report: WorkerReport, transaction_id: int = None) -> WorkerReportsTransaction:
        instance = WorkerReportsTransaction.objects.create(
            worker_report=worker_report, transaction_id=transaction_id or random.getrandbits(64)
        )
        return instance

    return create_instance
