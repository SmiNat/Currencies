import logging

import httpx

from .config import Config
from .connectors.database.json import JsonFileDatabaseConnector
from .connectors.database.sqlite import SQLiteDatabaseConnector
from .connectors.local.file_reader import CurrencyRatesDatabaseConnector
from .enums import CurrencySource, NbpWebApiUrl
from .exceptions import CurrencyNotFoundError, DatabaseError
from .utils import ConvertedPricePLN, validate_currency_input_data, validate_data_source

logger = logging.getLogger("currencies")


class PriceCurrencyConverterToPLN:
    """
    A class to convert prices from various currencies to PLN using either
    a JSON file or NBP API.
    """

    def fetch_single_currency_from_nbp(self, currency: str) -> tuple | str:
        """
        Fetches the exchange rate and date for a single currency from the NBP API.

        Args:
        - currency (str): The currency code (e.g., 'USD', 'EUR').
        """
        url = f"{NbpWebApiUrl.TABLE_A_SINGLE_CURRENCY}/{currency.lower()}/?format=json"
        try:
            with httpx.Client() as client:
                response = client.get(url)

                if response.status_code == 404:
                    logger.debug("NPB's API response: %s" % response.text)
                    logger.debug("No currency for '%s' code in NBP's API." % currency)
                    return f"Currency with code '{currency}' was not found in the NPB's database."

                logger.debug("NPB's API response: %s" % response.json())

                data = response.json()["rates"][0]
                rate = data["mid"]
                date = data["effectiveDate"]
                return rate, date
        except httpx.RequestError as exc:
            logger.error(f"An error occurred while requesting {exc.request.url!r}.")
            raise CurrencyNotFoundError(currency=currency)
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}."
            )
            raise CurrencyNotFoundError(currency=currency)

    def fetch_single_currency_from_local_database(self, currency: str) -> tuple | str:
        """
        Fetches the exchange rate and date for a single currency from a JSON file.

        Args:
        - currency (str): The currency code (e.g., 'USD', 'EUR').
        """
        try:
            currency_connector = CurrencyRatesDatabaseConnector()
            data = currency_connector.get_currency_latest_data(currency)
            if not data:
                logger.debug("No currency code '%s' in local database." % currency)
                return f"No database record for currency '{currency}'."
            logger.debug(
                "Latest database data for '%s' currency: %s" % (currency, data)
            )
            return data["rate"], data["date"]
        except FileNotFoundError:
            logger.error("Local database file not found.")
            raise DatabaseError()
        except Exception as e:
            logger.error(f"Error fetching data from local database: {e}")
            raise

    def convert_to_pln(
        self, amount: float | int, currency: str, data_source: str
    ) -> ConvertedPricePLN:
        """
        Converts a price from a specified currency to PLN based on the given source.

        Args:
        - amount (float | int): The price in the source currency.
        - currency (str): The currency code (e.g., 'USD', 'EUR').
        - data_source (str): The source of currency data ('JSON file' or 'API NBP').
        """
        validate_data_source(data_source)
        validate_currency_input_data(amount, currency)

        if data_source.lower() == CurrencySource.JSON_FILE.value:
            rate, date = self.fetch_single_currency_from_local_database(currency)
        elif data_source.lower() == CurrencySource.API_NBP.value:
            rate, date = self.fetch_single_currency_from_nbp(currency)

        result = {
            "amount": amount,
            "currency": currency,
            "currency_rate": rate,
            "currency_date": date,
            "price_in_pln": round(amount * rate, 2),
        }

        entity = ConvertedPricePLN(**result)
        self._save_to_database(entity)

        return entity

    def _save_to_database(self, entity: ConvertedPricePLN) -> None:
        """
        Saves the converted price entity to the specified database type.

        Args:
        - entity (ConvertedPricePLN): The entity containing the converted price
          data to be saved.
        """
        db_type = Config.ENV_STATE

        try:
            if db_type == "prod":
                connector = SQLiteDatabaseConnector()
            elif db_type == "dev":
                connector = JsonFileDatabaseConnector()
            else:
                raise DatabaseError()

            connector.save(entity)

        except Exception as e:
            logger.error(f"Error saving data to the database: {e}")
            raise
