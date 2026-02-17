from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Optional, Protocol
from uuid import uuid4

from .job import IngestionRepositoryProtocol, run_ingestion_job
from .quality_gate import BatchMetrics
from .source_registry import SourceDescriptor


class RunHistoryRepositoryProtocol(Protocol):
    def write_run_history(self, run: Mapping[str, object]) -> None: ...


def run_manual_update(
    source: SourceDescriptor,
    metrics: BatchMetrics,
    idempotency_key: str,
    payload: Mapping[str, object],
    rows: list[dict[str, object]],
    decision_time: datetime,
    repository: IngestionRepositoryProtocol,
    run_history_repository: Optional[RunHistoryRepositoryProtocol] = None,
) -> dict[str, object]:
    run_id = str(uuid4())
    started_at = datetime.now(timezone.utc)

    try:
        result = run_ingestion_job(
            source=source,
            metrics=metrics,
            idempotency_key=idempotency_key,
            payload=payload,
            rows=rows,
            decision_time=decision_time,
            repository=repository,
        )
        status = "success" if result.quarantined == 0 else "quarantine"
        error_message: Optional[str] = None
        raw_written = result.raw_written
        canonical_written = result.canonical_written
        quarantined = result.quarantined
    except Exception as error:
        status = "failed"
        error_message = str(error)
        raw_written = 0
        canonical_written = 0
        quarantined = 0

    finished_at = datetime.now(timezone.utc)
    run_record: dict[str, object] = {
        "run_id": run_id,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "source_name": source.name,
        "status": status,
        "raw_written": raw_written,
        "canonical_written": canonical_written,
        "quarantined": quarantined,
        "error_message": error_message,
    }

    if run_history_repository is not None:
        run_history_repository.write_run_history(run_record)

    return run_record
