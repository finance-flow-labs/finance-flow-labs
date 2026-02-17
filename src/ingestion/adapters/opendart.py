from collections.abc import Mapping
from typing import Optional, Protocol
from urllib.parse import urlencode


class ApiClient(Protocol):
    def request_json(
        self, url: str, headers: Optional[Mapping[str, str]] = None
    ) -> dict[str, object]: ...


class OpenDartAdapter:
    source_name: str = "opendart"

    def __init__(self, client: Optional[ApiClient] = None, api_key: str = "") -> None:
        self.client = client
        self.api_key = api_key

    def normalize(self, payload: Mapping[str, object]) -> dict[str, object]:
        return {
            "source": self.source_name,
            "entity_id": payload.get("id", ""),
            "payload": payload,
        }

    def fetch_company(self, corp_code: str) -> dict[str, object]:
        if self.client is None:
            raise ValueError("client is required for fetch operations")
        query = urlencode({"crtfc_key": self.api_key, "corp_code": corp_code})
        url = f"https://opendart.fss.or.kr/api/company.json?{query}"
        payload = self.client.request_json(url)
        return {"source": self.source_name, "entity_id": corp_code, "payload": payload}
