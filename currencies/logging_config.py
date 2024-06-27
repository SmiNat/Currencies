import logging
import os
from enum import Enum
from logging.config import dictConfig

from .config import Config

# Creating directory for logger file in dev (test) environment
if Config.ENV_STATE == "dev":
    if not os.path.exists(os.path.join(os.path.dirname(__file__), "tests")):
        os.mkdir(os.path.join(os.path.dirname(__file__), "tests"))


class FontColor(str, Enum):
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    LIGTH_BLUE_CYAN = "\033[96m"
    PURPLE_MAGNETA = "\033[95m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    WHITE = "\033[97m"
    DEFAULT = "\033[39m"


class FontBackground(str, Enum):
    BLACK = "\033[40m"
    BLUE = "\033[43m"
    GREEN = "\033[42m"
    LIGTH_BLUE_CYAN = "\033[46m"
    PURPLE_MAGNETA = "\033[45m"
    RED = "\033[41m"
    YELLOW = "\033[43m"
    WHITE = "\033[47m"
    DEFAULT = "\033[49m"


class FontType(str, Enum):
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALICS = "\033[3m"
    UNDERLINE = "\033[4m"
    CONCEAL = "\033[8m"
    CROSSED_OUT = "\033[9m"
    BOLD_OFF = "\033[22m"
    DEFAULT = ""


class FontReset(str, Enum):
    SUFFIX = "\033[0m"


class ColoredFormatter(logging.Formatter):
    MAPPING = {
        "DEBUG": FontColor.WHITE,
        "INFO": FontColor.LIGTH_BLUE_CYAN,
        "WARNING": FontColor.YELLOW,
        "ERROR": FontColor.RED,
        "CRITICAL": FontBackground.RED,
    }

    def __init__(
        self,
        custom_format=None,
        name_color=FontColor.DEFAULT,
        name_font_type=FontType.DEFAULT,
        message_color=FontColor.DEFAULT,
        message_font_type=FontType.DEFAULT,
        *args,
        **kwargs,
    ):
        datefmt = kwargs.pop("datefmt", "%Y-%m-%d %H:%M:%S")
        logging.Formatter.__init__(self, *args, datefmt=datefmt, **kwargs)

        if not custom_format:
            self.desired_format = (
                "%(asctime)s.%(msecs)03dZ - "
                "%(levelname)-8s - "
                f"{name_color}{name_font_type}%(name)s{FontReset.SUFFIX} - "
                "%(filename)s:%(lineno)s - %(funcName)s"
                f"{FontColor.YELLOW} >>> {FontReset.SUFFIX} "
                f"{message_color}{message_font_type}%(message)s{FontReset.SUFFIX}"
            )
        else:
            self.desired_format = custom_format

    def format(self, record):
        # Making a copy of a record to prevent altering the message for other loggers
        record = logging.makeLogRecord(record.__dict__)

        extra_info = record.__dict__.pop("additional information", "")
        if extra_info:
            record.msg += f"\nAdditional information: {extra_info}"

        # Changing levelname color depending on logger actual level
        color = self.MAPPING.get(record.levelname, FontColor.DEFAULT)
        record.levelname = f"{color}{record.levelname:<8}{FontReset.SUFFIX}"

        # Formatting the record using desired_format
        self._style._fmt = self.desired_format
        msg = super().format(record)
        return msg


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console": {
                    "()": ColoredFormatter,
                    "name_color": FontColor.GREEN,
                    "message_color": FontColor.GREEN,
                },
                "file": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "%(asctime)s.%(msecs)03dZ - %(levelname)8s - PROD - %(name)s - %(filename)s:%(lineno)s --- %(message)s",
                },
                "test": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                    "format": "%(asctime)s.%(msecs)03dZ - %(levelname)8s - TEST - %(name)s - %(filename)s:%(lineno)s --- %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "console",
                },
                "files": {
                    "class": "logging.FileHandler",
                    "level": "DEBUG",
                    "formatter": "file",
                    "filename": "logs_rotating.log",
                    "encoding": "utf-8",
                },
                "tests": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "test",
                    "filename": os.path.join(
                        os.path.dirname(__file__), "tests", "logs_test.log"
                    ),
                    "mode": "a",
                    "maxBytes": 1024 * 512,  # 0.5MB
                    "backupCount": 2,
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                "currencies": {
                    "handlers": [
                        "console",
                        "tests" if Config.ENV_STATE == "dev" else "files",
                    ],
                    "level": "INFO" if Config.ENV_STATE == "prod" else "DEBUG",
                    "propagade": False,
                }
            },
        }
    )
