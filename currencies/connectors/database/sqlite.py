import datetime
from contextlib import contextmanager

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...currency_converter import ConvertedPricePLN
from ...database_config import CurrencyData, SessionLocal
from ...exceptions import CurrencyDataIntegrityError


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
    def _get_session(self):
        """
        Provides a context manager for database sessions.

        Yields:
        - Session: A SQLAlchemy session.
        """
        session = self.session()
        try:
            yield session
        except Exception:
            session.rollback()
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
        - int: The ID of the newly added currency data record.
        """
        if not isinstance(entity, ConvertedPricePLN):
            raise TypeError("Entity must be a ConvertedPricePLN instance")

        with self._get_session() as session:
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
            except IntegrityError:
                raise CurrencyDataIntegrityError()

    def get_all(self) -> list:
        """
        Retrieves all currency data records from the database.

        Returns:
        - list[ConvertedPricePLN]: A list of all currency data records.
        """
        with self._get_session() as session:
            return session.query(CurrencyData).all()

    def get_by_id(self, entity_id: int) -> CurrencyData:
        """
        Retrieves a specific currency data record by ID.

        Args:
        - entity_id (int): The ID of the currency data record to retrieve.

        Returns:
        - CurrencyData: The currency data record with the specified ID.
        """
        with self._get_session() as session:
            return (
                session.query(CurrencyData).filter(CurrencyData.id == entity_id).first()
            )

    def delete_currency_data(self, entity_id: int) -> bool:
        """
        Deletes a specific currency data record by ID.

        Args:
        - entity_id (int): The ID of the currency data record to delete.

        Returns:
        - str: A message indicating the result of the deletion operation.
        """
        with self._get_session() as session:
            data = (
                session.query(CurrencyData).filter(CurrencyData.id == entity_id).first()
            )
            if data:
                session.delete(data)
                session.commit()
                return f"Currency '{entity_id}' deleted from the database."
            return "No currency to delete from the database."
