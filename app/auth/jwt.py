"""JWT token creation and verification."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.security import hash_password, verify_password

logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)


class AuthService:
    """Service for JWT authentication operations."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    def hash_password(self, password: str) -> str:
        return hash_password(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return verify_password(plain_password, hashed_password)

    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode.update({"exp": expire})
        try:
            return jwt.encode(
                to_encode,
                self.settings.SECRET_KEY,
                algorithm=self.settings.ALGORITHM,
            )
        except Exception as exc:
            logger.error("Failed to create access token: %s", exc)
            raise

    def verify_token(self, token: str) -> dict:
        try:
            return jwt.decode(
                token,
                self.settings.SECRET_KEY,
                algorithms=[self.settings.ALGORITHM],
            )
        except JWTError as exc:
            logger.warning("Invalid token: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
