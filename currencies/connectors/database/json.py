import json
import logging
import os
from collections import OrderedDict

from ...utils import ConvertedPricePLN, validate_currency_input_data

logger = logging.getLogger("currencies")


JSON_DATABASE = os.environ.get("JSON_DATABASE")


def get_local_db():
    return JSON_DATABASE


class JsonFileDatabaseConnector:
    """A connector class to retrieve and update data from a JSON database file."""

    def __init__(self) -> None:
        self._data = self._read_data()

    @staticmethod
    def _read_data() -> dict:
        """Reads data from the JSON file."""
        if not os.path.exists(get_local_db()):
            raise FileNotFoundError("Unable to locate file: %s" % get_local_db())
        try:
            with open(get_local_db(), "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Error reading data: %s", {e})
            return {}

    def _write_data(self) -> None:
        """Writes the current state of the in-memory database (_data) to the JSON file."""
        if not os.path.exists(get_local_db()):
            raise FileNotFoundError("Unable to locate file: %s" % get_local_db())
        try:
            with open(get_local_db(), "w") as file:
                json.dump(self._data, file, indent=4)
        except IOError as e:
            logger.error("Error writing data to %s: %s", get_local_db(), e)
            raise

    def save(self, entity: ConvertedPricePLN) -> int:
        """Saves a new entity to the JSON database file."""
        if not isinstance(entity, ConvertedPricePLN):
            raise TypeError("Entity must be of type ConvertedPricePLN.")

        entity = {
            "amount": entity.amount,
            "currency": entity.currency,
            "currency_rate": entity.currency_rate,
            "currency_date": entity.currency_date,
            "price_in_pln": entity.price_in_pln,
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
        """Retrieves all entities from the JSON file database."""
        return list(self._data.values())

    def get_by_id(self, entity_id: int) -> dict | None:
        """Retrieves an entity by its ID."""
        return self._data.get(str(entity_id), None)

    def update(
        self,
        entity_id: int,
        amount: float | int | None = None,
        currency: str | None = None,
        currency_rate: float | None = None,
        currency_date: str | None = None,
        price_in_pln: float | None = None,
    ) -> str:
        """
        Updates the entity with the given id in the JSON database.

        Args:
        - entity_id (int): The ID of the entity to update.
        - amount (Optional[float | int]): The price in source currency.
        - currency (Optional[str]): The new currency code, if updating.
        - currency_rate (Optional[float]): The new exchange rate, if updating.
        - currency_date (Optional[str]): The new date, if updating.
        - price_in_pln (Optional[float]): The new price in PLN, if updating.
        """
        entity = self._data.get(str(entity_id), None)
        if not entity:
            return f"No currency with id '{entity_id}' in the database."
        logger.debug("Database record to update: %s" % entity)

        validate_currency_input_data(
            amount, currency, currency_date, currency_rate, price_in_pln
        )

        updated_entity = {
            "id": entity_id,
            "amount": amount or entity["amount"],
            "currency": currency or entity["currency"],
            "currency_rate": currency_rate or entity["currency_rate"],
            "currency_date": currency_date or entity["currency_date"],
            "price_in_pln": price_in_pln or entity["price_in_pln"],
        }

        self._data[str(entity_id)] = updated_entity
        self._write_data()
        logger.debug("Database record after update: %s" % self._data[str(entity_id)])

        return f"Currency with id '{entity_id}' was successfully updated."

    def delete(self, entity_id: int) -> str:
        """Deletes a specific currency data record by its ID."""
        try:
            del self._data[str(entity_id)]
            self._write_data()
            return f"Currency with id '{entity_id}' deleted from the database."
        except KeyError:
            return f"No currency with id '{entity_id}' to delete from the database."
        except Exception as e:
            logger.error("Error while deleting data from the database: %s", e)
            raise
