import importlib
from datetime import datetime, timezone


job_mod = importlib.import_module("src.ingestion.job")
repo_mod = importlib.import_module("src.ingestion.repository")
registry_mod = importlib.import_module("src.ingestion.source_registry")
quality_mod = importlib.import_module("src.ingestion.quality_gate")

run_ingestion_job = job_mod.run_ingestion_job
InMemoryRepository = repo_mod.InMemoryRepository
SourceDescriptor = registry_mod.SourceDescriptor
BatchMetrics = quality_mod.BatchMetrics


def test_ingestion_job_promotes_to_canonical_when_all_checks_pass():
    repo = InMemoryRepository()
    source = SourceDescriptor(
        name="edgar",
        utility=5,
        reliability=5,
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

    result = run_ingestion_job(
        source=source,
        metrics=metrics,
        idempotency_key="edgar|AAPL|2026-01-01|r1",
        payload={"eps": 1.2},
        rows=[
            {
                "entity_id": "AAPL",
                "as_of": datetime(2026, 1, 1, tzinfo=timezone.utc),
                "available_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
            }
        ],
        decision_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
        repository=repo,
    )

    assert result.canonical_written == 1
    assert result.quarantined == 0
    assert result.dashboard["raw_events"] == 1


def test_ingestion_job_quarantines_when_quality_fails():
    repo = InMemoryRepository()
    source = SourceDescriptor(
        name="edgar",
        utility=5,
        reliability=5,
        legal=5,
        cost=3,
        maintenance=3,
    )
    metrics = BatchMetrics(
        freshness=False,
        completeness=True,
        schema_drift=False,
        license_ok=True,
    )

    result = run_ingestion_job(
        source=source,
        metrics=metrics,
        idempotency_key="edgar|AAPL|2026-01-01|r1",
        payload={"eps": 1.2},
        rows=[
            {
                "entity_id": "AAPL",
                "as_of": datetime(2026, 1, 1, tzinfo=timezone.utc),
                "available_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
            }
        ],
        decision_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
        repository=repo,
    )

    assert result.canonical_written == 0
    assert result.quarantined == 1
    assert result.dashboard["quarantine_events"] == 1
    assert result.dashboard["macro_series_points_written"] == 0


def test_ingestion_job_writes_macro_series_points_for_fred_source():
    repo = InMemoryRepository()
    source = SourceDescriptor(
        name="fred",
        utility=5,
        reliability=5,
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

    result = run_ingestion_job(
        source=source,
        metrics=metrics,
        idempotency_key="fred|UNRATE|2026-01-01|r1",
        payload={
            "payload": {
                "observations": [
                    {"date": "2025-12-01", "value": "4.4"},
                    {"date": "2026-01-01", "value": "4.3"},
                ]
            }
        },
        rows=[
            {
                "entity_id": "UNRATE",
                "as_of": datetime(2026, 1, 1, tzinfo=timezone.utc),
                "available_at": datetime(2026, 1, 2, tzinfo=timezone.utc),
            }
        ],
        decision_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
        repository=repo,
    )

    assert result.canonical_written == 1
    assert result.quarantined == 0
    assert result.dashboard["macro_series_points_written"] == 2
    assert len(repo.macro_series_points) == 2
    assert repo.macro_series_points[-1]["metric_key"] == "UNRATE"
