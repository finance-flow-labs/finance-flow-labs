import importlib


BudgetGuard = importlib.import_module("src.ingestion.budget_guard").BudgetGuard


def test_budget_guard_freezes_on_cap_breach():
    guard = BudgetGuard(monthly_cap=100)
    guard.record_spend(120)
    assert guard.is_frozen is True


def test_budget_guard_stays_open_under_cap():
    guard = BudgetGuard(monthly_cap=100)
    guard.record_spend(80)
    assert guard.is_frozen is False
