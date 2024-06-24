import json
import logging
import os
from collections import OrderedDict

from ...config import Config
from ...currency_converter import ConvertedPricePLN

logger = logging.getLogger(__name__)


class JsonFileDatabaseConnector:
    """
    A connector class to retrieve and update data from a JSON database file.

    Attributes:
    - _data (dict): The in-memory representation of the database.

    Methods:
    - _read_data: Reads data from the JSON file.
    - _write_data: Writes the current state of the in-memory database (_data)
      to the JSON file.
    - save: Saves a new entity to the JSON database file.
    - get_all: Retrieves all entities from the JSON database file.
    - get_by_id: Retrieves an entity by its ID.
    """

    def __init__(self) -> None:
        """
        Initializes the connector by reading data from the JSON file at the
        specified URL.
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
        if not os.path.exists(Config.DATABASE_URL):
            logger.error(
                "FileNotFoundError: unable to locate file: %s", {Config.DATABASE_URL}
            )
            return {}
        try:
            with open(Config.DATABASE_URL, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Error reading data: %s", {e})
            return {}

    def _write_data(self) -> None:
        """
        Writes the current state of the in-memory database (_data) to the JSON file.

        Raises:
        - IOError: If an error occurs while writing data to the JSON file.
        """
        try:
            with open(Config.DATABASE_URL, "w") as file:
                json.dump(self._data, file, indent=4)
        except IOError as e:
            logger.error("Error writing data to %s: %s", Config.DATABASE_URL, e)
            raise

    def save(self, entity: ConvertedPricePLN) -> int:
        """
        Saves a new entity to the JSON database file.

        Args:
        - entity (ConvertedPricePLN): An instance of ConvertedPricePLN to save
          in the database.

        Returns:
        - int: The ID of the saved entity.

        Raises:
        - TypeError: If the entity is not an instance of ConvertedPricePLN.
        - IOError: If an error occurs while writing data to the JSON file.
        - CurrencyDataIntegrityError: If the same record already exists in the database.
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
                return int(key)

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
