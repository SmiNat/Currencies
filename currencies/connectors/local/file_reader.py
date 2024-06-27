import json
import logging
import os

from ...enums import LocalDatabaseUrl
from ...utils import validate_currency_input_data

logger = logging.getLogger("currencies")

LOCAL_CURRENCY = LocalDatabaseUrl.CURRENCY_RATES_URL


class CurrencyRatesDatabaseConnector:
    """A connector class to retrieve currency rate data from a JSON file database."""

    def __init__(self) -> None:
        """
        Initializes the connector by reading data from the JSON file at
        the specified URL.

        Attributes:
        - _data (dict): The in-memory representation of the database.
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
        if not os.path.exists(LOCAL_CURRENCY):
            raise FileNotFoundError("Unable to locate file: %s" % LOCAL_CURRENCY)

        try:
            with open(LOCAL_CURRENCY, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Error reading data: %s" % e)
            return {}

    def _write_data(self) -> None:
        """
        Writes the current _data to the JSON file.

        Returns:
        - None.
        """
        if not os.path.exists(LOCAL_CURRENCY):
            raise FileNotFoundError("Unable to locate file: %s" % LOCAL_CURRENCY)
        try:
            with open(LOCAL_CURRENCY, "w") as file:
                json.dump(self._data, file, indent=4)
        except IOError as e:
            logger.error("Error writing data to %s: %s" % (LOCAL_CURRENCY, e))
            raise

    def get_all(self) -> dict:
        """
        Retrieves all currency data from the database.

        Returns:
        - dict[str, list[dict[str, Any]]]: A dictionary where keys are currency
          codes (e.g., 'EUR', 'CZK') and values are lists of dictionaries
          with currency data.
        """
        return self._data

    def get_currency_data(self, currency: str) -> list[dict]:
        """
        Retrieves data for a single currency from the database.

        Args:
        - currency (str): The currency code given in ISO 4217 currency codes
          standard (e.g., 'USD') (case-insensitive).

        Returns:
        - list[dict[str, Any]]: A list of dictionaries representing data for
          the specified currency. Returns an empty list if the currency
          code is not found.
        """
        return self._data.get(currency.upper(), [])

    def get_currency_latest_data(self, currency: str) -> dict:
        """
        Retrieves the latest rate for a single currency from the database.

        Args:
        - currency (str): The currency code given in ISO 4217 currency codes
          standard (e.g., 'USD') (case-insensitive).

        Returns:
        - dict[str, Any]: A dictionary representing the latest exchange rate for
          the specified currency, containing keys 'date' and 'rate'. Returns
          an empty dictionary if no data is found.
        """
        rates = self.get_currency_data(currency)
        if not rates:
            return {}
        sorted_data = sorted(rates, key=lambda x: x["date"], reverse=True)
        return sorted_data[0]

    def add_currency_data(self, currency: str, date: str, rate: float) -> None:
        """
        Adds or updates data for a new currency in the database.

        This method adds or updates data for a specified currency in the database.
        If the currency does not exist in the database, it adds the currency
        with relevant data.
        It validates the currency code and rate data format before proceeding
        with the update.

        Args:
        - currency (str): The currency code (e.g., 'EUR') to add/update.
        - date (str): Date in 'YYYY-MM-DD' format (e.g., '2020-10-30')
        - rate (float): Value of exchange rate.

        Returns:
            None.
        """
        validate_currency_input_data(currency, date, rate)

        currency = currency.upper()
        currency_data = {"date": date, "rate": rate}

        # Check if currency with given rate and date is already in the database
        if currency.upper() in self._data:
            if currency_data in self._data[currency]:
                logger.debug(
                    "A currency '%s' with data '%s' already exists in the database.",
                    currency,
                    currency_data,
                )
                return

        # If currency not yet in the database - add a new currency with given rate
        # and date to the database
        if currency not in list(code.upper() for code in self._data.keys()):
            self._data[currency] = [currency_data]
            self._write_data()
            return

        # Update currency data
        # Add new data to existing currency if there was no data with given date
        if not any(entry["date"] == date for entry in self._data[currency]):
            self._data[currency].append(currency_data)
        # Update exchange rate if currency already has data for the same date
        else:
            for entry in self._data[currency]:
                if entry["date"] == date:
                    entry["rate"] = rate
                    break

        self._write_data()

    def delete_currency(self, currency: str) -> str:
        """
        Deletes currency data from the database.

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
