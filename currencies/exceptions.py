class CurrencyDataIntegrityError(Exception):
    """
    Exception raised when an attempt to insert or update data violates
    integrity constraints in the database.
    """

    def __init__(self):
        message = (
            "IntegrityError: UNIQUE constraint failed: "
            "a record with the same parameters already exists in the database."
        )
        super().__init__(message)


class CurrencyNotFoundError(Exception):
    """Exception raised when a currency is not found in the database or API."""

    def __init__(
        self,
        message: str | None = None,
        currency: str | None = None,
        available_currencies: list[str] | None = None,
    ) -> None:
        message = (
            (
                f"'{currency.upper()}' currency not found."
                if currency
                else "Currency not found."
            )
            if not message
            else message
        )
        if available_currencies:
            message += " Available currencies: %s." % available_currencies
        super().__init__(message)


class DatabaseError(Exception):
    """
    Exception raised when a database URL cannot be set.
    """

    def __init__(self, message: str | None = None):
        default = "Unable to set proper connector to the database. Check the environment settings."
        message = message if message else default
        super().__init__(message)
