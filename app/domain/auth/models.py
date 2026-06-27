"""Auth domain models."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.auth.enums import UserRole


class User(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    email: Optional[str] = None
    role: UserRole = UserRole.AUTHENTICATED


class Session(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: UUID
    created_at: datetime
    expires_at: datetime
