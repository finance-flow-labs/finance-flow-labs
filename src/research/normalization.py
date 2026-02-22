import re
from datetime import datetime, timezone
from typing import Iterable, Mapping, Optional

from .contracts import NormalizedSeriesPoint


def _parse_datetime(value: object) -> Optional[datetime]:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if not isinstance(value, str) or not value:
        return None

    for fmt in ("%Y-%m-%d", "%Y%m", "%Y-%m", "%Y%m%d", "%Y"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    quarter_match = re.fullmatch(r"(\d{4})-?Q([1-4])", value.strip(), flags=re.IGNORECASE)
    if quarter_match:
        year = int(quarter_match.group(1))
        quarter = int(quarter_match.group(2))
        month = (quarter - 1) * 3 + 1
        return datetime(year, month, 1, tzinfo=timezone.utc)

    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _to_float(value: object) -> Optional[float]:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned or cleaned in {".", "NA", "NaN"}:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def normalize_fred_payload(
    payload: Mapping[str, object],
    entity_id: str,
    available_at: datetime,
    lineage_id: str,
) -> list[NormalizedSeriesPoint]:
    points: list[NormalizedSeriesPoint] = []
    observations = payload.get("observations")
    if not isinstance(observations, list):
        return points

    for row in observations:
        if not isinstance(row, Mapping):
            continue
        as_of = _parse_datetime(row.get("date"))
        value = _to_float(row.get("value"))
        if as_of is None or value is None:
            continue
        points.append(
            NormalizedSeriesPoint(
                source="fred",
                entity_id=entity_id,
                metric_key=entity_id,
                as_of=as_of,
                available_at=available_at,
                value=value,
                lineage_id=lineage_id,
            )
        )

    return sorted(points, key=lambda p: p.as_of)


def normalize_ecos_payload(
    payload: Mapping[str, object],
    entity_id: str,
    available_at: datetime,
    lineage_id: str,
) -> list[NormalizedSeriesPoint]:
    points: list[NormalizedSeriesPoint] = []
    statistic_search = payload.get("StatisticSearch")
    if not isinstance(statistic_search, Mapping):
        return points

    rows = statistic_search.get("row")
    if not isinstance(rows, list):
        return points

    for row in rows:
        if not isinstance(row, Mapping):
            continue

        metric_key = str(row.get("ITEM_NAME1") or row.get("ITEM_CODE1") or entity_id)
        as_of_raw = row.get("TIME") or row.get("TRM") or row.get("date")
        value_raw = row.get("DATA_VALUE") or row.get("value")

        as_of = _parse_datetime(as_of_raw)
        value = _to_float(value_raw)
        if as_of is None or value is None:
            continue

        points.append(
            NormalizedSeriesPoint(
                source="ecos",
                entity_id=entity_id,
                metric_key=metric_key,
                as_of=as_of,
                available_at=available_at,
                value=value,
                lineage_id=lineage_id,
            )
        )

    return sorted(points, key=lambda p: p.as_of)


def normalize_payload(
    source: str,
    payload: Mapping[str, object],
    entity_id: str,
    available_at: datetime,
    lineage_id: str,
) -> list[NormalizedSeriesPoint]:
    raw_payload = payload.get("payload") if isinstance(payload.get("payload"), Mapping) else payload

    if source == "fred":
        return normalize_fred_payload(raw_payload, entity_id, available_at, lineage_id)
    if source == "ecos":
        return normalize_ecos_payload(raw_payload, entity_id, available_at, lineage_id)
    return []
