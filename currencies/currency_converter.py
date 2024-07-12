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
    a local currency database in JSON file or external API of NBP for currency rate extraction.
    Converted data is saved either to JSON database (for 'dev' envirionment state)
    or to SQLITE database (for 'prod' envirionment state).
    """

    def fetch_single_currency_from_nbp(self, currency_code: str) -> tuple | str:
        """Fetches the exchange rate and date for a single currency from the NBP API."""
        if not isinstance(currency_code, str):
            raise TypeError(
                "Invalid data type for currency_code attribute. Required type: string."
            )
        url = f"{NbpWebApiUrl.TABLE_A_SINGLE_CURRENCY}/{currency_code.lower()}/?format=json"
        try:
            with httpx.Client() as client:
                response = client.get(url)

                if response.status_code == 404:
                    logger.debug("NPB's API response: %s" % response.text)
                    logger.debug(
                        "No currency for '%s' code in NBP's API." % currency_code
                    )
                    return f"Currency with code '{currency_code}' was not found in the NPB's database."

                logger.debug("NPB's API response: %s" % response.json())

                data = response.json()["rates"][0]
                rate = data["mid"]
                date = data["effectiveDate"]
                return rate, date
        except KeyError:
            logger.error("Invalid data extraction from API NBP.")
            raise
        except httpx.RequestError as exc:
            logger.error(f"An error occurred while requesting {exc.request.url!r}.")
            raise CurrencyNotFoundError(currency=currency_code)
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}."
            )
            raise CurrencyNotFoundError(currency=currency_code)

    def fetch_single_currency_from_local_database(
        self, currency_code: str
    ) -> tuple | str:
        """Fetches the exchange rate and date for a single currency from a JSON file."""
        if not isinstance(currency_code, str):
            raise TypeError(
                "Invalid data type for currency attribute. Required type: string."
            )
        try:
            currency_connector = CurrencyRatesDatabaseConnector()
            data = currency_connector.get_currency_latest_data(currency_code)
            if not data:
                logger.debug("No currency code '%s' in local database." % currency_code)
                return f"No database record for currency '{currency_code}'."
            logger.debug(
                "Latest database data for '%s' currency: %s" % (currency_code, data)
            )
            return data["rate"], data["date"]
        except KeyError as e:
            logger.error("Local database file has incorrect dict structure.")
            raise DatabaseError(
                "Invalid database structure. Unable to locate %s key." % e
            )
        except FileNotFoundError:
            logger.error("Local database file not found.")
            raise DatabaseError()
        except Exception as e:
            logger.error(f"Error fetching data from local database: {e}")
            raise

    def convert_to_pln(
        self, amount: float | int, currency_code: str, data_source: str
    ) -> ConvertedPricePLN:
        """
        Converts a price from a specified currency to PLN based on the given source.

        Args:
        - amount (float | int): The price in the source currency.
        - currency_code (str): The currency code (e.g., 'USD', 'EUR').
        - data_source (str): The source of currency data (either 'local database' or 'API NBP').
        """
        validate_data_source(data_source)
        validate_currency_input_data(amount, currency_code)

        try:
            if data_source.lower() == CurrencySource.JSON_FILE.value:
                rate, date = self.fetch_single_currency_from_local_database(
                    currency_code
                )
            elif data_source.lower() == CurrencySource.API_NBP.value:
                rate, date = self.fetch_single_currency_from_nbp(currency_code)

            result = {
                "amount": amount,
                "currency": currency_code,
                "currency_rate": rate,
                "currency_date": date,
                "price_in_pln": round(amount * rate, 2),
            }

            entity = ConvertedPricePLN(**result)
            self._save_to_database(entity)

            return entity

        except (TypeError, ValueError) as e:
            logger.error(f"Error converting currency: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            raise

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
