from collections.abc import Mapping
from typing import Optional, Protocol
from urllib.parse import urlencode


class ApiClient(Protocol):
    def request_json(
        self, url: str, headers: Optional[Mapping[str, str]] = None
    ) -> dict[str, object]: ...


class FredAdapter:
    source_name: str = "fred"

    def __init__(self, client: Optional[ApiClient] = None, api_key: str = "") -> None:
        self.client = client
        self.api_key = api_key

    def normalize(self, payload: Mapping[str, object]) -> dict[str, object]:
        return {
            "source": self.source_name,
            "entity_id": payload.get("id", ""),
            "payload": payload,
        }

    def fetch_series_observations(self, series_id: str) -> dict[str, object]:
        if self.client is None:
            raise ValueError("client is required for fetch operations")
        query = urlencode(
            {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
            }
        )
        url = f"https://api.stlouisfed.org/fred/series/observations?{query}"
        payload = self.client.request_json(url)
        return {"source": self.source_name, "entity_id": series_id, "payload": payload}
