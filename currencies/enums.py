from enum import Enum


class CurrencySource(str, Enum):
    """Enum for specifying the source of currency data."""

    API_NBP = "api nbp"
    JSON_FILE = "json file"


class LocalDatabaseUrl(str, Enum):
    """Enum for specifying directory of local databases."""

    CURRENCY_RATES_URL = "currency_rates.json"


class NbpWebApiUrl(str, Enum):
    """Enum for NBP URL addresses."""

    TABLE_A_ALL_CURRENCIES = r"https://api.nbp.pl/api/exchangerates/tables/a/"
    TABLE_A_SINGLE_CURRENCY = r"https://api.nbp.pl/api/exchangerates/rates/a/"
