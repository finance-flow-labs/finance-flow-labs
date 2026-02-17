from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .pit_query import filter_point_in_time
from .quality_gate import BatchMetrics, evaluate_quality
from .repository import InMemoryRepository
from .revision_store import RevisionStore
from .source_registry import SourceDescriptor, evaluate_source


@dataclass(frozen=True)
class JobResult:
    raw_written: int
    canonical_written: int
    quarantined: int
    dashboard: dict[str, int]


def run_ingestion_job(
    source: SourceDescriptor,
    metrics: BatchMetrics,
    idempotency_key: str,
    payload: Mapping[str, object],
    rows: list[dict[str, object]],
    decision_time: datetime,
    repository: InMemoryRepository,
    revision_store: Optional[RevisionStore] = None,
) -> JobResult:
    store = revision_store or RevisionStore()

    source_eval = evaluate_source(source)
    quality_eval = evaluate_quality(metrics)

    repository.write_raw(payload)
    store.put(idempotency_key, payload)

    if source_eval.admitted and quality_eval.promote:
        repository.write_canonical(payload)
        canonical_written = 1
        quarantined = 0
    else:
        reason = "source_gate_failed" if not source_eval.admitted else "quality_gate_failed"
        repository.write_quarantine(reason=reason, payload=payload)
        canonical_written = 0
        quarantined = 1

    pit_rows = filter_point_in_time(rows, decision_time)
    dashboard = repository.snapshot_counts()
    dashboard["pit_rows"] = len(pit_rows)

    return JobResult(
        raw_written=1,
        canonical_written=canonical_written,
        quarantined=quarantined,
        dashboard=dashboard,
    )
