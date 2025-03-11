import logging
import logging.config
from pathlib import Path

from app.core.config import settings

LOG_FILE_PATH = Path(settings.LOG_FILE_PATH)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": settings.DISABLE_EXISTING_LOGGERS,
    "formatters": {
        "default": {
            "format": settings.DEFAULT_FORMAT,
        },
        "detailed": {
            "format": settings.DETAILED_FORMAT,
        },
    },
    "handlers": {
        "console": {
            "level": settings.CONSOLE_LOG_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "file": {
            "level": settings.FILE_LOG_LEVEL,
            "class": "logging.FileHandler",
            "formatter": "detailed",
            "filename": settings.LOG_FILE_PATH,
            "mode": "a",
        },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["console", "file"],
            "level": settings.ROOT_LOG_LEVEL,
            "propagate": settings.ROOT_PROPAGATE,
        },
        "my_module": {
            "handlers": ["console", "file"],
            "level": settings.MODULE_LOG_LEVEL,
            "propagate": settings.MODULE_PROPAGATE,
        },
    },
}

# Ensure the log directory exists
LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.config.dictConfig(LOGGING_CONFIG)

def get_logger(name: str):
    return logging.getLogger(name)