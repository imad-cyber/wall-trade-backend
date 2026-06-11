"""
Base service class.
Provides common functionality for all service classes.
"""
from app.core import get_logger


class BaseService:
    """Base service class with common functionality."""

    def __init__(self):
        """Initialize base service."""
        self.logger = get_logger(self.__class__.__name__)

    def log_info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)

    def log_error(self, message: str, exc: Exception = None) -> None:
        """Log error message."""
        self.logger.error(message, exc_info=exc)

    def log_warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)
