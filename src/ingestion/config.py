from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    monthly_cost_cap: float = 1000.0
    default_timezone: str = "UTC"
