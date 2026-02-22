from collections import Counter
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

    attribution_summary = {
        "total": 0,
        "top_category": "n/a",
        "top_count": 0,
    }
    if hasattr(repository, "read_forecast_error_attributions"):
        attribution_rows = repository.read_forecast_error_attributions(horizon="1M", limit=200)
        categories = [
            str(row.get("category", "unknown"))
            for row in attribution_rows
            if isinstance(row, dict) and row.get("category")
        ]
        category_counts = Counter(categories)
        if category_counts:
            top_category, top_count = category_counts.most_common(1)[0]
            attribution_summary = {
                "total": len(attribution_rows),
                "top_category": top_category,
                "top_count": int(top_count),
            }

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
        "attribution_summary": attribution_summary,
        "recent_runs": recent_runs,
    }
