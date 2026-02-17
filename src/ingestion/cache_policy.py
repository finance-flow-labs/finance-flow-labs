from enum import Enum
from typing import Optional


class DataTier(Enum):
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"


def ttl_days_for_tier(tier: DataTier) -> Optional[int]:
    if tier == DataTier.GOLD:
        return None
    if tier == DataTier.SILVER:
        return 180
    return 90


def ttl_months_for_facts(tier: DataTier) -> Optional[int]:
    if tier == DataTier.SILVER:
        return 24
    return None
