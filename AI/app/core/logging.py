import logging
from logging.config import dictConfig


def configure_logging() -> None:
    """Configure opinionated JSON-ready logging."""

    if logging.getLogger().handlers:
        # Already configured
        return

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "structured": {
                    "format": (
                        "%(asctime)s | %(levelname)s | %(name)s | "
                        "%(filename)s:%(lineno)d | %(message)s"
                    )
                }
            },
            "handlers": {
                "default": {
                    "level": "INFO",
                    "class": "logging.StreamHandler",
                    "formatter": "structured",
                }
            },
            "loggers": {
                "": {"handlers": ["default"], "level": "INFO"},
                "uvicorn.error": {"handlers": ["default"], "level": "INFO", "propagate": False},
                "uvicorn.access": {"handlers": ["default"], "level": "INFO", "propagate": False},
            },
        }
    )

