import os

from dotenv import load_dotenv
from sqlalchemy import Column, Date, Float, Index, Integer, String, create_engine, func
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# Setting the database engine with a .sqlite3 file
engine = create_engine(
    url=str(os.environ.get("PROD_DATABASE_URL")),
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Setting database tables
class CurrencyData(Base):
    """
    A SQLAlchemy ORM model representing converted prices to PLN.
    """

    __tablename__ = "currency_data"

    id = Column(Integer, primary_key=True, index=True)
    # price_in_source_currency = Column(Float, nullable=False)  # ommited, as in database.json
    currency = Column(String(5), nullable=False)  # Assuming codes with 3-5 characters
    rate = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    price_in_pln = Column(Float, nullable=False)

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
