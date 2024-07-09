import datetime

import pytest

from currencies.enums import CurrencySource, DatabaseMapping
from currencies.exceptions import CurrencyNotFoundError
from currencies.utils import (
    get_available_data_sources,
    list_of_all_currency_codes,
    validate_currency_input_data,
    validate_data_source,
    validate_date,
    validate_db_type,
)


def test_get_available_data_sources():
    expected_sources = [src.value for src in CurrencySource]
    actual_sources = get_available_data_sources()
    assert (
        actual_sources == expected_sources
    ), f"Expected {expected_sources}, but got {actual_sources}"


def test_validate_date_invalid_format():
    with pytest.raises(ValueError) as exc_info:
        validate_date("2020,10,10")
    assert (
        "Invalid date format. Required format: 'YYYY-MM-DD' (e.g. 2020-12-30)"
        in str(exc_info.value)
    )


def test_validate_date_invalid_type():
    with pytest.raises(TypeError) as exc_info:
        validate_date(datetime.date(2020, 10, 10))
    assert "Invalid data type for date attribute. Required type: string" in str(
        exc_info.value
    )


def test_validate_data_source(monkeypatch):
    # Define a mock function to replace get_available_data_sources
    def mock_get_available_data_sources():
        return ["mock api nbp", "mock json file"]

    # Patch the get_available_data_sources function with the mock function
    monkeypatch.setattr(
        "currencies.utils.get_available_data_sources", mock_get_available_data_sources
    )

    # Valid data test
    assert validate_data_source("mock api nbp") is None

    # Invalid data test
    with pytest.raises(ValueError) as exc_info:
        validate_data_source("invalid")
    assert (
        "Invalid data source specified. Available sources: "
        "['mock api nbp', 'mock json file']" in str(exc_info.value)
    )


def test_validate_currency_input_data_invalid_amount_type():
    with pytest.raises(TypeError) as exc_info:
        validate_currency_input_data(amount="22.1")
    assert (
        "Invalid data type for amount attribute. Required type: float or integer"
        in str(exc_info.value)
    )


def test_validate_currency_input_data_invalid_currency_type():
    with pytest.raises(TypeError) as exc_info:
        validate_currency_input_data(currency=1234)
    assert "Invalid data type for currency attribute. Required type: string" in str(
        exc_info.value
    )


def test_validate_currency_input_data_invalid_currency_code():
    with pytest.raises(CurrencyNotFoundError) as exc_info:
        validate_currency_input_data(currency="ABCD")
    assert "Invalid currency code" in str(exc_info.value)


def test_validate_currency_input_data_invalid_rate_type():
    with pytest.raises(TypeError) as exc_info:
        validate_currency_input_data(rate="22.1")
    assert "Invalid data type for rate attribute. Required type: float" in str(
        exc_info.value
    )


def test_validate_currency_input_data_invalid_price_type():
    with pytest.raises(TypeError) as exc_info:
        validate_currency_input_data(price="22.1")
    assert (
        "Invalid data type for price attribute. Required type: float or integer"
        in str(exc_info.value)
    )


def test_validate_currency_input_data_invalid_date_type():
    with pytest.raises(TypeError) as exc_info:
        validate_currency_input_data(date=123)
    assert "Invalid data type for date attribute. Required type: string" in str(
        exc_info.value
    )


def test_list_of_all_currency_codes():
    assert set(["EUR", "GBP", "USD", "PLN"]) <= set(list_of_all_currency_codes())


def test_validate_db_type():
    with pytest.raises(TypeError) as exc_info:
        validate_db_type(datetime.date(2020, 10, 10))
    assert "Invalid data type for db_type attribute. Required type: string" in str(
        exc_info.value
    )


def test_validate_db_type_allowed_types():
    allowed_types = [src.value for src in DatabaseMapping]
    with pytest.raises(ValueError) as exc_info:
        validate_db_type("invalid")
    assert f"Invalid database type. Allowed types: {allowed_types}" in str(
        exc_info.value
    )
