class InsufficientFundsError(Exception):
    """Ошибка при недостаточном балансе кошелька."""

    def __init__(self, available: float, required: float, code: str):
        self.available = available
        self.required = required
        self.code = code

        super().__init__(
            f"Недостаточно средств: доступно {available:.4f} {code}, "
            f"требуется {required:.4f} {code}"
        )
