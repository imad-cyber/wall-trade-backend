"""Logging compatibility shim — use app.core.logging instead."""
from app.core.logging import get_logger, setup_logging

__all__ = ["setup_logging", "get_logger"]
