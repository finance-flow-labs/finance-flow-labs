from datetime import datetime, timezone
import importlib


manual_runner = importlib.import_module("src.ingestion.manual_runner")
repository_mod = importlib.import_module("src.ingestion.repository")
quality_mod = importlib.import_module("src.ingestion.quality_gate")
registry_mod = importlib.import_module("src.ingestion.source_registry")

run_manual_update = manual_runner.run_manual_update
InMemoryRepository = repository_mod.InMemoryRepository
BatchMetrics = quality_mod.BatchMetrics
SourceDescriptor = registry_mod.SourceDescriptor


class FakeRunHistoryRepo:
    def __init__(self):
        self.records = []

    def write_run_history(self, run):
        self.records.append(run)


def test_manual_runner_returns_status_and_counts():
    data_repo = InMemoryRepository()
    run_history_repo = FakeRunHistoryRepo()

    summary = run_manual_update(
        source=SourceDescriptor(
            name="sec_edgar",
            utility=5,
            reliability=5,
            legal=5,
            cost=3,
            maintenance=3,
        ),
        metrics=BatchMetrics(
            freshness=True,
            completeness=True,
            schema_drift=False,
            license_ok=True,
        ),
        idempotency_key="sec|AAPL|2026-02-18|r1",
        payload={"entity_id": "AAPL", "eps": 1.2},
        rows=[
            {
                "entity_id": "AAPL",
                "available_at": datetime(2026, 2, 18, tzinfo=timezone.utc),
            }
        ],
        decision_time=datetime(2026, 2, 18, 1, 0, tzinfo=timezone.utc),
        repository=data_repo,
        run_history_repository=run_history_repo,
    )

    assert summary["status"] == "success"
    assert summary["raw_written"] == 1
    assert summary["canonical_written"] == 1
    assert len(run_history_repo.records) == 1
    assert run_history_repo.records[0]["status"] == "success"
