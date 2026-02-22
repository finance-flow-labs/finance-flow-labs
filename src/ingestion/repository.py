from collections.abc import Mapping


class InMemoryRepository:
    def __init__(self) -> None:
        self.raw_events: list[dict[str, object]] = []
        self.canonical_events: list[dict[str, object]] = []
        self.quarantine_events: list[dict[str, object]] = []
        self.macro_series_points: list[dict[str, object]] = []

    def write_raw(self, row: Mapping[str, object]) -> None:
        self.raw_events.append(dict(row))

    def write_canonical(self, row: Mapping[str, object]) -> None:
        self.canonical_events.append(dict(row))

    def write_quarantine(self, reason: str, payload: Mapping[str, object]) -> None:
        self.quarantine_events.append({"reason": reason, "payload": dict(payload)})

    def write_macro_series_points(self, points: list[object]) -> int:
        for point in points:
            self.macro_series_points.append(
                {
                    "source": getattr(point, "source", "unknown"),
                    "entity_id": getattr(point, "entity_id", "unknown"),
                    "metric_key": getattr(point, "metric_key", "unknown"),
                    "as_of": getattr(point, "as_of", None),
                    "available_at": getattr(point, "available_at", None),
                    "value": getattr(point, "value", None),
                    "lineage_id": getattr(point, "lineage_id", None),
                }
            )
        return len(points)

    def read_canonical_facts(
        self, source: str, metric_name: str, limit: int = 12
    ) -> list[dict[str, object]]:
        rows = [
            row
            for row in self.canonical_events
            if row.get("source") == source and row.get("metric_name") == metric_name
        ]
        return rows[-limit:]

    def snapshot_counts(self) -> dict[str, int]:
        return {
            "raw_events": len(self.raw_events),
            "canonical_events": len(self.canonical_events),
            "quarantine_events": len(self.quarantine_events),
            "macro_series_points": len(self.macro_series_points),
        }
