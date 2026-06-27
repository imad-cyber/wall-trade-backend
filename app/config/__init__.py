"""Configuration compatibility shim — use app.core.config instead."""
from app.core.config import Settings, get_settings

__all__ = ["Settings", "get_settings"]
