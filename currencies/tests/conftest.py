import datetime
import json
import os
from unittest.mock import patch

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from currencies.config import Config

load_dotenv()

# uwaga, w przypadku wykorzystania zmiennych środowiskowych do ustanowienia testowych warunków,
# należy dopasować zmienną odpowiedzialną za wybór środowiska (eg. ENV_STATE)
# oraz zbudować mechanizm uzależniający prowadzenie testów na wybranym środowisku
os.environ["ENV_STATE"] = "test"  # tu: łącze nieaktywne
# tu: niezbędne łącza do plików testowych zostały określone z niniejszym pliku

from currencies.database_config import Base, CurrencyData, sessionmaker  # noqa: E402

TEST_DB_DIR = os.path.dirname(os.path.realpath(__file__))

TEST_DB_JSON_URL = os.path.join(TEST_DB_DIR, "database_for_tests.json")

TEST_DB_SQLITE_PATH = os.path.join(TEST_DB_DIR, "database_for_tests.sqlite")
TEST_DB_SQLITE_URL = f"sqlite:///{TEST_DB_SQLITE_PATH}"

TEST_CURRENCY_LOCAL_DB_URL = os.path.join(TEST_DB_DIR, "currency_db.json")

TEST_DB = {
    "1": {
        "id": 1,
        "amount": 10,
        "currency": "eur",
        "currency_rate": 4.44,
        "currency_date": "2010-10-10",
        "price_in_pln": 22.2,
    },
    "3": {
        "id": 3,
        "amount": 5,
        "currency": "eur",
        "currency_rate": 4.65,
        "currency_date": "2012-02-02",
        "price_in_pln": 23.25,
    },
}


CURRENCY_DB = {
    "EUR": [{"date": "2022-10-10", "rate": 4.25}, {"date": "2022-01-30", "rate": 4.05}],
    "CZK": [{"date": "2022-02-02", "rate": 0.29}, {"date": "2022-07-30", "rate": 0.28}],
}

# Set cleaning of database afert each test
clean_test_db = True
clean_currency_db = True


@pytest.fixture
def test_db_path():
    return TEST_DB_JSON_URL


@pytest.fixture
def test_db_content():
    return TEST_DB


@pytest.fixture
def test_json_db(test_db_path):
    os.makedirs(TEST_DB_DIR, exist_ok=True)

    with open(test_db_path, "w") as file:
        json.dump(TEST_DB, file, indent=4)

    with open(test_db_path, "r") as file:
        yield json.load(file)


@pytest.fixture(autouse=clean_test_db, scope="function")
def clean_test_json_db():
    try:
        yield
    finally:
        if os.path.exists(TEST_DB_JSON_URL):
            os.remove(TEST_DB_JSON_URL)


@pytest.fixture
def test_currency_local_db_path():
    return TEST_CURRENCY_LOCAL_DB_URL


@pytest.fixture
def test_currency_local_db_content():
    return CURRENCY_DB


@pytest.fixture
def currency_load_db(test_currency_local_db_path):
    os.makedirs(TEST_DB_DIR, exist_ok=True)

    with open(test_currency_local_db_path, "w") as file:
        json.dump(CURRENCY_DB, file, indent=4)

    with open(test_currency_local_db_path, "r") as file:
        yield json.load(file)


@pytest.fixture
def mock_file_directory(test_currency_local_db_path):
    with patch(
        "currencies.connectors.local.file_reader.LOCAL_CURRENCY",
        test_currency_local_db_path,
    ):
        yield


@pytest.fixture(autouse=clean_currency_db, scope="function")
def clean_currency_load_db(currency_load_db):
    try:
        yield
    finally:
        if os.path.exists(TEST_CURRENCY_LOCAL_DB_URL):
            os.remove(TEST_CURRENCY_LOCAL_DB_URL)


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
def clean_sqlite_db():
    """Cleans db session for each test."""
    with TestingSessionLocal() as db:
        db.execute(text("DELETE FROM currency_data"))
        db.commit()


@pytest.fixture
def sqlite_db_initial_data():
    """Fixture to populate the test_db.sqlite with initial data."""
    db = TestingSessionLocal()
    try:
        # Insert records into the test_db.sqlite
        data1 = CurrencyData(
            amount=10,
            currency="GBP",
            currency_rate=5.1234,
            currency_date=datetime.date(2024, 6, 1),
            price_in_pln=51.234,
        )
        data2 = CurrencyData(
            amount=10,
            currency="USD",
            currency_rate=4.22,
            currency_date=datetime.date(2020, 10, 10),
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


@pytest.fixture()
def mock_config_env_state_dev():
    with patch.object(Config, "ENV_STATE", return_value="dev"):
        yield


@pytest.fixture()
def mock_config_env_state_prod():
    with patch.object(Config, "ENV_STATE", return_value="prod"):
        yield
