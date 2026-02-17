from datetime import datetime, timezone
import importlib

BudgetGuard = importlib.import_module("src.ingestion.budget_guard").BudgetGuard
cache_policy = importlib.import_module("src.ingestion.cache_policy")
DataTier = cache_policy.DataTier
filter_point_in_time = importlib.import_module(
    "src.ingestion.pit_query"
).filter_point_in_time
quality_gate = importlib.import_module("src.ingestion.quality_gate")
BatchMetrics = quality_gate.BatchMetrics
evaluate_quality = quality_gate.evaluate_quality
RevisionStore = importlib.import_module("src.ingestion.revision_store").RevisionStore
source_registry = importlib.import_module("src.ingestion.source_registry")
SourceDescriptor = source_registry.SourceDescriptor
evaluate_source = source_registry.evaluate_source
pipeline = importlib.import_module("src.ingestion.pipeline")


def test_end_to_end_baseline_flow():
    source = SourceDescriptor(
        name="edgar",
        utility=5,
        reliability=4,
        legal=5,
        cost=3,
        maintenance=3,
    )
    metrics = BatchMetrics(
        freshness=True,
        completeness=True,
        schema_drift=False,
        license_ok=True,
    )

    decision_time = datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
    rows = [
        {
            "entity_id": "AAPL",
            "available_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "as_of": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        }
    ]

    outcome = pipeline.run_pipeline(
        source=source,
        metrics=metrics,
        idempotency_key="edgar|AAPL|2026-01-01|r1",
        payload={"eps": 1.2},
        rows=rows,
        decision_time=decision_time,
    )

    assert outcome["source_eval"].admitted is True
    assert outcome["quality"].promote is True
    assert outcome["write_result"].status == "inserted"
    assert len(outcome["pit_rows"]) == 1

    guard = BudgetGuard(monthly_cap=1000)
    guard.record_spend(100)
    assert guard.is_frozen is False
    assert DataTier.GOLD.value == "gold"
