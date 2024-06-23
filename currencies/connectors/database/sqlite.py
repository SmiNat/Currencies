import datetime
from contextlib import contextmanager

from sqlalchemy.orm import Session

from ...currency_converter import ConvertedPricePLN
from ...database_config import CurrencyData, SessionLocal


class SQLiteDatabaseConnector:
    """
    A connector class to interact with the SQLite database.

    Methods:
    - get_session(): Provides a context manager for database sessions.
    - add_currency_data(data: dict): Adds a new currency data record to the database.
    - get_all_currency_data(): Retrieves all currency data records from the database.
    - get_currency_data_by_id(currency_id: int): Retrieves a specific currency data record by ID.
    - delete_currency_data(currency_id: int): Deletes a specific currency data record by ID.
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
    def get_session(self):
        """
        Provides a context manager for database sessions.

        Yields:
        - Session: A SQLAlchemy session.
        """
        session = self.session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def add_currency_data(self, data: dict | ConvertedPricePLN) -> int:
        """
        Adds a new currency data record to the database.

        Args:
        - data (dict | ConvertedPricePLN): Currency data to add.

        Returns:
        - int: The ID of the newly added currency data record.
        """
        if isinstance(data, ConvertedPricePLN):
            data = data.__dict__

        data["currency_rate_fetch_date"] = datetime.strptime(
            data["currency_rate_fetch_date"], "%Y-%m-%d"
        ).date()

        with self.get_session() as session:
            new_data = CurrencyData(**data)
            session.add(new_data)
            session.commit()
            session.flush()  # Get the ID of the newly added record
            return new_data.id

    def get_all_currency_data(self) -> list:
        """
        Retrieves all currency data records from the database.

        Returns:
        - list[ConvertedPricePLN]: A list of all currency data records.
        """
        with self.get_session() as session:
            return session.query(CurrencyData).all()

    def get_currency_data_by_id(self, currency_id: int) -> CurrencyData:
        """
        Retrieves a specific currency data record by ID.

        Args:
        - currency_id (int): The ID of the currency data record to retrieve.

        Returns:
        - CurrencyData: The currency data record with the specified ID.
        """
        with self.get_session() as session:
            return (
                session.query(CurrencyData)
                .filter(CurrencyData.id == currency_id)
                .first()
            )

    def delete_currency_data(self, currency_id: int) -> bool:
        """
        Deletes a specific currency data record by ID.

        Args:
        - currency_id (int): The ID of the currency data record to delete.

        Returns:
        - str: A message indicating the result of the deletion operation.
        """
        with self.get_session() as session:
            data = (
                session.query(CurrencyData)
                .filter(CurrencyData.id == currency_id)
                .first()
            )
            if data:
                session.delete(data)
                session.commit()
                return f"Currency '{currency_id}' deleted from the database."
            return "No currency to delete from the database."
