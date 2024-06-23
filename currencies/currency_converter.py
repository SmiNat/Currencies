import asyncio
import json
from dataclasses import dataclass

import httpx

from .enums import CurrencySource, LocalDatabaseUrl, NbpWebApiUrl
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

    def save_to_database():
        pass  # OKODOWAĆ z użyciem Connectora i zapisać przy init - doczytać jak to zrobić dla dataclass


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
        with open(LocalDatabaseUrl.CURRENCY_RATES_URL) as file:
            data = json.load(file)
        if currency.upper() not in list(data.keys()):
            raise CurrencyNotFoundError(currency, list(data.keys()))

        sorted_data = sorted(data[currency], key=lambda x: x["date"], reverse=True)
        most_current = sorted_data[0]
        return most_current["rate"], most_current["date"]

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
        return ConvertedPricePLN(**result)
