import json
import logging
import os
from collections import OrderedDict

from ...config import DEV_DATABASE_NAME
from ...currency_converter import ConvertedPricePLN

logger = logging.getLogger(__name__)


class JsonFileDatabaseConnector:
    """
    A connector class to retrieve and update data from a JSON file database.

    Attributes:
        _data (dict): The in-memory representation of the database.
    """

    def __init__(self) -> None:
        """
        Initializes the connector by reading data from the JSON file at the specified URL.
        """
        self._data = self._read_data()

    @staticmethod
    def _read_data() -> dict:
        """
        Reads data from the JSON file.

        Returns:
            dict[str, Any]: The data read from the JSON file. Returns an empty
            dictionary if the file does not exist or an error occurs.
        """
        if not os.path.exists(DEV_DATABASE_NAME):
            logger.error(
                "FileNotFoundError: unable to locate file: %s", {DEV_DATABASE_NAME}
            )
            return {}
        try:
            with open(DEV_DATABASE_NAME, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Error reading data: %s", {e})
            return {}

    def _write_data(self) -> None:
        """
        Writes the current state of the in-memory database (_data) to the JSON file.

        Raises:
            IOError: If an error occurs while writing data to the JSON file
        """
        try:
            with open(DEV_DATABASE_NAME, "w") as file:
                json.dump(self._data, file, indent=4)
        except IOError as e:
            logger.error("Error writing data to %s: %s", DEV_DATABASE_NAME, e)
            raise

    def save(self, entity: dict | ConvertedPricePLN) -> int:
        """
        Saves a new entity to the JSON file database.

        Args:
            entity (dict[str, Any] | ConvertedPricePLN): The entity to save.
            Can be a dictionary or an instance of ConvertedPricePLN.

        Returns:
            int: The ID of the saved entity.

        Raises:
            ValueError: If the entity dictionary does not contain the required keys.
            TypeError: If the entity is neither a dictionary nor an instance of ConvertedPricePLN.
            IOError: If an error occurs while writing data to the JSON file.
        """
        new_id = str(max(map(int, self._data.keys()), default=0) + 1)

        if isinstance(entity, ConvertedPricePLN):
            entity = {
                "currency": entity.currency,
                "rate": entity.currency_rate,
                "price_in_pln": entity.price_in_pln,
                "date": entity.currency_rate_fetch_date,
            }
        elif isinstance(entity, dict):
            required_keys = {"currency", "rate", "price_in_pln", "date"}
            if not required_keys.issubset(entity):
                raise ValueError(
                    f"Entity dictionary must contain keys: {required_keys}"
                )
        else:
            raise TypeError("Entity must be a dict or ConvertedPricePLN instance")

        ordered_entity = OrderedDict([("id", int(new_id))] + list(entity.items()))

        self._data[new_id] = dict(ordered_entity)
        self._write_data()

        return new_id

    def get_all(self) -> list[dict]:
        """
        Retrieves all entities from the JSON file database.

        Returns:
            list[dict[str, Any]]: A list of all entities in the database.
        """
        return list(self._data.values())

    def get_by_id(self, entity_id: int) -> dict | None:
        """
        Retrieves an entity by its ID.

        Args:
            entity_id (int): The ID of the entity to retrieve.

        Returns:
            [dict[str, Any] | None]: The entity with the specified ID,
            or None if it does not exist.
        """
        return self._data.get(str(entity_id), None)
