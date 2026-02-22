from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Protocol

from src.research.normalization import normalize_payload

from .pit_query import filter_point_in_time
from .quality_gate import BatchMetrics, evaluate_quality
from .revision_store import RevisionStore
from .source_registry import SourceDescriptor, evaluate_source


@dataclass(frozen=True)
class JobResult:
    raw_written: int
    canonical_written: int
    quarantined: int
    dashboard: dict[str, int]


class IngestionRepositoryProtocol(Protocol):
    def write_raw(self, row: Mapping[str, object]) -> None: ...

    def write_canonical(self, row: Mapping[str, object]) -> None: ...

    def write_quarantine(self, reason: str, payload: Mapping[str, object]) -> None: ...

    def write_macro_series_points(self, points: list[object]) -> int: ...

    def snapshot_counts(self) -> dict[str, int]: ...


def _resolve_entity_id(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "unknown"
    value = rows[0].get("entity_id")
    if value is None:
        return "unknown"
    return str(value)


def _resolve_available_at(rows: list[dict[str, object]], decision_time: datetime) -> datetime:
    if not rows:
        return decision_time

    value = rows[0].get("available_at")
    if not isinstance(value, datetime):
        return decision_time

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def run_ingestion_job(
    source: SourceDescriptor,
    metrics: BatchMetrics,
    idempotency_key: str,
    payload: Mapping[str, object],
    rows: list[dict[str, object]],
    decision_time: datetime,
    repository: IngestionRepositoryProtocol,
    revision_store: Optional[RevisionStore] = None,
) -> JobResult:
    store = revision_store or RevisionStore()

    source_eval = evaluate_source(source)
    quality_eval = evaluate_quality(metrics)

    repository.write_raw(payload)
    store.put(idempotency_key, payload)

    macro_series_points_written = 0
    if source_eval.admitted and quality_eval.promote:
        repository.write_canonical(payload)
        canonical_written = 1
        quarantined = 0

        source_name = source.name.lower()
        if source_name in {"fred", "ecos"}:
            normalized_points = normalize_payload(
                source=source_name,
                payload=payload,
                entity_id=_resolve_entity_id(rows),
                available_at=_resolve_available_at(rows, decision_time),
                lineage_id=idempotency_key,
            )
            macro_series_points_written = repository.write_macro_series_points(
                normalized_points
            )
    else:
        reason = "source_gate_failed" if not source_eval.admitted else "quality_gate_failed"
        repository.write_quarantine(reason=reason, payload=payload)
        canonical_written = 0
        quarantined = 1

    pit_rows = filter_point_in_time(rows, decision_time)
    dashboard = repository.snapshot_counts()
    dashboard["pit_rows"] = len(pit_rows)
    dashboard["macro_series_points_written"] = macro_series_points_written

    return JobResult(
        raw_written=1,
        canonical_written=canonical_written,
        quarantined=quarantined,
        dashboard=dashboard,
    )
