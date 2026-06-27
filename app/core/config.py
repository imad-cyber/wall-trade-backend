"""
Application settings — authoritative configuration module.
Consolidated from app/config/settings.py with additional provider and cache fields.
"""
from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Wall-Trade-Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    APP_ENV: Optional[str] = None

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False

    # Supabase
    SUPABASE_URL: str = "https://your-supabase-url.supabase.co"
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None
    DATABASE_URL: Optional[str] = None

    # External APIs
    CAPITAL_API_KEY: Optional[str] = None
    CAPITAL_STAKE_API_KEY: Optional[str] = None
    CAPITAL_STAKE_BASE_URL: Optional[str] = None
    AI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    PSX_PROXY_URL: Optional[str] = None
    PSX_PROXY_BASE_URL: Optional[str] = None
    FMP_API_KEY: Optional[str] = None
    FMP_BASE_URL: str = "https://financialmodelingprep.com/api/v3"

    # AI
    AI_MODEL: str = "gpt-4o"
    AI_MAX_TOKENS: int = 4096

    # Cache TTL
    ANALYSIS_CACHE_TTL_HOURS: int = 24
    MACRO_CACHE_TTL_HOURS: int = 6

    # HTTP defaults
    DEFAULT_TIMEOUT_SECONDS: float = 10.0
    DEFAULT_MAX_RETRIES: int = 3

    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    ALLOWED_ORIGINS: Optional[list[str]] = None
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def supabase_database_key(self) -> Optional[str]:
        return self.SUPABASE_SERVICE_ROLE_KEY or self.SUPABASE_KEY or self.SUPABASE_ANON_KEY

    @property
    def capital_stake_key(self) -> Optional[str]:
        return self.CAPITAL_STAKE_API_KEY or self.CAPITAL_API_KEY

    @property
    def psx_proxy_base_url(self) -> Optional[str]:
        return self.PSX_PROXY_BASE_URL or self.PSX_PROXY_URL

    @property
    def ai_api_key(self) -> Optional[str]:
        return self.AI_API_KEY or self.OPENAI_API_KEY

    @property
    def allowed_origins(self) -> list[str]:
        return self.ALLOWED_ORIGINS or self.CORS_ORIGINS


@lru_cache()
def get_settings() -> Settings:
    """Get singleton Settings instance."""
    return Settings()
