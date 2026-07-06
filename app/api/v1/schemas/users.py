"""User & auth response schemas."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class UserProfileResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    subscription_tier: Literal["free", "pro", "institutional"] = "free"
    created_at: Optional[str] = None
    last_login: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class SubscriptionResponse(BaseModel):
    tier: Literal["free", "pro", "institutional"] = "free"
    features: list[str] = Field(default_factory=list)


class BetaSignupRequest(BaseModel):
    email: str


class BetaSignupResponse(BaseModel):
    success: bool = True
    message: str = "You're on the list! We'll be in touch."
