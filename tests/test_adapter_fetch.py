import importlib


sec_mod = importlib.import_module("src.ingestion.adapters.sec_edgar")
dart_mod = importlib.import_module("src.ingestion.adapters.opendart")
fred_mod = importlib.import_module("src.ingestion.adapters.fred")
ecos_mod = importlib.import_module("src.ingestion.adapters.ecos")

SecEdgarAdapter = sec_mod.SecEdgarAdapter
OpenDartAdapter = dart_mod.OpenDartAdapter
FredAdapter = fred_mod.FredAdapter
EcosAdapter = ecos_mod.EcosAdapter


class RecordingClient:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def request_json(self, url, headers=None):
        self.calls.append((url, headers or {}))
        return self.payload


def test_sec_adapter_fetches_with_user_agent_header():
    client = RecordingClient({"facts": {}})
    adapter = SecEdgarAdapter(client=client, user_agent="team@example.com")
    result = adapter.fetch_company_facts("0000320193")

    called_url, called_headers = client.calls[0]
    assert "companyfacts" in called_url
    assert called_headers["User-Agent"] == "team@example.com"
    assert result["source"] == "sec_edgar"


def test_dart_adapter_builds_query_with_key_and_corp_code():
    client = RecordingClient({"status": "000"})
    adapter = OpenDartAdapter(client=client, api_key="KEY123")
    result = adapter.fetch_company("00126380")

    called_url, _ = client.calls[0]
    assert "crtfc_key=KEY123" in called_url
    assert "corp_code=00126380" in called_url
    assert result["source"] == "opendart"


def test_fred_adapter_builds_series_observation_url():
    client = RecordingClient({"observations": []})
    adapter = FredAdapter(client=client, api_key="FREDKEY")
    result = adapter.fetch_series_observations("CPIAUCSL")

    called_url, _ = client.calls[0]
    assert "series_id=CPIAUCSL" in called_url
    assert "api_key=FREDKEY" in called_url
    assert result["source"] == "fred"


def test_ecos_adapter_builds_statistic_url():
    client = RecordingClient({"StatisticSearch": {"row": []}})
    adapter = EcosAdapter(client=client, api_key="ECOSKEY")
    result = adapter.fetch_statistic("722Y001")

    called_url, _ = client.calls[0]
    assert "ECOSKEY" in called_url
    assert "722Y001" in called_url
    assert result["source"] == "ecos"
