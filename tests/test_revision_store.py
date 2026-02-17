import importlib


RevisionStore = importlib.import_module("src.ingestion.revision_store").RevisionStore


def test_revision_store_noop_for_same_key_and_hash():
    store = RevisionStore()
    key = "source|entity|2026-01-01|rev1"
    payload = {"x": 1}

    first = store.put(key, payload)
    second = store.put(key, payload)

    assert first.status == "inserted"
    assert second.status == "noop"


def test_revision_store_adds_revision_when_hash_changes():
    store = RevisionStore()
    key = "source|entity|2026-01-01|rev1"

    first = store.put(key, {"x": 1})
    second = store.put(key, {"x": 2})

    assert first.status == "inserted"
    assert second.status == "revision"
    assert second.revision_number == 2
