from collections import Counter
from typing import Protocol


class DashboardRepositoryProtocol(Protocol):
    def read_latest_runs(self, limit: int = 20) -> list[dict[str, object]]: ...

    def read_status_counters(self) -> dict[str, int]: ...

    def read_learning_metrics(self, horizon: str = "1M") -> dict[str, object]: ...

    def read_forecast_error_category_stats(
        self, horizon: str = "1M", limit: int = 5
    ) -> list[dict[str, object]]: ...


def _count_non_empty_evidence(value: object) -> bool:
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, str):
        trimmed = value.strip()
        return trimmed not in {"", "[]", "null", "None"}
    return value is not None


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
        "top_categories": [],
        "hard_evidence_coverage": None,
        "soft_evidence_coverage": None,
        "evidence_gap_count": 0,
        "evidence_gap_coverage": None,
    }
    if hasattr(repository, "read_forecast_error_category_stats"):
        category_stats = repository.read_forecast_error_category_stats(horizon="1M", limit=5)
        if category_stats:
            top = category_stats[0]
            attribution_summary = {
                "total": int(sum(int(row.get("attribution_count", 0)) for row in category_stats)),
                "top_category": str(top.get("category", "n/a")),
                "top_count": int(top.get("attribution_count", 0)),
                "top_categories": category_stats,
                "hard_evidence_coverage": None,
                "soft_evidence_coverage": None,
                "evidence_gap_count": 0,
                "evidence_gap_coverage": None,
            }

    if hasattr(repository, "read_forecast_error_attributions"):
        attribution_rows = repository.read_forecast_error_attributions(horizon="1M", limit=200)
        if attribution_rows:
            categories = [
                str(row.get("category", "unknown"))
                for row in attribution_rows
                if isinstance(row, dict) and row.get("category")
            ]
            category_counts = Counter(categories)
            if category_counts and attribution_summary["top_category"] == "n/a":
                top_category, top_count = category_counts.most_common(1)[0]
                attribution_summary.update(
                    {
                        "total": len(attribution_rows),
                        "top_category": top_category,
                        "top_count": int(top_count),
                        "top_categories": [
                            {"category": key, "attribution_count": int(value)}
                            for key, value in category_counts.most_common(5)
                        ],
                    }
                )

            hard_count = 0
            soft_count = 0
            evidence_gap_count = 0
            valid_rows = 0
            for row in attribution_rows:
                if not isinstance(row, dict):
                    continue
                valid_rows += 1
                has_hard = _count_non_empty_evidence(row.get("evidence_hard"))
                has_soft = _count_non_empty_evidence(row.get("evidence_soft"))
                if has_hard:
                    hard_count += 1
                if has_soft:
                    soft_count += 1
                if not has_hard and not has_soft:
                    evidence_gap_count += 1

            if valid_rows > 0:
                attribution_summary["total"] = valid_rows
                attribution_summary["hard_evidence_coverage"] = hard_count / valid_rows
                attribution_summary["soft_evidence_coverage"] = soft_count / valid_rows
                attribution_summary["evidence_gap_count"] = evidence_gap_count
                attribution_summary["evidence_gap_coverage"] = evidence_gap_count / valid_rows

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
