"""
Centralized logging with JSON format and request_id injection.
"""
import logging
import logging.config
import os
from pathlib import Path
from typing import Any

from pythonjsonlogger import jsonlogger

from app.observability.context import get_ctx


class RequestIdFilter(logging.Filter):
    """Inject request_id from RequestContext into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_ctx().request_id or "-"
        return True


def _use_file_logging() -> bool:
    """File logs are for local development; serverless runtimes use stdout only."""
    if os.getenv("VERCEL"):
        return False
    log_dir = Path("logs")
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return False
    return True


def setup_logging(level: str = "INFO", format_type: str = "json") -> None:
    """Configure application logging."""
    handlers: dict[str, Any] = {
        "console": {
            "class": "logging.StreamHandler",
            "level": level,
            "formatter": format_type,
            "filters": ["request_id"],
            "stream": "ext://sys.stdout",
        },
    }
    root_handlers = ["console"]

    if _use_file_logging():
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": level,
            "formatter": format_type,
            "filters": ["request_id"],
            "filename": "logs/app.log",
            "maxBytes": 10485760,
            "backupCount": 10,
        }
        root_handlers.append("file")

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
        "handlers": handlers,
        "root": {
            "level": level,
            "handlers": root_handlers,
        },
        "loggers": {
            "uvicorn": {"level": level},
            "uvicorn.access": {"level": level, "handlers": root_handlers},
        },
    }
    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
