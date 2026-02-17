import importlib


EcosAdapter = importlib.import_module("src.ingestion.adapters.ecos").EcosAdapter
FredAdapter = importlib.import_module("src.ingestion.adapters.fred").FredAdapter
OpenDartAdapter = importlib.import_module(
    "src.ingestion.adapters.opendart"
).OpenDartAdapter
SecEdgarAdapter = importlib.import_module(
    "src.ingestion.adapters.sec_edgar"
).SecEdgarAdapter


def test_adapters_normalize_contract_shape():
    adapters = [
        SecEdgarAdapter(),
        OpenDartAdapter(),
        FredAdapter(),
        EcosAdapter(),
    ]

    for adapter in adapters:
        normalized = adapter.normalize({"id": "X1", "value": 10})
        assert "source" in normalized
        assert "entity_id" in normalized
        assert "payload" in normalized
