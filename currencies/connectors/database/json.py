import json
import logging
import os
from collections import OrderedDict

from ...currency_converter import ConvertedPricePLN
from ...utils import validate_currency_input_data

logger = logging.getLogger("currencies")


JSON_DATABASE_NAME = os.environ.get("JSON_DATABASE_NAME")


class JsonFileDatabaseConnector:
    """A connector class to retrieve and update data from a JSON database file."""

    def __init__(self) -> None:
        """
        Initializes the connector by reading data from the JSON file at the
        specified URL.

        Attributes:
        - _data (dict): The in-memory representation of the database.
        """
        self._data = self._read_data()

    @staticmethod
    def _read_data() -> dict:
        """
        Reads data from the JSON file.

        Returns:
        - dict[str, Any]: The data read from the JSON file. Returns an empty
          dictionary if the file does not exist or an error occurs.
        """
        if not os.path.exists(JSON_DATABASE_NAME):
            raise FileNotFoundError("Unable to locate file: %s" % JSON_DATABASE_NAME)
        try:
            with open(JSON_DATABASE_NAME, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Error reading data: %s", {e})
            return {}

    def _write_data(self) -> None:
        """
        Writes the current state of the in-memory database (_data) to the JSON file.

        Returns:
        - None.
        """
        if not os.path.exists(JSON_DATABASE_NAME):
            raise FileNotFoundError("Unable to locate file: %s" % JSON_DATABASE_NAME)
        try:
            with open(JSON_DATABASE_NAME, "w") as file:
                json.dump(self._data, file, indent=4)
        except IOError as e:
            logger.error("Error writing data to %s: %s", JSON_DATABASE_NAME, e)
            raise

    def save(self, entity: ConvertedPricePLN) -> int:
        """
        Saves a new entity to the JSON database file.

        Args:
        - entity (ConvertedPricePLN): An instance of ConvertedPricePLN to save
          in the database.

        Returns:
        - int: The ID of the saved entity.
        """
        if not isinstance(entity, ConvertedPricePLN):
            raise TypeError("Entity must be of type ConvertedPricePLN.")

        entity = {
            "currency": entity.currency,
            "rate": entity.currency_rate,
            "price_in_pln": entity.price_in_pln,
            "date": entity.currency_rate_fetch_date,
        }

        # Check if currency with given data is already in the database
        for key, value in self._data.items():
            if entity.items() <= value.items():
                logger.debug(
                    "A currency '%s' with given data already exists in the database.",
                    entity["currency"],
                )
                return key

        # Add a new record to the database
        new_id = str(max(map(int, self._data.keys()), default=0) + 1)
        ordered_entity = OrderedDict([("id", int(new_id))] + list(entity.items()))

        self._data[new_id] = dict(ordered_entity)
        self._write_data()

        return new_id

    def get_all(self) -> list[dict]:
        """
        Retrieves all entities from the JSON file database.

        Returns:
        - list[dict[str, Any]]: A list of all entities in the database.
        """
        return list(self._data.values())

    def get_by_id(self, entity_id: int) -> dict | None:
        """
        Retrieves an entity by its ID.

        Args:
        - entity_id (int): The ID of the entity to retrieve.

        Returns:
        - [dict[str, Any] | None]: The entity with the specified ID,
          or None if it does not exist.
        """
        return self._data.get(str(entity_id), None)

    def update(
        self,
        entity_id: int,
        currency: str | None = None,
        rate: float | None = None,
        price_in_pln: float | None = None,
        date: str | None = None,
    ) -> str:
        """
        Updates the entity with the given id in the JSON database.

        Args:
        - entity_id (int): The ID of the entity to update.
        - currency (Optional[str]): The new currency code, if updating.
        - rate (Optional[float]): The new exchange rate, if updating.
        - price_in_pln (Optional[float]): The new price in PLN, if updating.
        - date (Optional[str]): The new date, if updating.

        Returns:
        - str: A message indicating the result of the update operation.
        """
        entity = self._data.get(str(entity_id), None)
        if not entity:
            return f"No currency with id '{entity_id}' in the database."
        logger.debug("Database record to update: %s" % entity)

        validate_currency_input_data(currency, date, rate, price_in_pln)

        updated_entity = {
            "id": entity_id,
            "currency": currency or entity["currency"],
            "rate": rate or entity["rate"],
            "price_in_pln": price_in_pln or entity["price_in_pln"],
            "date": date or entity["date"],
        }

        self._data[str(entity_id)] = updated_entity
        self._write_data()
        logger.debug("Database record after update: %s" % self._data[str(entity_id)])

        return f"Currency with id '{entity_id}' was successfully updated."

    def delete(self, entity_id: int) -> str:
        """
        Deletes a specific currency data record by its ID.

        Args:
        - entity_id (int): The ID of the currency data record to delete.

        Returns:
        - str: A message indicating the result of the deletion operation.
        """
        try:
            del self._data[str(entity_id)]
            self._write_data()
            return f"Currency with id '{entity_id}' deleted from the database."
        except KeyError:
            return f"No currency with id '{entity_id}' to delete from the database."
        except Exception as e:
            logger.error("Error while deleting data from the database: %s", e)
            raise
