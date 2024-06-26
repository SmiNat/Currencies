import logging
from dataclasses import dataclass

import httpx

from .config import Config
from .connectors.local.file_reader import CurrencyRatesDatabaseConnector
from .enums import CurrencySource, DatabaseMapping, NbpWebApiUrl
from .utils import validate_currency_input_data, validate_data_source, validate_db_type

logger = logging.getLogger("currencies")


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
    A class to convert prices from various currencies to PLN using either
    a JSON file or NBP API.
    """

    # def __init__(self) -> None:
    #     """
    #     Initializes the PriceCurrencyConverterToPLN instance.

    #     Attributes:
    #     - currency_connector (CurrencyRatesDatabaseConnector):
    #       An instance of CurrencyRatesDatabaseConnector to fetch currency rate data
    #       from a JSON file.
    #     """
    #     self.currency_connector = CurrencyRatesDatabaseConnector()

    def fetch_single_currency_from_nbp(self, currency: str) -> tuple | str:
        """
        Fetches the exchange rate and date for a single currency from the NBP API.

        Args:
        - currency (str): The currency code (e.g., 'USD', 'EUR').

        Returns:
        - tuple: A tuple containing the exchange rate (float) and date (str) or
          a string message if no data found in the NPB's database.
        """
        url = f"{NbpWebApiUrl.TABLE_A_SINGLE_CURRENCY}/{currency.lower()}/?format=json"
        with httpx.Client() as client:
            response = client.get(url)
            logger.debug("NPB's API response: %s" % response.text)

            if response.status_code == 404:
                logger.debug("No currency for '%s' code in NBP's API." % currency)
                return f"Currency with code '{currency}' was not found in the NPB's database."

            logger.debug("NPB's API response: %s" % response.json())

            data = response.json()["rates"][0]
            rate = data["mid"]
            date = data["effectiveDate"]
            return rate, date

    def fetch_single_currency_from_local_database(self, currency: str) -> tuple | str:
        """
        Fetches the exchange rate and date for a single currency from a JSON file.

        Args:
        - currency (str): The currency code (e.g., 'USD', 'EUR').

        Returns:
        - tuple | str: A tuple containing the exchange rate (float) and date (str)
          or a string message if no data found in the database.
        """
        currency_connector = CurrencyRatesDatabaseConnector()
        data = currency_connector.get_currency_latest_data(currency)
        logger.debug("Latest database data for '%s' currency: %s" % (currency, data))

        if not data:
            logger.debug("No currency code '%s' in local database." % currency)
            return f"No database record for currency '{currency}'."
        return data["rate"], data["date"]

    def convert_to_pln(
        self, currency: str, price: float, source: str, db_type: str | None = None
    ) -> ConvertedPricePLN:
        """
        Converts a price from a specified currency to PLN based on the given source.

        Args:
        - currency (str): The currency code (e.g., 'USD', 'EUR').
        - price (float): The price in the source currency.
        - source (str): The source of currency data ('JSON file' or 'API NBP').
        - db_type (str | None): The type of database to save the converted price to
          ('JSON' or 'SQLITE'). If None, the default database type will be used.

        Returns:
        - ConvertedPricePLN: An instance of ConvertedPricePLN containing converted data.
        """
        validate_data_source(source)
        validate_currency_input_data(currency, price=price)

        if source.lower() == CurrencySource.JSON_FILE.value:
            rate, date = self.fetch_single_currency_from_local_database(currency)
        elif source.lower() == CurrencySource.API_NBP.value:
            rate, date = self.fetch_single_currency_from_nbp(currency)

        result = {
            "price_in_source_currency": price,
            "currency": currency,
            "currency_rate": rate,
            "price_in_pln": round(price * rate, 2),
            "currency_rate_fetch_date": date,
        }

        entity = ConvertedPricePLN(**result)
        self._save_to_database(entity, db_type)

        return entity

    def _save_to_database(
        self, entity: ConvertedPricePLN, db_type: str | None = None
    ) -> None:
        """
        Saves the converted price entity to the specified database type.

        Args:
        - entity (ConvertedPricePLN): The entity containing the converted price
          data to be saved.
        - db_type (str | None): The type of database to save the entity to.
          Can be either 'sqlite' or 'json' type. If None, the default database
          type is determined by the current environment configuration with 'sqlite'
          for the production database or 'json' for the development database.

        Returns:
        - None.
        """
        if db_type:
            validate_db_type(db_type)

        if not db_type:
            db_type = DatabaseMapping(Config.ENV_STATE.upper())

        if db_type == DatabaseMapping.PROD:
            from .connectors.database.sqlite import SQLiteDatabaseConnector  # noqa E402

            connector = SQLiteDatabaseConnector()

        elif db_type == DatabaseMapping.DEV:
            from .connectors.database.json import JsonFileDatabaseConnector  # noqa E402

            connector = JsonFileDatabaseConnector()

        connector.save(entity)
