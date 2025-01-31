import copy
import datetime
import logging
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from currencies.connectors.database.sqlite import SQLiteDatabaseConnector
from currencies.currency_converter import ConvertedPricePLN
from currencies.database_config import CurrencyData
from currencies.exceptions import CurrencyNotFoundError
from currencies.tests.conftest import SQLITE_DB_INITIAL_DATA

logger = logging.getLogger("currencies")


def test_if_testing_db_is_empty(db_session: Session):
    records = db_session.query(CurrencyData).count()
    assert records == 0


def test_if_testing_db_has_initial_data(
    db_session: Session, sqlite_db_initial_data: tuple[CurrencyData, CurrencyData]
):
    # Check initial state of the database
    records = db_session.query(CurrencyData).count()
    assert records == 2

    amounts = db_session.query(CurrencyData.amount).distinct().all()
    unique_amounts = [amount[0] for amount in amounts]
    expected_amounts = [
        SQLITE_DB_INITIAL_DATA[0]["amount"],
        SQLITE_DB_INITIAL_DATA[1]["amount"],
    ]
    assert sorted(unique_amounts) == sorted(expected_amounts)


def test_init(db_session: Session):
    session = SQLiteDatabaseConnector()
    assert isinstance(session, SQLiteDatabaseConnector)


def test_get_all(
    db_session: Session, sqlite_db_initial_data: tuple[CurrencyData, CurrencyData]
):
    with patch(
        "currencies.connectors.database.sqlite.get_db", side_effect=lambda: db_session
    ):
        session = SQLiteDatabaseConnector()

        db_records = copy.deepcopy(SQLITE_DB_INITIAL_DATA)
        for record in db_records:
            del record["time_created"]
            del record["time_updated"]

        exp_result = db_records

        result = session.get_all()
        assert result == exp_result


def test_get_all_empty_db(db_session: Session):
    with patch(
        "currencies.connectors.database.sqlite.get_db", side_effect=lambda: db_session
    ):
        session = SQLiteDatabaseConnector()

        exp_result = []

        result = session.get_all()
        assert result == exp_result


def test_get_all_logs_error(db_session: Session, caplog):
    with patch(
        "currencies.connectors.database.sqlite.get_db", side_effect=lambda: db_session
    ):
        session = SQLiteDatabaseConnector()

        # Mock the session query to raise an exception
        original_query = session.session.query
        session.session.query = MagicMock(side_effect=Exception("Test exception"))

        with caplog.at_level(logging.DEBUG):
            with pytest.raises(Exception, match="Test exception"):
                session.get_all()

        # Restore the original query method
        session.session.query = original_query

        logger.debug("Captured logs: %s" % caplog.messages)

        # Check that the error was logged
        assert any(
            "Error while retrieving data from the database" in message
            for message in caplog.messages
        ), "Expected log message not found in captured logs"


def test_get_by_id(
    db_session: Session, sqlite_db_initial_data: tuple[CurrencyData, CurrencyData]
):
    with patch(
        "currencies.connectors.database.sqlite.get_db", side_effect=lambda: db_session
    ):
        session = SQLiteDatabaseConnector()
        id = 1

        exp_result = SQLITE_DB_INITIAL_DATA[0]

        result = session.get_by_id(id)
        assert result == exp_result


def test_get_by_id_non_existing_record(
    db_session: Session, sqlite_db_initial_data: tuple[CurrencyData, CurrencyData]
):
    with patch(
        "currencies.connectors.database.sqlite.get_db", side_effect=lambda: db_session
    ):
        session = SQLiteDatabaseConnector()
        non_existing_id = 999

        exp_result = None

        result = session.get_by_id(non_existing_id)
        assert result == exp_result


def test_get_by_id_with_invalid_id(db_session: Session, sqlite_db_initial_data):
    with patch(
        "currencies.connectors.database.sqlite.get_db", side_effect=lambda: db_session
    ):
        session = SQLiteDatabaseConnector()
        non_existing_id = "invalid"

        exp_result = None

        result = session.get_by_id(non_existing_id)
        assert result == exp_result


def test_get_by_id_logs_error(db_session: Session, caplog):
    with patch(
        "currencies.connectors.database.sqlite.get_db", side_effect=lambda: db_session
    ):
        session = SQLiteDatabaseConnector()

        # Mock the session query to raise an exception
        original_query = session.session.query
        session.session.query = MagicMock(side_effect=Exception("Test exception"))

        with caplog.at_level(logging.ERROR):
            with pytest.raises(Exception, match="Test exception"):
                session.get_by_id(1)

        # Restore the original query method
        session.session.query = original_query

        logger.debug("Captured logs: %s" % caplog.messages)

        # Check that the error was logged
        assert any(
            "Error while retrieving data from the database" in message
            for message in caplog.messages
        ), "Expected log message not found in captured logs"


def test_save(db_session: Session):
    with patch(
        "currencies.connectors.database.sqlite.get_db", side_effect=lambda: db_session
    ):
        session = SQLiteDatabaseConnector()
        entity = ConvertedPricePLN(10, "CHF", 5.2, "2022-11-22", 52)
        db_record = (
            db_session.query(CurrencyData)
            .filter(CurrencyData.currency == "CHF")
            .first()
        )
        assert db_record is None
        assert db_session.query(CurrencyData).count() == 0

        exp_result = 1

        result = session.save(entity)
        assert result == exp_result

        db_record = (
            db_session.query(CurrencyData)
            .filter(CurrencyData.currency == "CHF")
            .first()
        )
        assert db_record is not None
        assert db_session.query(CurrencyData).count() == 1


def test_save_invalid_data_type(db_session: Session):
    with patch(
        "currencies.connectors.database.sqlite.get_db", side_effect=lambda: db_session
    ):
        session = SQLiteDatabaseConnector()
        entity = {
            "currency": "CHF",
            "currency_rate": 5.2,
            "currency_date": "2022-11-22",
            "price_in_pln": 52,
        }
        exp_response = "Entity must be a ConvertedPricePLN instance"
        with pytest.raises(TypeError) as exc_info:
            session.save(entity)
        assert exp_response in str(exc_info)


def test_save_if_data_already_in_db(
    db_session: Session, sqlite_db_initial_data: tuple[CurrencyData, CurrencyData]
):
    with patch(
        "currencies.connectors.database.sqlite.get_db", side_effect=lambda: db_session
    ):
        session = SQLiteDatabaseConnector()
        entity = ConvertedPricePLN(10, "GBP", 5.1234, "2024-06-01", 51.234)

        # Check if record with the same data exists in the database
        db_record = (
            db_session.query(CurrencyData)
            .filter_by(
                currency=entity.currency,
                currency_rate=entity.currency_rate,
                currency_date=entity.currency_date,
                price_in_pln=entity.price_in_pln,
            )
            .first()
        )
        assert db_record is not None
        assert db_session.query(CurrencyData).count() == 2

        id = db_record.id

        # Check save method response
        exp_response = id
        response = session.save(entity)
        assert exp_response == response
        assert db_session.query(CurrencyData).count() == 2


def test_update(
    db_session: Session, sqlite_db_initial_data: tuple[CurrencyData, CurrencyData]
):
    with patch(
        "currencies.connectors.database.sqlite.get_db", side_effect=lambda: db_session
    ):
        session = SQLiteDatabaseConnector()

        record_id = 1
        db_record = db_session.query(CurrencyData).filter_by(id=record_id).first()
        assert db_record is not None
        assert db_record.currency == sqlite_db_initial_data[0].currency == "GBP"

        new_currency = "CHF"
        assert db_record.currency != new_currency
        exp_response = f"Currency with id '{record_id}' was successfully updated."

        response = session.update(entity_id=record_id, currency=new_currency)
        assert exp_response in str(response)
        db_record = db_session.query(CurrencyData).filter_by(id=record_id).first()
        assert db_record.currency == new_currency


def test_update_if_no_record_in_db(db_session: Session):
    with patch(
        "currencies.connectors.database.sqlite.get_db", side_effect=lambda: db_session
    ):
        session = SQLiteDatabaseConnector()
        record_id = 1
        db_record = db_session.query(CurrencyData).filter_by(id=record_id).first()
        assert db_record is None

        new_currency = "CHF"
        exp_response = f"No currency with id '{record_id}' in the database."

        response = session.update(entity_id=record_id, currency=new_currency)
        assert exp_response in str(response)


@pytest.mark.parametrize(
    "invalid_data, error, message",
    [
        ({"currency": "invalid"}, CurrencyNotFoundError, "Invalid currency code"),
        (
            {"currency_date": datetime.date(2020, 10, 11)},
            TypeError,
            "Invalid data type for date attribute. Required type: string",
        ),
        (
            {"currency_date": "11-11-2020"},
            ValueError,
            "Invalid date format. Required format: 'YYYY-MM-DD'",
        ),
        (
            {"currency_rate": "4.55"},
            TypeError,
            "Invalid data type for rate attribute. Required type: float",
        ),
    ],
)
def test_update_invalid_data(
    db_session: Session,
    sqlite_db_initial_data: tuple[CurrencyData, CurrencyData],
    invalid_data: dict,
    error: Exception,
    message: str,
):
    with patch(
        "currencies.connectors.database.sqlite.get_db", side_effect=lambda: db_session
    ):
        session = SQLiteDatabaseConnector()
        record_id = 1
        db_record = db_session.query(CurrencyData).filter_by(id=record_id).first()
        assert db_record is not None

        with pytest.raises(error) as exc_info:
            session.update(entity_id=record_id, **invalid_data)
        assert message in str(exc_info)


def test_delete(
    db_session: Session, sqlite_db_initial_data: tuple[CurrencyData, CurrencyData]
):
    with patch(
        "currencies.connectors.database.sqlite.get_db", side_effect=lambda: db_session
    ):
        session = SQLiteDatabaseConnector()
        record_id = 1
        db_record = db_session.query(CurrencyData).filter_by(id=record_id).first()
        assert db_record is not None

        exp_response = f"Currency with id '{record_id}' deleted from the database."
        response = session.delete(record_id)
        assert exp_response in response
        db_record = db_session.query(CurrencyData).filter_by(id=record_id).first()
        assert db_record is None


def test_delete_no_record_in_db(
    db_session: Session, sqlite_db_initial_data: tuple[CurrencyData, CurrencyData]
):
    with patch(
        "currencies.connectors.database.sqlite.get_db", side_effect=lambda: db_session
    ):
        session = SQLiteDatabaseConnector()
        record_id = 999  # no existing record id
        db_record = db_session.query(CurrencyData).filter_by(id=record_id).first()
        assert db_record is None

        exp_response = f"No currency with id '{record_id}' to delete from the database."
        response = session.delete(record_id)
        assert exp_response in response


def test_delete_currency_with_exception(
    db_session: Session,
    sqlite_db_initial_data: tuple[CurrencyData, CurrencyData],
    caplog,
):
    with patch(
        "currencies.connectors.database.sqlite.get_db", side_effect=lambda: db_session
    ):
        session = SQLiteDatabaseConnector()
        record_id = 1
        db_record = db_session.query(CurrencyData).filter_by(id=record_id).first()
        assert db_record is not None

        with pytest.raises(SQLAlchemyError):
            with patch.object(
                db_session, "query", side_effect=SQLAlchemyError("Simulated error")
            ):
                session.delete(record_id)

        assert any(
            "Error while deleting data from the database" in record.message
            for record in caplog.records
        )
