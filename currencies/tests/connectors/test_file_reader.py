from unittest.mock import mock_open, patch

import pytest

from currencies.connectors.local.file_reader import CurrencyRatesDatabaseConnector
from currencies.exceptions import CurrencyNotFoundError


def test_init():
    connector = CurrencyRatesDatabaseConnector()
    assert isinstance(connector, CurrencyRatesDatabaseConnector)


def test_read_data_file_not_found(caplog):
    with patch("builtins.open", side_effect=FileNotFoundError):
        connector = CurrencyRatesDatabaseConnector()
        assert connector._read_data() == {}
        assert "FileNotFoundError" in caplog.text


def test_read_data_json_decode_error(caplog):
    with patch("builtins.open", mock_open(read_data="invalid json data")):
        connector = CurrencyRatesDatabaseConnector()
        assert connector._read_data() == {}
        assert "JSONDecodeError" in caplog.text


def test_read_data_io_error(caplog):
    with patch("builtins.open", side_effect=OSError("IO error")):
        connector = CurrencyRatesDatabaseConnector()
        connector._read_data()

    # Check if any error message related to IO error is in the captured logs
    assert any("IO error" in log.message for log in caplog.records)


def test_get_all_read_data_from_non_existing_file_or_error():
    with patch.object(
        CurrencyRatesDatabaseConnector,
        "_read_data",
        return_value={},  # Mock the return value of _read_data
    ):
        connector = CurrencyRatesDatabaseConnector()
        exp_response = {}
        eur_data = connector.get_all()
        assert exp_response == eur_data


def test_get_all_from_currency_db_non_empty_db(currency_load_db):
    with patch.object(
        CurrencyRatesDatabaseConnector,
        "_read_data",
        return_value=currency_load_db,
    ):
        connector = CurrencyRatesDatabaseConnector()

        # Test retrieving all data for non empty DB
        exp_response = currency_load_db
        eur_data = connector.get_all()
        assert exp_response == eur_data


def test_get_all_from_currency_db_empty_db(currency_load_db):
    with patch.object(
        CurrencyRatesDatabaseConnector,
        "_read_data",
        return_value=[],
    ):
        connector = CurrencyRatesDatabaseConnector()

        # Test retrieving all data for empty DB
        exp_response = []
        eur_data = connector.get_all()
        assert exp_response == eur_data


def test_get_currency_data(currency_load_db):
    with patch.object(
        CurrencyRatesDatabaseConnector,
        "_read_data",
        return_value=currency_load_db,
    ):
        connector = CurrencyRatesDatabaseConnector()

        # Test retrieving currency data for EUR
        exp_response = [
            {"date": "2023-10-01", "rate": 4.25},
            {"date": "2023-01-30", "rate": 4.05},
        ]
        eur_data = connector.get_currency_data("EUR")
        assert exp_response == eur_data

        # Test retrieving currency data for CZK
        exp_response = [
            {"date": "2023-03-02", "rate": 0.29},
            {"date": "2023-07-30", "rate": 0.28},
        ]
        czk_data = connector.get_currency_data("CZK")
        assert exp_response == czk_data

        # Test retrieving data for non-existent currency
        non_existent_data = connector.get_currency_data("invalid")
        assert [] == non_existent_data


def test_get_currency_data_when_no_currency_secified(currency_load_db):
    with patch.object(
        CurrencyRatesDatabaseConnector,
        "_read_data",
        return_value=[],
    ):
        connector = CurrencyRatesDatabaseConnector()

        # Test retrieving currency data for unspecified currency
        exp_response = "missing 1 required positional argument: 'currency'"
        with pytest.raises(TypeError) as exc_info:
            connector.get_currency_data()
        assert exp_response in str(exc_info)


def test_get_currency_latest_data(currency_load_db):
    with patch.object(
        CurrencyRatesDatabaseConnector,
        "_read_data",
        return_value=currency_load_db,
    ):
        connector = CurrencyRatesDatabaseConnector()

        # Test retrieving latest data for EUR
        eur_latest_data = connector.get_currency_latest_data("EUR")
        assert eur_latest_data["date"] == "2023-10-01"
        assert eur_latest_data["rate"] == 4.25

        # Test retrieving latest data for CZK
        czk_latest_data = connector.get_currency_latest_data("CZK")
        assert czk_latest_data["date"] == "2023-07-30"
        assert czk_latest_data["rate"] == 0.28

        # Test retrieving latest data for non-existent currency
        non_existent_latest_data = connector.get_currency_latest_data("invalid")
        assert {} == non_existent_latest_data


def test_add_currency_data(currency_load_db):
    with patch.object(
        CurrencyRatesDatabaseConnector,
        "_read_data",
        return_value=currency_load_db,
    ):
        connector = CurrencyRatesDatabaseConnector()

        # Cheeck if 'CNY' currency is not in db
        original_data = connector.get_currency_data("CNY")
        assert [] == original_data

        # Add new currency data
        currency = "CNY"
        date = "2023-06-15"
        rate = 1.234
        connector.add_currency_data(currency, date, rate)
        # Check if the currency was added correctly
        added_data = connector.get_currency_data(currency)
        assert [{"date": date, "rate": rate}] == added_data

        # Update existing currency data - replace rate for the same date
        new_rate = 1.345
        the_same_date = date
        connector.add_currency_data(currency, the_same_date, new_rate)
        # Check if the currency data was updated correctly
        updated_data = connector.get_currency_data(currency)
        assert [{"date": date, "rate": new_rate}] == updated_data

        # Update existing currency data - add rate and date
        new_rate = 1.222
        new_date = "2024-02-02"
        connector.add_currency_data(currency, new_date, new_rate)
        # Check if the currency data was updated correctly
        updated_data = connector.get_currency_data(currency)
        assert [
            {"date": "2023-06-15", "rate": 1.345},
            {"date": new_date, "rate": new_rate},
        ] == updated_data


def test_add_currency_data_if_data_already_in_db(currency_load_db):
    with patch.object(
        CurrencyRatesDatabaseConnector,
        "_read_data",
        return_value=currency_load_db,
    ):
        connector = CurrencyRatesDatabaseConnector()

        # Cheeck if 'EUR' currency is already in db
        original_data = connector.get_currency_data("EUR")
        assert currency_load_db["EUR"] == original_data

        # Add a currency with data that already exists in db
        currency = "EUR"
        date = "2023-10-01"
        rate = 4.25
        connector.add_currency_data(currency, date, rate)
        # Check if the currency was not changed
        added_data = connector.get_currency_data(currency)
        assert added_data == original_data


@pytest.mark.parametrize(
    "currency, date, rate, error, exp_response",
    [
        (
            "invalid",
            "2023-12-12",
            1.234,
            CurrencyNotFoundError,
            "Invalid currency code. Available currencies",
        ),
        (
            "PLN",
            "invalid",
            1.234,
            ValueError,
            "Invalid date format. Required format: 'YYYY-MM-DD'",
        ),
        (
            "PLN",
            "2023-12-12",
            "invalid",
            TypeError,
            "Invalid data type for rate attribute. Required type: float",
        ),
        (
            123,
            "2023-12-12",
            1.234,
            TypeError,
            "Invalid data type for currency attribute. Required type: string",
        ),
    ],
)
def test_add_currency_data_invalid_data(
    currency_load_db,
    currency: str,
    date: str,
    rate: str | float,
    error: Exception,
    exp_response: str,
):
    with patch.object(
        CurrencyRatesDatabaseConnector,
        "_read_data",
        return_value=currency_load_db,
    ):
        connector = CurrencyRatesDatabaseConnector()

        # Add new currency data
        currency = currency
        date = date
        rate = rate

        # Check response
        with pytest.raises(error) as exc_info:
            connector.add_currency_data(currency, date, rate)
        assert exp_response in str(exc_info)


def test_delete_currency(currency_load_db):
    with patch.object(
        CurrencyRatesDatabaseConnector,
        "_read_data",
        return_value=currency_load_db,
    ):
        connector = CurrencyRatesDatabaseConnector()

        # Delete existing currency
        currency = "EUR"
        result = connector.delete_currency(currency)
        # Check if the correct message is returned
        assert result == f"Currency '{currency}' deleted from the database."
        # Check if the currency was actually deleted
        assert currency not in connector.get_all()

        # Try deleting non-existent currency
        non_existent_currency = "XYZ"
        result = connector.delete_currency(non_existent_currency)
        # Check if the correct message is returned
        assert result == "No currency to delete from the database."
