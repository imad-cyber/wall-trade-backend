"""
Centralized logging configuration.
Provides structured logging for the application with JSON format support.
"""
import logging
import logging.config
from typing import Any
from pythonjsonlogger import jsonlogger


def setup_logging(level: str = "INFO", format_type: str = "json") -> None:
    """
    Configure application logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type - 'json' for JSON format, 'standard' for standard format
    """
    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": format_type,
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": level,
                "formatter": format_type,
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
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
            "sqlalchemy": {"level": "WARNING"},
        },
    }

    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)
