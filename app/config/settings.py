"""
Singleton Settings class for managing environment variables and configuration.
This module uses Pydantic for validation and provides a centralized configuration source.
"""
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator



class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses Pydantic for validation and automatic type coercion.
    """

    # Application Settings
    APP_NAME: str = "Wall-Trade-Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False

    # Supabase Configuration
    SUPABASE_URL: str = "https://your-supabase-url.supabase.co"
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None

    # Database Configuration
    DATABASE_URL: Optional[str] = None

    # External market/AI services. Endpoints remain registered when absent.
    CAPITAL_API_KEY: Optional[str] = None
    CAPITAL_STAKE_API_KEY: Optional[str] = None
    AI_API_KEY: Optional[str] = None
    PSX_PROXY_URL: Optional[str] = None
    FMP_API_KEY: Optional[str] = None

    # Security Settings
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS Settings
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    class Config:
        """Pydantic config for BaseSettings."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is one of the allowed values."""
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"

    @property
    def supabase_database_key(self) -> Optional[str]:
        """Prefer service-role key for backend DB work, then anon aliases."""
        return self.SUPABASE_SERVICE_ROLE_KEY or self.SUPABASE_KEY or self.SUPABASE_ANON_KEY

    @property
    def capital_stake_key(self) -> Optional[str]:
        """Support both FRD and existing repository env names."""
        return self.CAPITAL_STAKE_API_KEY or self.CAPITAL_API_KEY


@lru_cache()
def get_settings() -> Settings:
    """
    Get singleton Settings instance.
    Uses LRU cache to ensure only one instance is created.

    Returns:
        Settings: Singleton settings instance
    """
    return Settings()
