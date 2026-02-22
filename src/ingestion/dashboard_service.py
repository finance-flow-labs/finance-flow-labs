from typing import Protocol


class DashboardRepositoryProtocol(Protocol):
    def read_latest_runs(self, limit: int = 20) -> list[dict[str, object]]: ...

    def read_status_counters(self) -> dict[str, int]: ...

    def read_learning_metrics(self, horizon: str = "1M") -> dict[str, object]: ...


def build_dashboard_view(
    repository: DashboardRepositoryProtocol,
    limit: int = 20,
) -> dict[str, object]:
    recent_runs = repository.read_latest_runs(limit=limit)
    counters = repository.read_status_counters()
    learning_metrics = repository.read_learning_metrics(horizon="1M")

    if recent_runs:
        latest = recent_runs[0]
        last_run_status = str(latest.get("status", "unknown"))
        last_run_time = str(latest.get("finished_at", ""))
    else:
        last_run_status = "no-data"
        last_run_time = ""

    return {
        "last_run_status": last_run_status,
        "last_run_time": last_run_time,
        "counters": counters,
        "learning_metrics": learning_metrics,
        "recent_runs": recent_runs,
    }
