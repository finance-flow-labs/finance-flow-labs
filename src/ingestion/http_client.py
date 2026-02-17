import json
import time
from dataclasses import dataclass
from typing import Callable, Mapping, Optional


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    body: bytes
    headers: Mapping[str, str]


class HttpError(Exception):
    pass


class SimpleHttpClient:
    def __init__(
        self,
        transport: Callable[[str, str, Mapping[str, str]], HttpResponse],
        rate_limit_per_second: float = 5.0,
        max_retries: int = 2,
        sleep: Callable[[float], None] = time.sleep,
        now: Callable[[], float] = time.monotonic,
    ) -> None:
        self._transport = transport
        self._interval = 1.0 / rate_limit_per_second if rate_limit_per_second > 0 else 0.0
        self._max_retries = max_retries
        self._sleep = sleep
        self._now = now
        self._next_allowed_time = 0.0

    def _wait_for_rate_limit(self) -> None:
        current = self._now()
        if self._next_allowed_time > current:
            self._sleep(self._next_allowed_time - current)

    def _mark_request_time(self) -> None:
        self._next_allowed_time = self._now() + self._interval

    def request_json(
        self, url: str, headers: Optional[Mapping[str, str]] = None
    ) -> dict[str, object]:
        attempt = 0
        request_headers = dict(headers or {})

        while True:
            self._wait_for_rate_limit()
            try:
                response = self._transport("GET", url, request_headers)
            except Exception as error:
                if attempt >= self._max_retries:
                    raise HttpError(str(error)) from error
                attempt += 1
                self._sleep(float(attempt))
                continue

            self._mark_request_time()

            if response.status_code == 200:
                decoded = json.loads(response.body.decode("utf-8"))
                if isinstance(decoded, dict):
                    return decoded
                raise HttpError("response body is not a JSON object")

            if response.status_code in {429, 500, 502, 503, 504} and attempt < self._max_retries:
                attempt += 1
                self._sleep(float(attempt))
                continue

            raise HttpError(f"request failed with status {response.status_code}")
