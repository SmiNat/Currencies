import json
from collections import OrderedDict

from ...config import DEV_DATABASE_NAME
from ...currency_converter import ConvertedPricePLN


class JsonFileDatabaseConnector:
    def __init__(self) -> None:
        self._data = self._read_data()

    @staticmethod
    def _read_data() -> dict:
        try:
            with open(DEV_DATABASE_NAME, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def save(self, entity: dict | ConvertedPricePLN) -> int:
        new_id = str(max(map(int, self._data.keys()), default=0) + 1)

        if isinstance(entity, ConvertedPricePLN):
            ordered_entity = OrderedDict(
                [
                    ("id", int(new_id)),
                    ("currency", entity.currency),
                    ("rate", entity.currency_rate),
                    ("price_in_pln", entity.price_in_pln),
                    ("date", entity.currency_rate_fetch_date),
                ]
            )
        elif isinstance(entity, dict):
            ordered_entity = OrderedDict(
                [
                    ("id", int(new_id)),
                    ("currency", entity["currency"]),
                    ("rate", entity["rate"]),
                    ("price_in_pln", entity["price_in_pln"]),
                    ("date", entity["date"]),
                ]
            )

        self._data[new_id] = ordered_entity

        with open(DEV_DATABASE_NAME, "w") as file:
            json.dump(self._data, file, indent=4)
        return new_id

    def get_all(self) -> list[dict]:
        return list(self._data.values())

    def get_by_id(self, entity_id: int) -> dict | None:
        return self._data.get(str(entity_id), None)
