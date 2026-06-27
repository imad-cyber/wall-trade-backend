"""Compatibility shim for database module."""
from app.database import get_db_client, get_db_manager

__all__ = ["get_db_client", "get_db_manager"]
