import importlib


cache_policy = importlib.import_module("src.ingestion.cache_policy")
DataTier = cache_policy.DataTier
ttl_days_for_tier = cache_policy.ttl_days_for_tier
ttl_months_for_facts = cache_policy.ttl_months_for_facts


def test_gold_has_no_expiration():
    assert ttl_days_for_tier(DataTier.GOLD) is None


def test_silver_and_bronze_ttl_mapping():
    assert ttl_days_for_tier(DataTier.SILVER) == 180
    assert ttl_days_for_tier(DataTier.BRONZE) == 90
    assert ttl_months_for_facts(DataTier.SILVER) == 24
