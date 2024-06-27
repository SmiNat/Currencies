import datetime

from currency_codes import get_all_currencies

from .enums import CurrencySource, DatabaseMapping
from .exceptions import CurrencyNotFoundError


def get_available_data_sources():
    """Returns a list of available data sources from the CurrencySource enum."""
    return [src.value for src in CurrencySource]


def validate_data_source(source: str) -> None:
    """
    Validate the data source value.

    Parameters:
    - source (str): The data source to be validated.

    Raises:
    - ValueError: If the data source is not valid.
    """
    available_sources = get_available_data_sources()
    if source.lower() not in available_sources:
        raise ValueError(
            "Invalid data source specified. Available sources: %s." % available_sources
        )


def validate_date(date: str) -> None:
    """
    Validate the currency data format and type.

    Parameters:
    - date (str): Date in 'YYYY-MM-DD' format.

    Raises:
    - TypeError: If date is not a string.
    - ValueError: If date is not in format: YYYY-MM-DD.
    """

    if isinstance(date, str):
        try:
            datetime.datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(
                "Invalid date format. Required format: 'YYYY-MM-DD' (e.g. 2020-12-30)."
            )
    else:
        raise TypeError("Invalid data type for date attribute. Required type: string.")


def validate_currency_input_data(
    currency: str | None = None,
    date: str | None = None,
    rate: float | None = None,
    price: float | int | None = None,
):
    """
    Validate the currency input data.

    Parameters:
    - currency (str): Currency code or None.
    - date (str): Date in 'YYYY-MM-DD' format or None.
    - rate (float): Currency rate or None.

    Raises:
    - TypeError: If parameters are of the wrong type.
    - CurrencyNotFoundError: If the currency code is invalid.
    """
    if currency:
        if not isinstance(currency, str):
            raise TypeError(
                "Invalid data type for currency attribute. Required type: string."
            )

        available_currencies = list_of_all_currency_codes()
        if currency.upper() not in available_currencies:
            raise CurrencyNotFoundError(
                message="Invalid currency code.",
                available_currencies=available_currencies,
            )

    if rate:
        if not isinstance(rate, float):
            raise TypeError(
                "Invalid data type for rate attribute. Required type: float."
            )

    if date:
        validate_date(date)

    if price:
        if not isinstance(price, (float, int)):
            raise TypeError(
                "Invalid data type for price attribute. Required type: float or integer."
            )


def list_of_all_currency_codes() -> list:
    """Returns list of all currency codes."""
    return [currency.code for currency in get_all_currencies() if currency.code]


def validate_db_type(db_type: str) -> None:
    if not isinstance(db_type, str):
        raise TypeError(
            "Invalid data type for db_type attribute. Required type: string."
        )

    allowed_types = [member.value for member in DatabaseMapping]

    if db_type.lower() not in allowed_types:
        raise ValueError("Invalid database type. Allowed types: %s." % allowed_types)
