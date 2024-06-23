import asyncio
from dataclasses import dataclass

import httpx

from .config import Config
from .connectors.local.file_reader import CurrencyRatesDatabaseConnector
from .enums import CurrencySource, NbpWebApiUrl
from .exceptions import CurrencyNotFoundError
from .utils import validate_data_source


@dataclass(frozen=True)
class ConvertedPricePLN:
    """Data class representing a converted price in PLN."""

    price_in_source_currency: float
    currency: str
    currency_rate: float
    currency_rate_fetch_date: str
    price_in_pln: float


class PriceCurrencyConverterToPLN:
    """
    A class to convert prices from various currencies to PLN using either a JSON file or NBP API.

    Methods:
    - fetch_single_currency_from_nbp(currency: str) -> tuple:
      Fetches the exchange rate and date for a single currency from the NBP API.
      Raises CurrencyNotFound if the currency is not found.

    - fetch_single_currency_from_database(currency: str) -> tuple:
      Fetches the exchange rate and date for a single currency from a JSON file.
      Raises CurrencyNotFound if the currency is not found.

    - convert_to_pln(*, currency: str, price: float, source: str) -> ConvertedPricePLN:
      Converts a price from a specified currency to PLN based on the given source.
      Validates the source and fetches data accordingly from JSON file or NBP API.
      Raises ValueError if database source is invalid.
    """

    def __init__(self) -> None:
        """
        Initializes the PriceCurrencyConverterToPLN instance.

        Usage:
        eur_converter = PriceCurrencyConverterToPLN()
        print(eur_converter.convert_to_pln("EUR", 100, "json file"))

        Attributes:
        - currency_connector (CurrencyRatesDatabaseConnector):
          An instance of CurrencyRatesDatabaseConnector to fetch currency rate data
          from a JSON file.
        """
        self.currency_connector = CurrencyRatesDatabaseConnector()

    async def fetch_single_currency_from_nbp(self, currency: str) -> tuple:
        """
        Fetches the exchange rate and date for a single currency from the NBP API.

        Args:
        - currency (str): The currency code (e.g., 'USD', 'EUR').

        Returns:
        - tuple: A tuple containing the exchange rate (float) and date (str).

        Raises:
        - CurrencyNotFound: If the currency is not found in the API.
        """
        url = f"{NbpWebApiUrl.TABLE_A_SINGLE_CURRENCY}/{currency.lower()}/?format=json"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 404:
                raise CurrencyNotFoundError(currency)
            data = response.json()["rates"][0]
            rate = data["mid"]
            date = data["effectiveDate"]
            return rate, date

    def fetch_single_currency_from_database(self, currency: str) -> tuple:
        """
        Fetches the exchange rate and date for a single currency from a JSON file.

        Args:
        - currency (str): The currency code (e.g., 'USD', 'EUR').

        Returns:
        - tuple: A tuple containing the exchange rate (float) and date (str).

        Raises:
        - CurrencyNotFound: If the currency is not found in the database.
        """
        data = self.currency_connector.get_currency_latest_data(currency)
        return data["rate"], data["date"]

    def convert_to_pln(
        self, currency: str, price: float, source: str
    ) -> ConvertedPricePLN:
        """
        Converts a price from a specified currency to PLN based on the given source.

        Args:
        - currency (str): The currency code (e.g., 'USD', 'EUR').
        - price (float): The price in the source currency.
        - source (str): The source of currency data ('JSON file' or 'API NBP').

        Returns:
        - ConvertedPricePLN: An instance of ConvertedPricePLN containing converted data.

        Raises:
        - ValueError: If an invalid data source is specified.
        - CurrencyNotFound: If the currency is not found in the specified source.
        """
        validate_data_source(source)

        if source.lower() == CurrencySource.JSON_FILE.value:
            rate, date = self.fetch_single_currency_from_database(currency)
        elif source.lower() == CurrencySource.API_NBP.value:
            rate, date = asyncio.run(self.fetch_single_currency_from_nbp(currency))

        result = {
            "price_in_source_currency": price,
            "currency": currency,
            "currency_rate": rate,
            "price_in_pln": round(price * rate, 2),
            "currency_rate_fetch_date": date,
        }

        entity = ConvertedPricePLN(**result)
        self._save_to_database(entity)

        return entity

    def _save_to_database(self, entity: ConvertedPricePLN) -> None:
        if Config.ENV_STATE == "prod":
            from .connectors.database.sqlite import SQLiteDatabaseConnector  # noqa

            connector = SQLiteDatabaseConnector()
        if Config.ENV_STATE == "dev":
            from .connectors.database.json import JsonFileDatabaseConnector  # noqa

            connector = JsonFileDatabaseConnector()

        connector.save(entity)
