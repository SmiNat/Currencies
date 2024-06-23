import json
import logging
import os

from currency_codes import exceptions, get_currency_by_code

from ...enums import LocalDatabaseUrl
from ...exceptions import CurrencyNotFoundError
from ...utils import list_of_all_currency_codes

logger = logging.getLogger(__name__)


class CurrencyRatesDatabaseConnector:
    """
    A connector class to retrieve currency rate data from a JSON file database.

    Attributes:
    - _data (dict): The in-memory representation of the database.
    """

    def __init__(self) -> None:
        """
        Initializes the connector by reading data from the JSON file at the specified URL.
        """
        self._data = self._read_data()

    @staticmethod
    def _read_data() -> dict:
        """
        Reads data from the JSON file specified by CURRENCY_RATES_URL.

        Returns:
        - dict: The data read from the JSON file. Returns an empty dictionary
          if the file does not exist or an error occurs.
        """
        if not os.path.exists(LocalDatabaseUrl.CURRENCY_RATES_URL):
            logger.error(
                "FileNotFoundError: unable to locate file: %s",
                {LocalDatabaseUrl.CURRENCY_RATES_URL},
            )
            return {}
        try:
            with open(LocalDatabaseUrl.CURRENCY_RATES_URL, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Error reading data: %s", {e})
            return {}

    def _write_data(self) -> bool:
        """
        Writes the current _data to the JSON file.

        Raises:
        - IOError: If an error occurs while writing data to the JSON file
        """
        try:
            with open(LocalDatabaseUrl.CURRENCY_RATES_URL, "w") as file:
                json.dump(self._data, file, indent=4)
        except IOError as e:
            logger.error(
                "Error writing data to %s: %s", LocalDatabaseUrl.CURRENCY_RATES_URL, e
            )
            raise

    def get_all(self) -> dict:
        """
        Retrieves all currency rate data from the database.

        Returns:
        - dict[str, list[dict[str, Any]]]: A dictionary where keys are currency
          codes (e.g., 'EUR', 'CZK') and values are lists of dictionaries
          representing rate data.
        """
        return self._data

    def get_currency_data(self, currency: str) -> list:
        """
        Retrieves rate data for a single currency from the database.

        Args:
        - currency (str): The currency code to retrieve data for (case-insensitive).

        Returns:
        - list[dict[str, any]]: A list of dictionaries representing rate data
          for the specified currency. Returns an empty list if the currency
          code is not found.
        """
        return self._data.get(currency.upper(), [])

    def get_currency_latest_data(self, currency: str) -> dict:
        """
        Retrieves the latest rate data for a single currency from the database.

        Args:
        - currency (str): The currency code to retrieve data for (case-insensitive).

        Returns:
        - dict[str, Any]: A dictionary representing the latest rate data for
          the specified currency, containing keys 'date' and 'rate'. Returns
          an empty dictionary if no data is found.
        """
        rates = self.get_currency_data(currency)
        if not rates:
            return {}
        sorted_data = sorted(rates, key=lambda x: x["date"], reverse=True)
        return sorted_data[0]

    def add_currency_rate(self, currency: str, rate: dict) -> None:
        """
        Adds or updates rate data for a new currency in the database.

        This method adds or updates rate data for a specified currency in the database.
        If the currency does not exist in the database, it raises a CurrencyNotFoundError.
        It validates the currency code and rate data format before proceeding with the update.

        Args:
        - currency (str): The currency code (e.g., 'EUR') to add/update.
        - rate (dict[str, Any]): A dictionary representing rate data for
          the currency. Must contain 'date' and 'rate' keys.

        Raises:
        - TypeError: If the provided currency code is not a string or is empty,
          or if the rate data is not a dictionary or does not contain 'date'
          and 'rate' keys.
        - CurrencyNotFoundError: If the specified currency code does not exist
          in the database.

        Returns:
            None
        """
        try:
            get_currency_by_code(currency)
        except exceptions.CurrencyNotFoundError:
            raise CurrencyNotFoundError(currency, list_of_all_currency_codes())

        if not isinstance(currency, str) or not currency:
            raise TypeError("Invalid currency code provided: %s", currency)

        if not isinstance(rate, dict) or set(["date", "rate"]) != set(rate.keys()):
            raise TypeError("Invalid rates data provided for currency %s", currency)

        if currency.upper() in list(self._data.keys()):
            if rate in self._data[currency.upper()]:
                logger.debug(
                    "A currency '%s' with data '%s' already exists in the database",
                    currency,
                    rate,
                )
            else:
                self._data[currency.upper()].append(rate)
        else:
            self._data[currency.upper()] = [rate]

        self._write_data()

    def delete_currency(self, currency: str) -> str:
        """
        Deletes rate data for a currency from the database.

        Args:
        - currency (str): The currency code to delete (e.g., 'EUR').

        Returns:
        - str: A message indicating the result of the deletion operation.
        """
        if currency.upper() in self._data:
            del self._data[currency.upper()]
            self._write_data()
            return f"Currency '{currency}' deleted from the database."
        else:
            logger.info("Currency '%s' does not exist in the database", currency)
            return "No currency to delete from the database."
