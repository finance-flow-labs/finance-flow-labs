from pathlib import Path


def test_forecast_learning_loop_migration_contains_required_tables_and_columns():
    sql = Path("migrations/008_forecast_learning_loop_tables.sql").read_text(encoding="utf-8")

    required_tokens = [
        "CREATE TABLE IF NOT EXISTS investment_theses",
        "CREATE TABLE IF NOT EXISTS forecast_records",
        "CREATE TABLE IF NOT EXISTS realization_records",
        "CREATE TABLE IF NOT EXISTS forecast_error_attributions",
        "thesis_id",
        "horizon",
        "expected_return_low",
        "expected_return_high",
        "realized_return",
        "forecast_error",
        "category",
        "data_lag",
        "regime_shift",
        "valuation_miss",
        "macro_miss",
        "execution_slippage",
        "risk_control_failure",
        "unknown",
    ]

    for token in required_tokens:
        assert token in sql


def test_forecast_learning_loop_migration_keeps_hard_soft_evidence_separation():
    sql = Path("migrations/008_forecast_learning_loop_tables.sql").read_text(encoding="utf-8")

    # Ground rule: facts(HARD) and interpretation(SOFT) must be separated in storage.
    assert "evidence_hard JSONB" in sql
    assert "evidence_soft JSONB" in sql
