"""
Database connection management and session factory.
Provides connection pooling and lifecycle management for Supabase.
"""
from typing import Generator
from supabase import create_client, Client
from app.config import get_settings
from app.core import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Manages database connections and client lifecycle."""

    _instance: "DatabaseManager" = None
    _client: Client = None

    def __new__(cls) -> "DatabaseManager":
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize database manager."""
        if self._client is None:
            self._initialize_client()

    def _initialize_client(self) -> None:
        """
        Initialize Supabase client.
        
        Raises:
            ValueError: If required environment variables are missing
        """
        settings = get_settings()
        
        supabase_key = settings.supabase_database_key
        if not settings.SUPABASE_URL or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and one of SUPABASE_SERVICE_ROLE_KEY, SUPABASE_KEY, "
                "or SUPABASE_ANON_KEY must be configured"
            )
        
        try:
            self._client = create_client(settings.SUPABASE_URL, supabase_key)
            logger.info("Database client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database client: {str(e)}")
            raise

    @property
    def client(self) -> Client:
        """
        Get database client instance.
        
        Returns:
            Client: Supabase client instance
        """
        if self._client is None:
            self._initialize_client()
        return self._client

    def get_session(self) -> Generator:
        """
        Get database session for dependency injection.
        
        Yields:
            Client: Database client instance
        """
        yield self.client

    def close(self) -> None:
        """Close database connection."""
        if self._client is not None:
            try:
                logger.info("Closing database connection")
                self._client = None
            except Exception as e:
                logger.error(f"Error closing database connection: {str(e)}")


# Global database manager instance
_db_manager: DatabaseManager = None


def get_db_manager() -> DatabaseManager:
    """
    Get or create database manager singleton.
    
    Returns:
        DatabaseManager: Database manager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_db_client() -> Client:
    """
    Dependency injection function for database client.
    
    Returns:
        Client: Supabase client instance
    """
    return get_db_manager().client
