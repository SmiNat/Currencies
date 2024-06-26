import json
from unittest.mock import patch

import pytest

from currencies.connectors.database.json import JsonFileDatabaseConnector
from currencies.currency_converter import ConvertedPricePLN
from currencies.exceptions import CurrencyNotFoundError


def test_init():
    connector = JsonFileDatabaseConnector()
    assert isinstance(connector, JsonFileDatabaseConnector)


def test_read_values(test_json_db: dict, test_db_content: dict):
    with patch.object(
        JsonFileDatabaseConnector,
        "_read_data",
        return_value=test_json_db,
    ):
        connector = JsonFileDatabaseConnector()
        assert connector._read_data() == test_db_content


def test_read_data_file_not_found(caplog):
    with patch("os.path.exists", return_value=False):
        connector = JsonFileDatabaseConnector()
        assert connector.get_all() == []
        assert any(
            "FileNotFoundError: unable to locate file" in log.message
            for log in caplog.records
        )


def test_read_data_json_decode_error(caplog, test_json_db):
    with patch("json.load", side_effect=json.JSONDecodeError("error message", "", 0)):
        connector = JsonFileDatabaseConnector()
        assert connector.get_all() == []
        assert any("Error reading data:" in log.message for log in caplog.records)


def test_write_data_io_error(caplog, test_db_path: str):
    with patch("currencies.connectors.database.json.Config.DATABASE_URL", test_db_path):
        with patch("json.dump", side_effect=IOError("IO error")):
            connector = JsonFileDatabaseConnector()
            # entity = ConvertedPricePLN(10, "USD", 4.2, "2024-06-30", 42)
            with pytest.raises(IOError):
                connector._write_data()
            assert any("Error writing data to" in log.message for log in caplog.records)
            assert any("IO error" in log.message for log in caplog.records)


def test_get_all(test_json_db: dict, test_db_content: dict):
    with patch.object(
        JsonFileDatabaseConnector,
        "_read_data",
        return_value=test_json_db,
    ):
        connector = JsonFileDatabaseConnector()
        assert connector.get_all() == list(test_db_content.values())


def test_get_all_empty_db(test_json_db: dict, test_db_content: dict):
    with patch.object(
        JsonFileDatabaseConnector,
        "_read_data",
        return_value={},
    ):
        connector = JsonFileDatabaseConnector()
        assert connector.get_all() == []


def test_get_by_id(test_json_db: dict, test_db_content: dict):
    with patch.object(
        JsonFileDatabaseConnector,
        "_read_data",
        return_value=test_json_db,
    ):
        connector = JsonFileDatabaseConnector()
        id = 1
        exp_response = test_db_content[str(id)]
        assert connector.get_by_id(id) == exp_response


def test_get_by_id_when_id_not_in_db(test_json_db: dict, test_db_content: dict):
    with patch.object(
        JsonFileDatabaseConnector,
        "_read_data",
        return_value=test_json_db,
    ):
        connector = JsonFileDatabaseConnector()
        id = 11
        exp_response = None
        assert connector.get_by_id(id) == exp_response


def test_get_by_id_invalid_id(test_json_db: dict, test_db_content: dict):
    with patch.object(
        JsonFileDatabaseConnector,
        "_read_data",
        return_value=test_json_db,
    ):
        connector = JsonFileDatabaseConnector()
        id = "invalid"
        exp_response = None
        assert connector.get_by_id(id) == exp_response


def test_save_new_entity(test_json_db: dict, test_db_path: str):
    with patch("currencies.connectors.database.json.Config.DATABASE_URL", test_db_path):
        connector = JsonFileDatabaseConnector()
        entity = ConvertedPricePLN(10, "USD", 4.2, "2024-06-30", 42)
        existing_ids = list(test_json_db.keys())

        new_id = connector.save(entity)
        assert isinstance(new_id, str)
        assert isinstance(int(new_id), int)
        assert new_id not in existing_ids

        saved_entity = connector.get_by_id(new_id)
        assert saved_entity is not None
        assert saved_entity["currency"] == "USD"
        assert saved_entity["rate"] == 4.2
        assert saved_entity["price_in_pln"] == 42.0
        assert saved_entity["date"] == "2024-06-30"


def test_save_new_entity_invalid_data_type(test_json_db: dict, test_db_path: str):
    with patch("currencies.connectors.database.json.Config.DATABASE_URL", test_db_path):
        connector = JsonFileDatabaseConnector()
        entity = {
            "price_in_currency": 10,
            "currency": "USD",
            "rate": 4.2,
            "date": "2024-06-30",
            "price_in_pln": 42,
        }
        with pytest.raises(TypeError) as exc_info:
            connector.save(entity)
        assert "Entity must be of type ConvertedPricePLN" in str(exc_info.value)


def test_save_new_entity_already_in_db(test_json_db: dict, test_db_path: str, caplog):
    with patch("currencies.connectors.database.json.Config.DATABASE_URL", test_db_path):
        connector = JsonFileDatabaseConnector()
        existing_ids = list(test_json_db.keys())
        existing_data = test_json_db["3"]  # existing id

        entity = ConvertedPricePLN(
            5,
            existing_data["currency"],
            existing_data["rate"],
            existing_data["date"],
            existing_data["price_in_pln"],
        )

        new_id = connector.save(entity)
        assert new_id in existing_ids
        assert new_id == "3"
        assert any(
            "A currency 'eur' with given data already exists in the database"
            in log.message
            for log in caplog.records
        )


def test_update_entity(test_json_db: dict, test_db_path: str):
    with patch("currencies.connectors.database.json.Config.DATABASE_URL", test_db_path):
        connector = JsonFileDatabaseConnector()
        entity_id = 1
        new_rate = 4.8

        assert connector.get_by_id(entity_id) is not None
        assert connector.get_by_id(entity_id)["rate"] != new_rate
        original_data = connector.get_by_id(entity_id)

        result = connector.update(entity_id, rate=new_rate)

        data = original_data.copy()
        data["rate"] = new_rate
        exp_result = data

        updated_entity = connector.get_by_id(entity_id)
        assert "successfully updated" in result
        assert updated_entity is not None
        assert updated_entity["rate"] == new_rate
        assert updated_entity == exp_result


def test_update_entity_with_invalid_id(test_json_db: dict, test_db_path: str):
    with patch("currencies.connectors.database.json.Config.DATABASE_URL", test_db_path):
        connector = JsonFileDatabaseConnector()
        entity_id = 999  # non existing id
        new_rate = 4.8

        exp_result = f"No currency with id '{entity_id}' in the database"
        result = connector.update(entity_id, rate=new_rate)
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
    test_json_db: dict,
    test_db_path: str,
    currency: str,
    rate: float,
    price_in_pln: float | int,
    date: str,
    error: Exception,
    message: str,
):
    with patch("currencies.connectors.database.json.Config.DATABASE_URL", test_db_path):
        connector = JsonFileDatabaseConnector()
        entity_id = 1  # existing id

        exp_result = message
        with pytest.raises(error) as exc_info:
            connector.update(
                entity_id,
                currency=currency,
                rate=rate,
                price_in_pln=price_in_pln,
                date=date,
            )
        assert exp_result in str(exc_info.value)


def test_delete_entity(test_json_db: dict, test_db_path: str):
    with patch("currencies.connectors.database.json.Config.DATABASE_URL", test_db_path):
        connector = JsonFileDatabaseConnector()
        entity_id = 1
        assert connector.get_by_id(entity_id) is not None

        result = connector.delete(entity_id)

        assert f"Currency with id '{entity_id}' deleted from the database" in result
        assert connector.get_by_id(entity_id) is None


def test_delete_entity_with_non_existing_record(test_json_db: dict, test_db_path: str):
    with patch("currencies.connectors.database.json.Config.DATABASE_URL", test_db_path):
        connector = JsonFileDatabaseConnector()
        entity_id = 999  # non existing id
        assert connector.get_by_id(entity_id) is None

        result = connector.delete(entity_id)

        assert (
            f"No currency with id '{entity_id}' to delete from the database" in result
        )


def test_delete_entity_raises_exception(caplog, test_db_path: str):
    with patch("currencies.connectors.database.json.Config.DATABASE_URL", test_db_path):
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
