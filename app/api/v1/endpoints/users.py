"""User & auth endpoints — U1 through U4."""
from fastapi import APIRouter, Depends, status

from app.api.v1.dependencies import get_users_service
from app.api.v1.schemas.envelope import make_response
from app.api.v1.schemas.users import BetaSignupRequest, UpdateProfileRequest
from app.auth.dependencies import get_current_supabase_user
from app.services.users_service import UsersService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", status_code=status.HTTP_200_OK)
async def get_current_user_profile(
    user=Depends(get_current_supabase_user),
    service: UsersService = Depends(get_users_service),
):
    """U1 — Authenticated user profile."""
    profile = service.get_profile(user)
    return make_response(profile.model_dump(mode="json"))


@router.patch("/me", status_code=status.HTTP_200_OK)
async def update_user_profile(
    body: UpdateProfileRequest,
    user=Depends(get_current_supabase_user),
    service: UsersService = Depends(get_users_service),
):
    """U2 — Update display name / avatar."""
    profile = service.update_profile(user, body)
    return make_response(profile.model_dump(mode="json"))


@router.get("/me/subscription", status_code=status.HTTP_200_OK)
async def get_user_subscription(
    user=Depends(get_current_supabase_user),
    service: UsersService = Depends(get_users_service),
):
    """U3 — Subscription tier."""
    sub = service.get_subscription(user)
    return make_response(sub.model_dump(mode="json"))


@router.post("/beta-signup", status_code=status.HTTP_201_CREATED)
async def beta_signup(
    body: BetaSignupRequest,
    service: UsersService = Depends(get_users_service),
):
    """U4 — Public beta waitlist signup."""
    result = service.register_beta_signup(body.email)
    return make_response(result.model_dump(mode="json"))
