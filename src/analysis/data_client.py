"""Canonical data client for the analysis layer.

Reads time-series from canonical_fact_store and provides anomaly detection.
Falls back gracefully to empty results when the database is not configured.
When DB is unavailable, FRED and ECOS data can be fetched directly via their
public REST APIs using FRED_API_KEY and ECOS_API_KEY environment variables.
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, timedelta, timezone
from typing import Union
from urllib.parse import urlencode
from urllib.request import urlopen

from src.ingestion.postgres_repository import PostgresRepository
from src.ingestion.repository import InMemoryRepository


class _FredDirectClient:
    """Lightweight FRED REST API client using stdlib urllib."""

    _BASE = "https://api.stlouisfed.org/fred/series/observations"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def fetch(self, series_id: str, limit: int = 12) -> list[dict[str, object]]:
        params = urlencode(
            {
                "series_id": series_id,
                "api_key": self._api_key,
                "sort_order": "desc",
                "limit": limit,
                "file_type": "json",
            }
        )
        url = f"{self._BASE}?{params}"
        with urlopen(url, timeout=15) as resp:  # noqa: S310
            data = json.loads(resp.read().decode())

        rows: list[dict[str, object]] = []
        for obs in data.get("observations", []):
            raw_val = obs.get("value", ".")
            try:
                metric_value: object = float(raw_val)
            except (ValueError, TypeError):
                metric_value = None
            rows.append(
                {
                    "source": "fred",
                    "entity_id": series_id,
                    "metric_name": series_id,
                    "as_of": obs.get("date", ""),
                    "metric_value": metric_value,
                }
            )
        # API returns desc; reverse to chronological order
        return list(reversed(rows))


class _EcosDirectClient:
    """Lightweight ECOS REST API client using stdlib urllib."""

    _BASE = "https://ecos.bok.or.kr/api/StatisticSearch"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def fetch(self, stat_code: str, limit: int = 12) -> list[dict[str, object]]:
        now = datetime.now(tz=timezone.utc)
        end_dt = now.replace(day=1)
        start_dt = end_dt - timedelta(days=limit * 31)
        start = start_dt.strftime("%Y%m")
        end = end_dt.strftime("%Y%m")

        url = (
            f"{self._BASE}/{self._api_key}/json/kr/1/{limit}"
            f"/{stat_code}/M/{start}/{end}"
        )
        with urlopen(url, timeout=15) as resp:  # noqa: S310
            data = json.loads(resp.read().decode())

        rows: list[dict[str, object]] = []
        stat_search = data.get("StatisticSearch", {})
        for row in stat_search.get("row", []):
            time_str = str(row.get("TIME", ""))
            if len(time_str) == 6:
                as_of = f"{time_str[:4]}-{time_str[4:6]}-01"
            else:
                as_of = time_str
            raw_val = row.get("DATA_VALUE", "")
            try:
                metric_value: object = float(raw_val)
            except (ValueError, TypeError):
                metric_value = None
            rows.append(
                {
                    "source": "ecos",
                    "entity_id": stat_code,
                    "metric_name": stat_code,
                    "as_of": as_of,
                    "metric_value": metric_value,
                }
            )
        return rows


class CanonicalDataClient:
    """Reads canonical economic time-series from canonical_fact_store."""

    def __init__(self) -> None:
        dsn = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
        self._repo: Union[PostgresRepository, InMemoryRepository] = (
            PostgresRepository(dsn=dsn) if dsn else InMemoryRepository()
        )

    def read_series(
        self, source: str, metric_name: str, limit: int = 12
    ) -> list[dict[str, object]]:
        try:
            rows = self._repo.read_canonical_facts(source, metric_name, limit)
        except Exception:
            rows = []

        if not rows and source == "fred":
            fred_key = os.getenv("FRED_API_KEY", "")
            if fred_key:
                try:
                    rows = _FredDirectClient(fred_key).fetch(metric_name, limit)
                except Exception:
                    rows = []

        if not rows and source == "ecos":
            ecos_key = os.getenv("ECOS_API_KEY", "")
            if ecos_key:
                try:
                    rows = _EcosDirectClient(ecos_key).fetch(metric_name, limit)
                except Exception:
                    rows = []

        return rows


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

    def _to_float(raw: object) -> float | None:
        if raw is None:
            return None
        if isinstance(raw, bool):
            return float(raw)
        if isinstance(raw, (int, float)):
            return float(raw)
        if isinstance(raw, str):
            try:
                return float(raw)
            except ValueError:
                return None
        return None

    for i in range(window, len(rows)):
        window_vals: list[float] = []
        for j in range(i - window, i):
            candidate = _to_float(rows[j].get("metric_value"))
            if candidate is None:
                continue
            window_vals.append(candidate)
        if len(window_vals) < window:
            continue

        current_val = rows[i].get("metric_value")
        if current_val is None:
            continue
        current = _to_float(current_val)
        if current is None:
            continue

        mean: float = sum(window_vals) / len(window_vals)
        variance: float = sum((v - mean) ** 2 for v in window_vals) / len(window_vals)
        std: float = math.sqrt(variance)

        if std == 0:
            continue

        z: float = (current - mean) / std
        if abs(z) > threshold:
            row = dict(rows[i])
            row["z_score"] = round(z, 4)
            row["rolling_mean"] = round(mean, 6)
            row["rolling_std"] = round(std, 6)
            flagged.append(row)

    return flagged
