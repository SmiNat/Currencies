from enum import Enum


class LocalDatabaseUrl(str, Enum):
    """Enum for specifying directory of local databases."""

    PROD_DATABASE_URL = (
        "sqlite:///database.sqlite3"  # move to config.py file with basic config rules
    )
    DEV_DATABASE_URL = (
        "tests/database.json"  # move to config.py file with basic config rules
    )

    PROD_DATABASE_NAME = "database.sqlite3"
    DEV_DATABASE_NAME = "database.json"

    CURRENCY_RATES_URL = "example_currency_rates.json"


class CurrencySource(str, Enum):
    """Enum for specifying the source of currency data."""

    API_NBP = "api nbp"
    JSON_FILE = "json file"


class NbpWebApiUrl(str, Enum):
    """Enum for NBP URL addresses."""

    TABLE_A_ALL_CURRENCIES = r"https://api.nbp.pl/api/exchangerates/tables/a/"
    TABLE_A_SINGLE_CURRENCY = r"https://api.nbp.pl/api/exchangerates/rates/a/"
