import json
import os

import pytest

# os.environ["ENV_STATE"] = "test"  # w naszym zadaniu chyba mowa o dev jako środowisku testowym

clean_test_db = True
clean_currency_db = True

TEST_DB_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_DB_FILE = os.path.join(TEST_DB_DIR, "test_db.json")
CURRENCY_DB_FILE = os.path.join(TEST_DB_DIR, "currency_db.json")

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
    return TEST_DB_FILE


@pytest.fixture
def test_db_content():
    return TEST_DB


@pytest.fixture
def test_json_db():
    os.makedirs(TEST_DB_DIR, exist_ok=True)
    try:
        with open(TEST_DB_FILE, "w") as file:
            json.dump(TEST_DB, file, indent=4)

        with open(TEST_DB_FILE, "r") as file:
            yield json.load(file)
    finally:
        if clean_test_db:
            if os.path.exists(TEST_DB_FILE):
                os.remove(TEST_DB_FILE)


@pytest.fixture
def currency_load_db():
    os.makedirs(TEST_DB_DIR, exist_ok=True)
    try:
        with open(CURRENCY_DB_FILE, "w") as file:
            json.dump(CURRENCY_DB, file, indent=4)

        with open(CURRENCY_DB_FILE, "r") as file:
            yield json.load(file)
    finally:
        if clean_currency_db:
            if os.path.exists(CURRENCY_DB_FILE):
                os.remove(CURRENCY_DB_FILE)
