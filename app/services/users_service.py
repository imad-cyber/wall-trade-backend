"""User profile and auth service."""
from typing import Any, Optional

from app.api.v1.schemas.users import (
    BetaSignupResponse,
    SubscriptionResponse,
    UpdateProfileRequest,
    UserProfileResponse,
)
from app.core.exceptions import ConflictError, ResourceNotFoundError
from app.repositories.profile_repository import ProfileRepository

TIER_FEATURES = {
    "free": ["basic_quotes", "company_overview"],
    "pro": ["basic_quotes", "company_overview", "pro_statistics", "pro_news", "technical_short_tf"],
    "institutional": ["all"],
}


class UsersService:
    def __init__(self, profile_repo: ProfileRepository):
        self.profile_repo = profile_repo

    def _to_profile(self, row: dict[str, Any], user_id: str, email: str = "") -> UserProfileResponse:
        return UserProfileResponse(
            id=row.get("id", user_id),
            email=row.get("email", email),
            display_name=row.get("display_name"),
            avatar_url=row.get("avatar_url"),
            subscription_tier=row.get("subscription_tier", "free"),
            created_at=row.get("created_at"),
            last_login=row.get("last_login"),
        )

    def get_profile(self, user: dict[str, Any]) -> UserProfileResponse:
        user_id = user["user_id"]
        email = user.get("email", "")
        row = self.profile_repo.get_by_user_id(user_id)
        if not row:
            row = self.profile_repo.upsert(
                user_id,
                {"email": email, "subscription_tier": "free"},
            )
        return self._to_profile(row, user_id, email)

    def update_profile(self, user: dict[str, Any], data: UpdateProfileRequest) -> UserProfileResponse:
        user_id = user["user_id"]
        payload = data.model_dump(exclude_none=True)
        row = self.profile_repo.upsert(user_id, payload)
        return self._to_profile(row, user_id, user.get("email", ""))

    def get_subscription(self, user: dict[str, Any]) -> SubscriptionResponse:
        profile = self.get_profile(user)
        tier = profile.subscription_tier
        return SubscriptionResponse(tier=tier, features=TIER_FEATURES.get(tier, TIER_FEATURES["free"]))

    def register_beta_signup(self, email: str) -> BetaSignupResponse:
        existing = self.profile_repo.get_beta_signup(email)
        if existing:
            raise ConflictError("Email already registered", error_code="CONFLICT")
        self.profile_repo.create_beta_signup(email)
        return BetaSignupResponse()
