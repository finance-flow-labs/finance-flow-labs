from collections.abc import Mapping
from typing import Optional, Protocol


class ApiClient(Protocol):
    def request_json(
        self, url: str, headers: Optional[Mapping[str, str]] = None
    ) -> dict[str, object]: ...


class SecEdgarAdapter:
    source_name: str = "sec_edgar"

    def __init__(self, client: Optional[ApiClient] = None, user_agent: str = "") -> None:
        self.client = client
        self.user_agent = user_agent

    def normalize(self, payload: Mapping[str, object]) -> dict[str, object]:
        return {
            "source": self.source_name,
            "entity_id": payload.get("id", ""),
            "payload": payload,
        }

    def fetch_company_facts(self, cik: str) -> dict[str, object]:
        if self.client is None:
            raise ValueError("client is required for fetch operations")
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        payload = self.client.request_json(url, headers={"User-Agent": self.user_agent})
        return {"source": self.source_name, "entity_id": cik, "payload": payload}
