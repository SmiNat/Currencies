class CurrencyNotFoundError(Exception):
    """Exception raised when a currency is not found in the database or API."""

    def __init__(
        self, currency: str | None = None, available_currencies: list[str] | None = None
    ) -> None:
        message = (
            f"'{currency.upper()}' currency not found."
            if currency
            else "Currency not found."
        )
        if available_currencies:
            message += " Available currencies: %s." % available_currencies
        super().__init__(message)
