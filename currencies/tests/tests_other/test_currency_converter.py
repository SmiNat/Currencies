import json
import logging
from http import HTTPStatus
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest
from httpx import HTTPStatusError, Request, RequestError, Response

from currencies.config import Config
from currencies.connectors.local.file_reader import CurrencyRatesDatabaseConnector
from currencies.currency_converter import PriceCurrencyConverterToPLN
from currencies.database_config import CurrencyData
from currencies.exceptions import DatabaseError

logger = logging.getLogger("currencies")


def test_PriceCurrencyConverterToPLN_init():
    price = PriceCurrencyConverterToPLN()
    assert isinstance(price, PriceCurrencyConverterToPLN)


def test_fetch_single_currency_from_nbp_success():
    # Mock response data
    mock_data = {"rates": [{"mid": 4.15, "effectiveDate": "2023-09-01"}]}

    # Mock client instance and response
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = HTTPStatus.OK
    mock_response.json.return_value = mock_data
    mock_client.get.return_value = mock_response

    with patch("httpx.Client") as mock_http_client:
        mock_http_client.return_value.__enter__.return_value = mock_client

        converter = PriceCurrencyConverterToPLN()

        # Upper case
        rate, date = converter.fetch_single_currency_from_nbp("USD")

        assert rate == 4.15
        assert date == "2023-09-01"
        mock_client.get.assert_called_once()

        # Case insensitive
        rate, date = converter.fetch_single_currency_from_nbp("usD")

        assert rate == 4.15
        assert date == "2023-09-01"
        mock_client.get.assert_called()


def test_fetch_single_currency_from_nbp_404_if_currency_not_found():
    # Mock client instance and response for 404 scenario
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = HTTPStatus.NOT_FOUND
    mock_client.get.return_value = mock_response

    with patch("httpx.Client") as mock_http_client:
        mock_http_client.return_value.__enter__.return_value = mock_client

        converter = PriceCurrencyConverterToPLN()

        # Invalid currency ticker
        result = converter.fetch_single_currency_from_nbp("XYZ")

        assert isinstance(result, str)  # Check if result is a string
        assert "Currency with code 'XYZ' was not found" in result
        mock_client.get.assert_called_once()


def test_fetch_single_currency_from_nbp_invaid_currency_type():
    # Mock client instance and response for 404 scenario
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = HTTPStatus.NOT_FOUND
    mock_client.get.return_value = mock_response

    with patch("httpx.Client") as mock_http_client:
        mock_http_client.return_value.__enter__.return_value = mock_client

        converter = PriceCurrencyConverterToPLN()

        # Invalid currency type
        with pytest.raises(TypeError) as exc_info:
            converter.fetch_single_currency_from_nbp(123)

        assert (
            "Invalid data type for currency_code attribute. Required type: string."
            in str(exc_info.value)
        )


@patch.object(PriceCurrencyConverterToPLN, "fetch_single_currency_from_nbp")
def test_fetch_single_currency_from_nbp_requesterror_raised(
    mock_fetch_single_currency_from_nbp,
):
    mock_fetch_single_currency_from_nbp.side_effect = RequestError(
        "Request error message"
    )

    converter = PriceCurrencyConverterToPLN()

    with pytest.raises(RequestError):
        converter.fetch_single_currency_from_nbp("USD")


@patch.object(PriceCurrencyConverterToPLN, "fetch_single_currency_from_nbp")
def test_fetch_single_currency_from_nbp_httpstatuserror_raised(
    mock_fetch_single_currency_from_nbp,
):
    # Mock the request and response
    mock_request = Mock(spec=Request)
    mock_response = Mock(spec=Response)

    mock_fetch_single_currency_from_nbp.side_effect = HTTPStatusError(
        "HTTP status error message", request=mock_request, response=mock_response
    )

    converter = PriceCurrencyConverterToPLN()

    with pytest.raises(HTTPStatusError):
        converter.fetch_single_currency_from_nbp("USD")


@patch.object(httpx.Client, "get")
def test_fetch_single_currency_from_nbp_missing_rates(mock_get):
    mocked_api_response = {
        "table": "A",
        "currency": "dolar amerykański",
        "code": "USD",
        "invalid": [
            {
                "no": "134/A/NBP/2024",
                "effectiveDate": "2024-07-11",
                "mid": 3.9257,
            }
        ],
    }

    mock_get.return_value.json.return_value = mocked_api_response

    converter = PriceCurrencyConverterToPLN()

    with pytest.raises(KeyError):
        converter.fetch_single_currency_from_nbp("USD")


@patch.object(PriceCurrencyConverterToPLN, "fetch_single_currency_from_nbp")
def test_fetch_single_currency_from_nbp_network_error(
    mock_fetch_single_currency_from_nbp,
):
    mock_fetch_single_currency_from_nbp.side_effect = RequestError("Network error")

    converter = PriceCurrencyConverterToPLN()

    with pytest.raises(RequestError):
        converter.fetch_single_currency_from_nbp("USD")


def test_fetch_single_currency_from_local_database_success_with_fixture(
    mock_file_directory,
):
    converter = PriceCurrencyConverterToPLN()
    assert converter.fetch_single_currency_from_local_database("EUR") == (
        4.25,
        "2022-10-10",
    )


def test_fetch_single_currency_from_local_database_success_with_fixture_case_insensitive(
    mock_file_directory,
):
    converter = PriceCurrencyConverterToPLN()
    assert converter.fetch_single_currency_from_local_database("eUr") == (
        4.25,
        "2022-10-10",
    )


def test_fetch_single_currency_from_local_database_success_with_patch():
    with patch.object(
        CurrencyRatesDatabaseConnector,
        "get_currency_latest_data",
        return_value={"date": "2024-05-30", "rate": 4.1},
    ):
        converter = PriceCurrencyConverterToPLN()
        assert converter.fetch_single_currency_from_local_database("EUR") == (
            4.1,
            "2024-05-30",
        )


def test_fetch_single_currency_from_local_database_no_currency_data_with_fixture(
    mock_file_directory,
):
    converter = PriceCurrencyConverterToPLN()
    assert (
        "No database record for currency 'JPY abcd'"
        in converter.fetch_single_currency_from_local_database("JPY abcd")
    )


def test_fetch_single_currency_from_local_database_no_currency_data_with_patch():
    with patch.object(
        CurrencyRatesDatabaseConnector,
        "get_currency_latest_data",
        return_value={},
    ):
        converter = PriceCurrencyConverterToPLN()
        assert (
            "No database record for currency 'EUR'"
            in converter.fetch_single_currency_from_local_database("EUR")
        )


@patch.object(CurrencyRatesDatabaseConnector, "get_currency_latest_data")
def test_fetch_single_currency_from_local_database_empty_data(
    mock_get_currency_latest_data,
):
    mock_get_currency_latest_data.return_value = None

    converter = PriceCurrencyConverterToPLN()

    result = converter.fetch_single_currency_from_local_database("EUR")
    assert result == "No database record for currency 'EUR'."


@patch.object(CurrencyRatesDatabaseConnector, "get_currency_latest_data")
def test_fetch_single_currency_from_local_database_key_error(
    mock_get_currency_latest_data,
):
    mock_get_currency_latest_data.return_value = {"invalid_key": "value"}

    converter = PriceCurrencyConverterToPLN()

    with pytest.raises(DatabaseError) as exc_info:
        converter.fetch_single_currency_from_local_database("EUR")
    assert "Invalid database structure. Unable to locate 'rate' key." in str(
        exc_info.value
    )


@patch.object(CurrencyRatesDatabaseConnector, "get_currency_latest_data")
def test_fetch_single_currency_from_local_database_file_not_found(
    mock_get_currency_latest_data,
):
    mock_get_currency_latest_data.side_effect = FileNotFoundError("File not found")

    converter = PriceCurrencyConverterToPLN()

    with pytest.raises(DatabaseError) as exc_info:
        converter.fetch_single_currency_from_local_database("EUR")
    assert (
        "Unable to set proper connector to the database. Check the environment settings"
        in str(exc_info.value)
    )


def test_fetch_single_currency_from_local_database_invalid_currency_type_with_fixture(
    mock_file_directory,
):
    converter = PriceCurrencyConverterToPLN()
    with pytest.raises(TypeError) as exc_info:
        converter.fetch_single_currency_from_local_database(123)
    assert "Invalid data type for currency attribute. Required type: string." in str(
        exc_info.value
    )


def test_convert_to_pln_saving_to_json_with_local_db_currency(json_db, json_db_path):
    # Check initial state of the database
    local_db = json_db
    amounts = [value["amount"] for value in local_db.values()]
    assert 200 not in amounts

    with patch.object(Config, "ENV_STATE", "dev"):
        with patch(
            "currencies.connectors.database.json.get_local_db",
            side_effect=lambda: json_db_path,
        ):
            converter = PriceCurrencyConverterToPLN()
            converter.convert_to_pln(200, "EUR", "local database")

            # Reload the database to check the updated state
            with open(json_db_path, "r") as file:
                updated_db = json.load(file)

            amounts = [value["amount"] for value in updated_db.values()]
            assert 200 in amounts


@patch.object(httpx.Client, "get")
def test_convert_to_pln_saving_to_json_with_api_nbp_currency(
    mock_get, json_db, json_db_path
):
    mocked_api_response = {
        "table": "A",
        "currency": "dolar amerykański",
        "code": "USD",
        "rates": [
            {
                "no": "134/A/NBP/2024",
                "effectiveDate": "2024-07-11",
                "mid": 3.9257,
            }
        ],
    }

    # Check initial state of the database
    amounts = [value["amount"] for value in json_db.values()]
    assert 200 not in amounts
    currency_rates = [value["currency_rate"] for value in json_db.values()]
    assert 3.9257 not in currency_rates
    logger.debug("JSON DATA BEFORE: %s" % json_db)

    # Converting new currency to PLN and saving data to the json database (dev env)
    with patch.object(Config, "ENV_STATE", "dev"):
        with patch(
            "currencies.connectors.database.json.get_local_db",
            side_effect=lambda: json_db_path,
        ):
            mock_get.return_value.json.return_value = mocked_api_response
            logger.debug("Mock applied: %s" % mock_get.return_value.json.return_value)
            converter = PriceCurrencyConverterToPLN()
            result = converter.convert_to_pln(200, "USD", "api nbp")
            logger.debug("Convert to PLN result: %s" % result)

            # Reload the database to check the updated state
            with open(json_db_path, "r") as file:
                updated_db = json.load(file)

            amounts = [value["amount"] for value in updated_db.values()]
            currency_rates = [value["currency_rate"] for value in updated_db.values()]

            logger.debug("JSON DATA AFTER: %s" % json_db)
            assert 200 in amounts
            assert 3.9257 in currency_rates


def test_convert_to_pln_saving_to_sqlite_with_local_database(
    db_session, sqlite_db_initial_data
):
    # Check initial state of the database
    assert db_session.query(CurrencyData).count() == 2
    amounts = db_session.query(CurrencyData.amount).distinct().all()
    unique_amounts = [amount[0] for amount in amounts]  # Extract values from the tuples
    assert 200 not in unique_amounts

    with patch.object(Config, "ENV_STATE", "prod"):
        with patch(
            "currencies.connectors.database.sqlite.get_db", return_value=db_session
        ):
            converter = PriceCurrencyConverterToPLN()
            converter.convert_to_pln(200, "EUR", "local database")

            amounts = db_session.query(CurrencyData.amount).distinct().all()
            unique_amounts = [amount[0] for amount in amounts]
            assert 200 in unique_amounts


@patch.object(httpx.Client, "get")
def test_convert_to_pln_saving_to_sqlite_with_api_nbp_currency(
    mock_get, db_session, sqlite_db_initial_data
):
    mocked_api_response = {
        "table": "A",
        "currency": "dolar amerykański",
        "code": "USD",
        "rates": [
            {
                "no": "134/A/NBP/2024",
                "effectiveDate": "2024-07-11",
                "mid": 3.9257,
            }
        ],
    }

    # Check initial state of the database
    assert db_session.query(CurrencyData).count() == 2

    amounts = db_session.query(CurrencyData.amount).distinct().all()
    unique_amounts = [amount[0] for amount in amounts]  # Extract values from the tuples
    assert 200 not in unique_amounts

    currency_rates = db_session.query(CurrencyData.currency_rate).distinct().all()
    unique_currency_rates = [
        currency_rate[0] for currency_rate in currency_rates
    ]  # Extract values from the tuples
    assert 3.9257 not in unique_currency_rates

    logger.debug("SQLITE DATA BEFORE: %s" % db_session.query(CurrencyData).all())

    # Converting new currency to PLN and saving data to the sqlite database (prod env)
    with patch.object(Config, "ENV_STATE", "prod"):
        with patch(
            "currencies.connectors.database.sqlite.get_db", return_value=db_session
        ):
            mock_get.return_value.json.return_value = mocked_api_response
            logger.debug("Mock applied: %s" % mock_get.return_value.json.return_value)
            converter = PriceCurrencyConverterToPLN()
            result = converter.convert_to_pln(200, "USD", "api nbp")
            logger.debug("Convert to PLN result: %s" % result)

            logger.debug("SQLITE DATA AFTER: %s" % db_session.query(CurrencyData).all())

            amounts = db_session.query(CurrencyData.amount).distinct().all()
            unique_amounts = [amount[0] for amount in amounts]
            assert 200 in unique_amounts

            currency_rates = (
                db_session.query(CurrencyData.currency_rate).distinct().all()
            )
            unique_currency_rates = [
                currency_rate[0] for currency_rate in currency_rates
            ]
            assert 3.9257 in unique_currency_rates
