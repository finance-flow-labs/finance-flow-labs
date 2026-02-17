from collections.abc import Mapping
from typing import Optional, Protocol


class ApiClient(Protocol):
    def request_json(
        self, url: str, headers: Optional[Mapping[str, str]] = None
    ) -> dict[str, object]: ...


class EcosAdapter:
    source_name: str = "ecos"

    def __init__(self, client: Optional[ApiClient] = None, api_key: str = "") -> None:
        self.client = client
        self.api_key = api_key

    def normalize(self, payload: Mapping[str, object]) -> dict[str, object]:
        return {
            "source": self.source_name,
            "entity_id": payload.get("id", ""),
            "payload": payload,
        }

    def fetch_statistic(self, stat_code: str) -> dict[str, object]:
        if self.client is None:
            raise ValueError("client is required for fetch operations")
        url = (
            "https://ecos.bok.or.kr/api/StatisticSearch/"
            f"{self.api_key}/json/kr/1/100/{stat_code}/M/202001/202312"
        )
        payload = self.client.request_json(url)
        return {"source": self.source_name, "entity_id": stat_code, "payload": payload}
