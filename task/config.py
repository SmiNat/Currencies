"""Depending on the purpose of using the application, change ENV_STATE variable
in the .env file to either 'prod' or 'dev' (test environment)."""

ENV_STATE = "prod"

PROD_DATABASE_NAME = "currencies.db"
DEV_DATABASE_NAME = "database.json"

PROD_DATABASE_URL = "sqlite:///currencies.db"
DEV_DATABASE_URL = "tests/database.json"
