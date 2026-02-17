class BudgetGuard:
    def __init__(self, monthly_cap: float) -> None:
        self.monthly_cap: float = monthly_cap
        self.spent: float = 0.0

    @property
    def is_frozen(self) -> bool:
        return self.spent > self.monthly_cap

    def record_spend(self, amount: float) -> None:
        self.spent += amount
