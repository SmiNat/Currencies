"""Depending on the purpose of using the application, change ENV_STATE variable
in the .env file to either 'prod' or 'dev' (test environment)."""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    ENV_STATE = os.environ.get(
        "ENV_STATE", "dev"
    )  # Default to 'dev' if ENV_STATE is not set

    if ENV_STATE == "prod":
        DATABASE_URL = os.environ.get("DATABASE_URL_FOR_PROD")
    elif ENV_STATE == "dev":
        DATABASE_URL = os.environ.get("DATABASE_URL_FOR_DEV")
    else:
        raise ValueError(f"Unsupported environment state: {ENV_STATE}")
