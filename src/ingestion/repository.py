from collections.abc import Mapping


class InMemoryRepository:
    def __init__(self) -> None:
        self.raw_events: list[dict[str, object]] = []
        self.canonical_events: list[dict[str, object]] = []
        self.quarantine_events: list[dict[str, object]] = []

    def write_raw(self, row: Mapping[str, object]) -> None:
        self.raw_events.append(dict(row))

    def write_canonical(self, row: Mapping[str, object]) -> None:
        self.canonical_events.append(dict(row))

    def write_quarantine(self, reason: str, payload: Mapping[str, object]) -> None:
        self.quarantine_events.append({"reason": reason, "payload": dict(payload)})

    def snapshot_counts(self) -> dict[str, int]:
        return {
            "raw_events": len(self.raw_events),
            "canonical_events": len(self.canonical_events),
            "quarantine_events": len(self.quarantine_events),
        }
