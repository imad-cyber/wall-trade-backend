"""
Centralized logging with JSON format and request_id injection.
"""
import logging
import logging.config
from typing import Any

from pythonjsonlogger import jsonlogger

from app.observability.context import get_ctx


class RequestIdFilter(logging.Filter):
    """Inject request_id from RequestContext into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_ctx().request_id or "-"
        return True


def setup_logging(level: str = "INFO", format_type: str = "json") -> None:
    """Configure application logging."""
    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_id": {
                "()": RequestIdFilter,
            },
        },
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(request_id)s %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": format_type,
                "filters": ["request_id"],
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": level,
                "formatter": format_type,
                "filters": ["request_id"],
                "filename": "logs/app.log",
                "maxBytes": 10485760,
                "backupCount": 10,
            },
        },
        "root": {
            "level": level,
            "handlers": ["console", "file"],
        },
        "loggers": {
            "uvicorn": {"level": level},
            "uvicorn.access": {"level": level, "handlers": ["console", "file"]},
        },
    }
    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
