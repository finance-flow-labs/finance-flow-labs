from datetime import datetime

from .pit_query import filter_point_in_time
from .quality_gate import BatchMetrics, evaluate_quality
from .revision_store import RevisionStore
from .source_registry import SourceDescriptor, evaluate_source
from .config import Settings


_store = RevisionStore()


def build_pipeline() -> dict[str, object]:
    settings = Settings()
    return {"name": "ingestion-pipeline", "cost_cap": settings.monthly_cost_cap}


def run_pipeline(
    source: SourceDescriptor,
    metrics: BatchMetrics,
    idempotency_key: str,
    payload: dict[str, object],
    rows: list[dict[str, object]],
    decision_time: datetime,
) -> dict[str, object]:
    source_eval = evaluate_source(source)
    quality = evaluate_quality(metrics)
    write_result = _store.put(idempotency_key, payload)
    pit_rows = filter_point_in_time(rows, decision_time)
    return {
        "source_eval": source_eval,
        "quality": quality,
        "write_result": write_result,
        "pit_rows": pit_rows,
    }
