import importlib


http_client = importlib.import_module("src.ingestion.http_client")
HttpResponse = http_client.HttpResponse
SimpleHttpClient = http_client.SimpleHttpClient


class SequenceTransport:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __call__(self, method, url, headers):
        self.calls.append((method, url, headers))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_http_client_retries_on_429_then_succeeds():
    transport = SequenceTransport(
        [
            HttpResponse(status_code=429, body=b"{}", headers={}),
            HttpResponse(status_code=200, body=b'{"ok": true}', headers={}),
        ]
    )
    sleeps = []

    client = SimpleHttpClient(
        transport=transport,
        max_retries=2,
        sleep=lambda seconds: sleeps.append(seconds),
    )
    result = client.request_json("https://example.com/data")

    assert result["ok"] is True
    assert len(transport.calls) == 2
    assert len(sleeps) >= 1


def test_http_client_applies_rate_limit_wait_between_calls():
    transport = SequenceTransport(
        [
            HttpResponse(status_code=200, body=b'{"seq": 1}', headers={}),
            HttpResponse(status_code=200, body=b'{"seq": 2}', headers={}),
        ]
    )
    now_values = [0.0, 0.0, 0.3, 1.0]
    sleeps = []

    client = SimpleHttpClient(
        transport=transport,
        rate_limit_per_second=1.0,
        now=lambda: now_values.pop(0),
        sleep=lambda seconds: sleeps.append(seconds),
    )
    client.request_json("https://example.com/a")
    client.request_json("https://example.com/b")

    assert len(transport.calls) == 2
    assert sleeps == [0.7]
