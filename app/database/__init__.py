"""Database compatibility shim — use app.providers.supabase instead."""
from app.providers.supabase.client import close_supabase_client, get_authed_client, get_supabase_client


class DatabaseManager:
    """Backward-compatible wrapper around Supabase provider."""

    @property
    def client(self):
        return get_supabase_client()

    def close(self) -> None:
        close_supabase_client()


_db_manager = None


def get_db_manager() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_db_client():
    return get_supabase_client()


__all__ = ["DatabaseManager", "get_db_manager", "get_db_client", "get_authed_client"]
