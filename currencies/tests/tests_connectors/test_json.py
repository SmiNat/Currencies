from unittest.mock import patch

import pytest

from currencies.connectors.database.json import JsonFileDatabaseConnector
from currencies.currency_converter import ConvertedPricePLN
from currencies.exceptions import CurrencyNotFoundError


def test_init(json_db):
    with patch.object(
        JsonFileDatabaseConnector,
        "_read_data",
        return_value=json_db,
    ):
        connector = JsonFileDatabaseConnector()
        assert isinstance(connector, JsonFileDatabaseConnector)


def test_read_data(json_db: dict, json_db_content: dict):
    with patch.object(
        JsonFileDatabaseConnector,
        "_read_data",
        return_value=json_db,
    ):
        connector = JsonFileDatabaseConnector()
        assert connector._read_data() == json_db_content


def test_read_data_file_not_found():
    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError) as exc_value:
            connector = JsonFileDatabaseConnector()
    assert "Unable to locate file" in str(exc_value)


def test_get_all(json_db: dict, json_db_content: dict):
    with patch.object(
        JsonFileDatabaseConnector,
        "_read_data",
        return_value=json_db,
    ):
        connector = JsonFileDatabaseConnector()
        assert connector.get_all() == list(json_db_content.values())


def test_get_all_empty_db(json_db: dict, json_db_content: dict):
    with patch.object(
        JsonFileDatabaseConnector,
        "_read_data",
        return_value={},
    ):
        connector = JsonFileDatabaseConnector()
        assert connector.get_all() == []


def test_get_by_id(json_db: dict, json_db_content: dict):
    with patch.object(
        JsonFileDatabaseConnector,
        "_read_data",
        return_value=json_db,
    ):
        connector = JsonFileDatabaseConnector()
        id = 1
        exp_response = json_db_content[str(id)]
        assert connector.get_by_id(id) == exp_response


def test_get_by_id_when_id_not_in_db(json_db: dict, json_db_content: dict):
    with patch.object(
        JsonFileDatabaseConnector,
        "_read_data",
        return_value=json_db,
    ):
        connector = JsonFileDatabaseConnector()
        id = 11
        exp_response = None
        assert connector.get_by_id(id) == exp_response


def test_get_by_id_invalid_id(json_db: dict, json_db_content: dict):
    with patch.object(
        JsonFileDatabaseConnector,
        "_read_data",
        return_value=json_db,
    ):
        connector = JsonFileDatabaseConnector()
        id = "invalid"
        exp_response = None
        assert connector.get_by_id(id) == exp_response


def test_save_new_entity(json_db: dict, json_db_path: str):
    with patch("currencies.connectors.database.json.JSON_DATABASE", json_db_path):
        connector = JsonFileDatabaseConnector()
        new_entity = ConvertedPricePLN(10, "USD", 4.2, "2024-06-30", 42)
        existing_ids = list(json_db.keys())
        assert existing_ids == list(connector._read_data().keys())
        assert len(connector._read_data()) == 2

        new_id = connector.save(new_entity)
        assert isinstance(new_id, str)
        assert isinstance(int(new_id), int)
        assert new_id not in existing_ids
        assert len(connector._read_data()) == 3

        saved_entity = connector.get_by_id(new_id)
        assert saved_entity is not None
        assert saved_entity["currency"] == "USD"
        assert saved_entity["currency_rate"] == 4.2
        assert saved_entity["price_in_pln"] == 42.0
        assert saved_entity["currency_date"] == "2024-06-30"


def test_save_new_entity_invalid_data_type(json_db: dict, json_db_path: str):
    with patch("currencies.connectors.database.json.JSON_DATABASE", json_db_path):
        connector = JsonFileDatabaseConnector()
        entity = {
            "price_in_currency": 10,
            "currency": "USD",
            "currency_rate": 4.2,
            "currency_date": "2024-06-30",
            "price_in_pln": 42,
        }
        with pytest.raises(TypeError) as exc_info:
            connector.save(entity)
        assert "Entity must be of type ConvertedPricePLN" in str(exc_info.value)


def test_save_new_entity_already_in_db(json_db: dict, json_db_path: str):
    with patch("currencies.connectors.database.json.JSON_DATABASE", json_db_path):
        connector = JsonFileDatabaseConnector()
        existing_ids = list(json_db.keys())
        assert existing_ids == list(connector._read_data().keys())

        existing_data = json_db["3"]  # existing id
        assert "3" in list(json_db.keys())
        assert "3" in list(connector._read_data().keys())
        assert len(json_db) == 2

        entity = ConvertedPricePLN(
            5,
            existing_data["currency"],
            existing_data["currency_rate"],
            existing_data["currency_date"],
            existing_data["price_in_pln"],
        )

        new_id = connector.save(entity)
        assert new_id in existing_ids
        assert new_id == "3"
        assert len(json_db) == 2


def test_update_entity(json_db: dict, json_db_path: str):
    with patch("currencies.connectors.database.json.JSON_DATABASE", json_db_path):
        connector = JsonFileDatabaseConnector()
        entity_id = 1
        new_rate = 4.8

        assert connector.get_by_id(entity_id) is not None
        assert connector.get_by_id(entity_id)["currency_rate"] != new_rate
        original_data = connector.get_by_id(entity_id)

        result = connector.update(entity_id, currency_rate=new_rate)

        data = original_data.copy()
        data["currency_rate"] = new_rate
        exp_result = data

        updated_entity = connector.get_by_id(entity_id)
        assert "successfully updated" in result
        assert updated_entity is not None
        assert updated_entity["currency_rate"] == new_rate
        assert updated_entity == exp_result


def test_update_entity_with_invalid_id(json_db: dict, json_db_path: str):
    with patch("currencies.connectors.database.json.JSON_DATABASE", json_db_path):
        connector = JsonFileDatabaseConnector()
        entity_id = 999  # non existing id
        new_rate = 4.8

        exp_result = f"No currency with id '{entity_id}' in the database"
        result = connector.update(entity_id, currency_rate=new_rate)
        assert exp_result in result


@pytest.mark.parametrize(
    "currency, rate, price_in_pln, date, error, message",
    [
        (
            "invalid",
            3.50,
            17.50,
            "2020-10-10",
            CurrencyNotFoundError,
            "Invalid currency code. Available currencies",
        ),
        (
            "chf",
            "3.50",
            17.50,
            "2020-10-10",
            TypeError,
            "Invalid data type for rate attribute. Required type: float",
        ),
        (
            "chf",
            3.50,
            "17",
            "2020-10-10",
            TypeError,
            "Invalid data type for price attribute. Required type: float or integer",
        ),
        (
            "chf",
            3.50,
            17.50,
            "2020,10,10",
            ValueError,
            "Invalid date format. Required format: 'YYYY-MM-DD'",
        ),
    ],
)
def test_update_entity_with_invalid_datato_update(
    json_db: dict,
    json_db_path: str,
    currency: str,
    rate: float,
    price_in_pln: float | int,
    date: str,
    error: Exception,
    message: str,
):
    with patch("currencies.connectors.database.json.JSON_DATABASE", json_db_path):
        connector = JsonFileDatabaseConnector()
        entity_id = 1  # existing id

        exp_result = message
        with pytest.raises(error) as exc_info:
            connector.update(
                entity_id,
                currency=currency,
                currency_rate=rate,
                price_in_pln=price_in_pln,
                currency_date=date,
            )
        assert exp_result in str(exc_info.value)


def test_delete_entity(json_db: dict, json_db_path: str):
    with patch("currencies.connectors.database.json.JSON_DATABASE", json_db_path):
        connector = JsonFileDatabaseConnector()
        entity_id = 1
        assert connector.get_by_id(entity_id) is not None

        result = connector.delete(entity_id)

        assert f"Currency with id '{entity_id}' deleted from the database" in result
        assert connector.get_by_id(entity_id) is None


def test_delete_entity_with_non_existing_record(json_db: dict, json_db_path: str):
    with patch("currencies.connectors.database.json.JSON_DATABASE", json_db_path):
        connector = JsonFileDatabaseConnector()
        entity_id = 999  # non existing id
        assert connector.get_by_id(entity_id) is None

        result = connector.delete(entity_id)

        assert (
            f"No currency with id '{entity_id}' to delete from the database" in result
        )


def test_delete_entity_raises_exception(caplog, json_db, json_db_path: str):
    with patch("currencies.connectors.database.json.JSON_DATABASE", json_db_path):
        connector = JsonFileDatabaseConnector()
        entity_id = connector.save(ConvertedPricePLN(10, "USD", 4.2, "2024-06-30", 42))

        # Simulate an exception during the write operation
        with patch.object(
            JsonFileDatabaseConnector,
            "_write_data",
            side_effect=Exception("Simulated write error"),
        ):
            with pytest.raises(Exception, match="Simulated write error"):
                connector.delete(entity_id)

            # Check that the error message was logged
            assert any(
                "Error while deleting data from the database" in log.message
                for log in caplog.records
            )
