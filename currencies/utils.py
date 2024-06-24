import datetime

from currency_codes import get_all_currencies

from .enums import CurrencySource
from .exceptions import CurrencyNotFoundError


def validate_data_source(source: str) -> None:
    """
    Validate the data source value.

    Parameters:
    - source (str): The data source to be validated.

    Raises:
    - ValueError: If the data source is not valid.
    """
    available_sources = [src.value for src in CurrencySource]
    if source.lower() not in available_sources:
        raise ValueError(
            "Invalid data source specified. Available interest rates: %s."
            % available_sources
        )


def validate_currency_input_data_for_json_database(
    currency: str, date: str, rate: float
):
    """
    Validate the currency input data.

    Parameters:
    - currency (str): Currency code.
    - date (str): Date in 'YYYY-MM-DD' format.
    - rate (float): Currency rate.

    Raises:
    - TypeError: If parameters are of the wrong type.
    - CurrencyNotFoundError: If the currency code is invalid.
    """
    if not isinstance(currency, str):
        raise TypeError(
            "Invalid data type for currency variable. Required type: string."
        )

    available_currencies = list_of_all_currency_codes()
    if currency.upper() not in available_currencies:
        raise CurrencyNotFoundError(
            message="Invalid currency code.",
            available_currencies=available_currencies,
        )

    if not isinstance(rate, float):
        raise TypeError("Invalid data type for rate variable. Required type: float.")

    if isinstance(date, str):
        try:
            datetime.datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise TypeError(
                "Invalid data type for date variable. Required type: string with "
                "format: 'YYYY-MM-DD' (e.g. 2020-12-30)."
            )
    else:
        raise TypeError(
            "Invalid data type for date variable. Required type: string with "
            "format: 'YYYY-MM-DD' (e.g. 2020-12-30)."
        )


def list_of_all_currency_codes() -> list:
    """Returns list of all currency codes."""
    return [currency.code for currency in get_all_currencies() if currency.code]
