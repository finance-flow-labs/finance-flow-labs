from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EventRecord:
    source: str
    entity_id: str
    as_of: datetime
    available_at: datetime
    ingested_at: datetime
    lineage_id: str
    schema_version: str
    license_tier: str
    payload: dict[str, object]
