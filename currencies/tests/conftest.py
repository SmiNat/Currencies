import datetime
import json
import os

import pytest
from sqlalchemy import create_engine

os.environ["ENV_STATE"] = (
    "test"  # w naszym zadaniu chyba mowa o dev jako środowisku testowym (?)
)

from currencies.database_config import Base, CurrencyData, sessionmaker  # noqa: E402

clean_test_db = True
clean_currency_db = True

TEST_DB_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_DB_JSON_FILE = os.path.join(TEST_DB_DIR, "test_db.json")

TEST_DB_SQLITE_URL = "sqlite:///currencies/tests/test_db.sqlite"
TEST_DB_SQLITE_FILE = os.path.join(TEST_DB_DIR, "test_db.sqlite")

CURRENCY_DB_JSON_FILE = os.path.join(TEST_DB_DIR, "currency_db.json")

TEST_DB = {
    "1": {
        "id": 1,
        "currency": "eur",
        "rate": 4.44,
        "price_in_pln": 22.2,
        "date": "2010-10-10",
    },
    "3": {
        "id": 3,
        "currency": "eur",
        "rate": 4.65,
        "price_in_pln": 23.25,
        "date": "2012-02-02",
    },
}


CURRENCY_DB = {
    "EUR": [{"date": "2023-10-01", "rate": 4.25}, {"date": "2023-01-30", "rate": 4.05}],
    "CZK": [{"date": "2023-03-02", "rate": 0.29}, {"date": "2023-07-30", "rate": 0.28}],
}


@pytest.fixture
def test_db_path():
    return TEST_DB_JSON_FILE


@pytest.fixture
def test_db_content():
    return TEST_DB


@pytest.fixture
def test_json_db():
    os.makedirs(TEST_DB_DIR, exist_ok=True)

    with open(TEST_DB_JSON_FILE, "w") as file:
        json.dump(TEST_DB, file, indent=4)

    with open(TEST_DB_JSON_FILE, "r") as file:
        yield json.load(file)


@pytest.fixture(autouse=clean_test_db, scope="function")
def clean_test_json_db():
    try:
        yield
    finally:
        if os.path.exists(TEST_DB_JSON_FILE):
            os.remove(TEST_DB_JSON_FILE)


@pytest.fixture
def currency_load_db():
    os.makedirs(TEST_DB_DIR, exist_ok=True)
    with open(CURRENCY_DB_JSON_FILE, "w") as file:
        json.dump(CURRENCY_DB, file, indent=4)

    with open(CURRENCY_DB_JSON_FILE, "r") as file:
        yield json.load(file)


@pytest.fixture(autouse=clean_currency_db, scope="function")
def clean_currency_load_db():
    try:
        yield
    finally:
        if os.path.exists(CURRENCY_DB_JSON_FILE):
            os.remove(CURRENCY_DB_JSON_FILE)


# Creating test.sqlite database instead of using application db (database.sqlite)
engine = create_engine(
    # url=config.DATABASE_URL,  # [opcjonalnie] skonfigurowanie lokalizacji w pliku config
    url=str(TEST_DB_SQLITE_URL),
    connect_args={"check_same_thread": False},
    echo=False,
)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Overriding database connection
@pytest.fixture
def db_session():
    """Sets a clean db session for each test."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=clean_currency_db, scope="function")
def clean_test_sqlite_db():
    try:
        yield
    finally:
        if os.path.exists(TEST_DB_SQLITE_FILE):
            os.remove(TEST_DB_SQLITE_FILE)


@pytest.fixture
def populate_test_sqlite_db():
    """Fixture to populate the test_db.sqlite with initial data."""
    db = TestingSessionLocal()
    try:
        # Insert records into the test_db.sqlite
        data1 = CurrencyData(
            currency="GBP",
            rate=5.1234,
            date=datetime.date(2024, 6, 1),
            price_in_pln=51.234,
        )
        data2 = CurrencyData(
            currency="USD",
            rate=4.22,
            date=datetime.date(2020, 10, 10),
            price_in_pln=42.2,
        )

        db.add(data1)
        db.commit()
        db.add(data2)
        db.commit()
        db.refresh(data1)
        db.refresh(data2)
        return data1, data2
    finally:
        db.close()
