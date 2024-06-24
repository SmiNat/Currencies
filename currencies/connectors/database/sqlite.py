import datetime
import logging
from contextlib import contextmanager

from sqlalchemy.orm import Session

from ...currency_converter import ConvertedPricePLN
from ...database_config import CurrencyData, SessionLocal

logger = logging.getLogger(__name__)


class SQLiteDatabaseConnector:
    """
    A connector class to interact with the SQLite database.

    Methods:
    - _get_session: Provides a context manager for database sessions.
    - save: Adds a new currency data record to the database.
    - get_all: Retrieves all currency data records from the database.
    - get_by_id: Retrieves a specific currency data record by ID.
    - delete_currency_data: Deletes a specific currency data record by ID.
    """

    def __init__(self, session: Session | None = None) -> None:
        """
        Initializes the connector with the given session factory or the default SessionLocal.

        Args:
        - session (Session, optional): The session factory for creating database
          sessions. Defaults to SessionLocal if not provided.
        """
        self.session = SessionLocal if not session else session

    @contextmanager
    def _get_session(self) -> Session:  # type: ignore
        """
        Provides a context manager for database sessions.

        Yields:
        - Session: A SQLAlchemy session.

        Raises:
        - Exception: If an error occurs while accessing the database.
        """
        session = self.session()
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

        Returns:
        - int: The ID of the newly added currency data record or already existing one.

        Raises:
        - TypeError: If the provided entity is not an instance of ConvertedPricePLN.
        - Exception: If an unexpected error occurs while saving data to the database.
        """
        if not isinstance(entity, ConvertedPricePLN):
            raise TypeError("Entity must be a ConvertedPricePLN instance")

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
        """
        Retrieves all currency data records from the database.

        Returns:
        - list[dict[str, Any]]: A list with currency data records.

        Raises:
        - Exception: If an error occurs while retrieving data from the database.
        """
        with self._get_session() as session:
            try:
                records = session.query(CurrencyData).all()
                return [
                    {
                        "id": record.id,
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

        Returns:
        - [dict[str, Any] | None]: The currency data record with the specified ID,
          or None if it does not exist.

        Raises:
        - Exception: If an error occurs while retrieving data from the database.
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

    def delete_currency_data(self, entity_id: int) -> bool:
        """
        Deletes a specific currency data record by its ID.

        Args:
        - entity_id (int): The ID of the currency data record to delete.

        Returns:
        - str: A message indicating the result of the deletion operation.

        Raises:
        - Exception: If an error occurs while deleting data from the database.
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
                    return f"Currency '{entity_id}' deleted from the database."
                return "No currency to delete from the database."
            except Exception as e:
                logger.error("Error while deleting data from the database: %s", e)
                raise
