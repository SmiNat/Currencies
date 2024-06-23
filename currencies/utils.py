from currency_codes import get_all_currencies

from .enums import CurrencySource


def validate_data_source(source: str) -> None:
    """Validate the data source value."""
    if source.lower() not in [src.value for src in CurrencySource]:
        raise ValueError(
            "Invalid data source specified. Available interest rate data sources: %s."
            % [src.value for src in CurrencySource]
        )


def list_of_all_currency_codes() -> list:
    codes = []
    for currency in get_all_currencies():
        if currency.code:
            codes.append(currency.code)
    return codes
