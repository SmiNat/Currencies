import os

from dotenv import load_dotenv
from sqlalchemy import Column, Float, Index, Integer, String, create_engine, func
from sqlalchemy.orm import declarative_base, sessionmaker, validates

from .utils import validate_date

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
    amount = Column(Float, nullable=False)
    currency = Column(String(5), nullable=False)  # Assuming codes with 3-5 characters
    currency_rate = Column(Float, nullable=False)
    currency_date = Column(String, nullable=False)  # 'YYYY-MM-DD' format allowed
    price_in_pln = Column(Float, nullable=False)

    __table_args__ = (
        Index(
            "idx_unique_currency_data",
            func.upper(currency),
            currency_rate,
            currency_date,
            price_in_pln,
            unique=True,
        ),
    )

    @validates("currency_date")
    def validate_date(self, key, date):
        validate_date(date)
        return date


# Creating database tables
Base.metadata.create_all(bind=engine)


# Creating a database connection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
