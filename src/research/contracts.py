from dataclasses import dataclass
from datetime import datetime
from typing import Literal


EvidenceTier = Literal["HARD", "SOFT"]


@dataclass(frozen=True)
class NormalizedSeriesPoint:
    source: str
    entity_id: str
    metric_key: str
    as_of: datetime
    available_at: datetime
    value: float
    lineage_id: str
    evidence_tier: EvidenceTier = "HARD"
