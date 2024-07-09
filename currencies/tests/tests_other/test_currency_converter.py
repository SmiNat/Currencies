from http import HTTPStatus
from unittest.mock import MagicMock, patch

from currencies.connectors.local.file_reader import CurrencyRatesDatabaseConnector
from currencies.currency_converter import PriceCurrencyConverterToPLN


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
        rate, date = converter.fetch_single_currency_from_nbp("USD")

        assert rate == 4.15
        assert date == "2023-09-01"
        mock_client.get.assert_called_once()


def test_fetch_single_currency_from_nbp_404():
    # Mock client instance and response for 404 scenario
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = HTTPStatus.NOT_FOUND
    mock_client.get.return_value = mock_response

    with patch("httpx.Client") as mock_http_client:
        mock_http_client.return_value.__enter__.return_value = mock_client

        converter = PriceCurrencyConverterToPLN()
        result = converter.fetch_single_currency_from_nbp("USD")

        assert isinstance(result, str)  # Check if result is a string
        assert "Currency with code 'USD' was not found" in result
        mock_client.get.assert_called_once()


def test_fetch_single_currency_from_local_database_success():
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


def test_fetch_single_currency_from_local_database_no_currency_data():
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


def test_convert_to_pln_saving_to_json(mock_config_env_state_dev):
    assert False


def test_convert_to_pln_saving_to_sqlite(mock_config_env_state_prod):
    assert False
