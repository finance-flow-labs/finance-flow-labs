from datetime import datetime
from collections.abc import Iterable, Mapping


def filter_point_in_time(
    rows: Iterable[Mapping[str, object]], decision_time: datetime
) -> list[Mapping[str, object]]:
    filtered: list[Mapping[str, object]] = []
    for row in rows:
        available_at = row.get("available_at")
        if isinstance(available_at, datetime) and available_at <= decision_time:
            filtered.append(row)
    filtered.sort(key=lambda row: (row.get("available_at"), row.get("entity_id")))
    return filtered
