"""Canonical data client for the analysis layer.

Reads time-series from canonical_fact_store and provides anomaly detection.
Falls back gracefully to empty results when the database is not configured.
"""

from __future__ import annotations

from src.ingestion.postgres_repository import PostgresRepository


class CanonicalDataClient:
    """Reads canonical economic time-series from canonical_fact_store."""

    def __init__(self) -> None:
        self._repo = PostgresRepository()

    def read_series(
        self, source: str, metric_name: str, limit: int = 12
    ) -> list[dict[str, object]]:
        """Return up to *limit* rows for (source, metric_name), oldest first.

        Returns [] when SUPABASE_URL / SUPABASE_KEY are not set.
        """
        return self._repo.read_canonical_facts(source, metric_name, limit)


def detect_anomalies(
    rows: list[dict[str, object]],
    window: int = 6,
    threshold: float = 2.0,
) -> list[dict[str, object]]:
    """Return rows whose metric_value deviates beyond *threshold* standard
    deviations from a rolling window mean.

    Args:
        rows: Time-ordered list of canonical fact dicts with a ``metric_value``
              numeric field.
        window: Number of prior observations used for the rolling statistics.
        threshold: Z-score magnitude that flags an anomaly.

    Returns:
        Subset of *rows* that are flagged, each augmented with
        ``z_score``, ``rolling_mean``, and ``rolling_std`` keys.

    Notes:
        - Returns ``[]`` when ``len(rows) < window + 1``.
        - Rows with a ``None`` / missing ``metric_value`` are skipped.
    """
    if len(rows) < window + 1:
        return []

    flagged: list[dict[str, object]] = []

    for i in range(window, len(rows)):
        window_vals = [
            float(rows[j]["metric_value"])
            for j in range(i - window, i)
            if rows[j].get("metric_value") is not None
        ]
        if len(window_vals) < window:
            continue

        current_val = rows[i].get("metric_value")
        if current_val is None:
            continue

        mean = sum(window_vals) / len(window_vals)
        variance = sum((v - mean) ** 2 for v in window_vals) / len(window_vals)
        std = variance ** 0.5

        if std == 0:
            continue

        z = (float(current_val) - mean) / std
        if abs(z) > threshold:
            row = dict(rows[i])
            row["z_score"] = round(z, 4)
            row["rolling_mean"] = round(mean, 6)
            row["rolling_std"] = round(std, 6)
            flagged.append(row)

    return flagged
