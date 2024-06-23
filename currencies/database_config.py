import os

from dotenv import load_dotenv
from sqlalchemy import Column, Date, Float, Index, Integer, String, create_engine, func
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# Setting the database engine with a .sqlite3 file
engine = create_engine(
    url=str(os.environ.get("DATABASE_URL_FOR_PROD")),
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Setting database table
class CurrencyData(Base):
    """
    A SQLAlchemy ORM model representing converted prices to PLN.

    Attributes:
        id (int): Primary key.
        price_in_source_currency (float): Price in the source currency.
        currency (str): Source currency code.
        currency_rate (float): Exchange rate from source currency to PLN.
        currency_rate_fetch_date (date): Date when the exchange rate was fetched.
        price_in_pln (float): Price converted to PLN.
    """

    __tablename__ = "currency_data"

    id = Column(Integer, primary_key=True, index=True)
    # price_in_source_currency = Column(Float, nullable=False)  # ommited, as in database.json
    currency = Column(String(3), nullable=False)  # Assuming ISO 4217 currency codes
    rate = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    price_in_pln = Column(Float)

    __table_args__ = (
        Index(
            "idx_unique_currency_data",
            func.upper(currency),
            rate,
            date,
            price_in_pln,
            unique=True,
        ),
    )


# Creating database tables
Base.metadata.create_all(bind=engine)
