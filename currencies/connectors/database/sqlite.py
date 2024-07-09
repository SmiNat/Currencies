import datetime
import logging
import os
from contextlib import contextmanager

from sqlalchemy.orm import Session

from ...currency_converter import ConvertedPricePLN
from ...database_config import CurrencyData, SessionLocal
from ...utils import validate_currency_input_data

logger = logging.getLogger("currencies")

SQLITE_DATABASE_NAME = os.environ.get("SQLITE_DATABASE_NAME")


class SQLiteDatabaseConnector:
    """A connector class to interact with the SQLite database."""

    def __init__(self, session: Session | None = None) -> None:
        """
        Initializes the connector with the given session factory or the default
        SessionLocal().

        Attributes:
        - session (Session, optional): The session factory for creating database
          sessions. Defaults to SessionLocal() if not provided.
        """
        self.session = SessionLocal() if not session else session

    @contextmanager
    def _get_session(self) -> Session:  # type: ignore
        """
        Provides a context manager for database sessions.
        """
        session = self.session

        if not isinstance(session, Session):
            raise TypeError(
                "Invalid session initial attribute. Required type: Session."
            )

        try:
            yield session
        except Exception as e:
            logger.error("Error with accessing the database: %s", {e})
            # session.rollback()
            raise
        finally:
            session.close()

    def save(self, entity: ConvertedPricePLN) -> int:
        """
        Adds a new currency data record to the database.

        Args:
        - entity (ConvertedPricePLN): An instance of ConvertedPricePLN to add
          to the database.
        """
        if not isinstance(entity, ConvertedPricePLN):
            raise TypeError("Entity must be a ConvertedPricePLN instance.")

        with self._get_session() as session:
            # Check if currency with the same data as data of the entity is
            # already in the database
            existing_record = (
                session.query(CurrencyData)
                .filter_by(
                    currency=entity.currency,
                    rate=entity.currency_rate,
                    price_in_pln=entity.price_in_pln,
                    date=datetime.datetime.strptime(
                        entity.currency_rate_fetch_date, "%Y-%m-%d"
                    ).date(),
                )
                .first()
            )
            if existing_record:
                logger.debug(
                    "A currency '%s' with given data already exists in the database.",
                    entity.currency,
                )
                return existing_record.id

            # Add a new record to the database
            new_data = CurrencyData(
                amount=entity.amount,
                currency=entity.currency,
                rate=entity.currency_rate,
                date=datetime.datetime.strptime(
                    entity.currency_rate_fetch_date, "%Y-%m-%d"
                ).date(),
                price_in_pln=entity.price_in_pln,
            )
            try:
                session.add(new_data)
                session.commit()
                session.flush()  # Get the ID of the newly added record
                return new_data.id

            except Exception as e:
                logger.error("Error while saving data to the database: %s", {e})
                raise

    def get_all(self) -> list[dict]:
        """Retrieves all currency data records from the database."""
        with self._get_session() as session:
            try:
                records = session.query(CurrencyData).all()
                return [
                    {
                        "id": record.id,
                        "amount": record.amount,
                        "currency": record.currency,
                        "rate": record.rate,
                        "price_in_pln": record.price_in_pln,
                        "date": record.date.strftime("%Y-%m-%d"),
                    }
                    for record in records
                ]
            except Exception as e:
                logger.error("Error while retrieving data from the database: %s", e)
                raise

    def get_by_id(self, entity_id: int) -> dict | None:
        """
        Retrieves a specific currency data record by ID.

        Args:
        - entity_id (int): The ID of the currency data record to retrieve.
        """
        with self._get_session() as session:
            try:
                record = (
                    session.query(CurrencyData)
                    .filter(CurrencyData.id == entity_id)
                    .first()
                )
                if record:
                    record_as_dict = {
                        col.name: getattr(record, col.name)
                        for col in record.__table__.columns
                    }
                    record_as_dict["date"] = record_as_dict["date"].strftime("%Y-%m-%d")
                    return record_as_dict

                return None
            except Exception as e:
                logger.error("Error while retrieving data from the database: %s", e)
                raise

    def update(
        self,
        entity_id: int,
        amount: float | None = None,
        currency: str | None = None,
        date: str | None = None,
        rate: float | None = None,
        price_in_pln: float | None = None,
    ) -> str:
        """
        Updates the entity with the given id in the SQLite database.

        Args:
        - entity_id (int): The ID of the entity to update.
        - amount (Optional[float]): A price in source currency.
        - currency (Optional[str]): The new currency code, if updating.
        - rate (Optional[float]): The new exchange rate, if updating.
        - price_in_pln (Optional[float]): The new price in PLN, if updating.
        - date (Optional[str]): The new date, if updating.
        """
        with self._get_session() as session:
            record = (
                session.query(CurrencyData).filter(CurrencyData.id == entity_id).first()
            )
            if not record:
                return f"No currency with id '{entity_id}' in the database."
            logger.debug("Database record to update: %s" % record.__dict__)

            validate_currency_input_data(currency, date, rate, price_in_pln)

            record.amount = amount or record.amount
            record.currency = currency or record.currency
            record.rate = rate or record.rate
            record.price_in_pln = price_in_pln or record.price_in_pln
            record.date = (
                datetime.datetime.strptime(date, "%Y-%m-%d").date()
                if date
                else record.date
            )

            try:
                session.commit()
                session.refresh(record)
                logger.debug("Database record after update: %s" % record.__dict__)
                return f"Currency with id '{entity_id}' was successfully updated."
            except Exception as e:
                logger.error("Error while updating the record in the database: %s", e)
                raise

    def delete(self, entity_id: int) -> str:
        """
        Deletes a specific currency data record by its ID.

        Args:
        - entity_id (int): The ID of the currency data record to delete.
        """
        with self._get_session() as session:
            try:
                data = (
                    session.query(CurrencyData)
                    .filter(CurrencyData.id == entity_id)
                    .first()
                )
                if data:
                    session.delete(data)
                    session.commit()
                    return f"Currency with id '{entity_id}' deleted from the database."
                return f"No currency with id '{entity_id}' to delete from the database."
            except Exception as e:
                logger.error("Error while deleting data from the database: %s", e)
                raise
