import importlib


dashboard_service = importlib.import_module("src.ingestion.dashboard_service")
build_dashboard_view = dashboard_service.build_dashboard_view


class FakeDashboardRepo:
    def read_latest_runs(self, limit=20):
        return [
            {"run_id": "run-2", "status": "success", "finished_at": "2026-02-18T01:00:00Z"},
            {"run_id": "run-1", "status": "quarantine", "finished_at": "2026-02-18T00:00:00Z"},
        ]

    def read_status_counters(self):
        return {"raw_events": 100, "canonical_events": 90, "quarantine_events": 10}


def test_dashboard_service_builds_operator_view_model():
    view = build_dashboard_view(FakeDashboardRepo())

    assert view["last_run_status"] == "success"
    assert view["last_run_time"] == "2026-02-18T01:00:00Z"
    assert view["counters"]["raw_events"] == 100
    assert len(view["recent_runs"]) == 2
