import importlib
import os
from unittest.mock import patch

import pytest

from currencies.config import Config


def reload_config_module():
    # Reload the config module to ensure it picks up the patched environment variables
    import currencies.config as config_module

    importlib.reload(config_module)
    return config_module.Config()


def test_conifig_init():
    config = Config()
    assert isinstance(config, Config)


def test_config_prod_environment():
    with patch.dict(
        os.environ, {"ENV_STATE": "prod", "PROD_DATABASE_URL": "postgresql://prod.db"}
    ):
        config = reload_config_module()
        assert config.ENV_STATE == "prod"
        assert config.DATABASE_URL == "postgresql://prod.db"


def test_config_dev_environment():
    with patch.dict(
        os.environ, {"ENV_STATE": "dev", "DEV_DATABASE_URL": "some_database.json"}
    ):
        config = reload_config_module()
        assert config.ENV_STATE == "dev"
        assert config.DATABASE_URL == "some_database.json"


def test_config_unsupported_environment():
    with patch.dict(os.environ, {"ENV_STATE": "invalid"}):
        with pytest.raises(ValueError, match="Unsupported environment state: invalid"):
            reload_config_module()
