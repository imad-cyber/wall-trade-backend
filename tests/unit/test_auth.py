"""Auth unit tests."""
from datetime import timedelta
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from jose import jwt

from app.auth.dependencies import get_optional_user
from app.auth.jwt import AuthService
from app.auth.supabase_auth import validate_supabase_token
from app.core.config import Settings
from app.core.exceptions import AuthenticationError


class TestAuthService:
    @pytest.fixture
    def auth_service(self):
        return AuthService()

    def test_hash_password(self, auth_service):
        hashed = auth_service.hash_password("test_password_123")
        assert hashed != "test_password_123"

    def test_verify_password(self, auth_service):
        password = "test_password_123"
        hashed = auth_service.hash_password(password)
        assert auth_service.verify_password(password, hashed) is True
        assert auth_service.verify_password("wrong", hashed) is False

    def test_create_access_token(self, auth_service):
        token = auth_service.create_access_token({"sub": "user123"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_valid(self, auth_service):
        token = auth_service.create_access_token({"sub": "user123"})
        decoded = auth_service.verify_token(token)
        assert decoded["sub"] == "user123"

    def test_verify_token_invalid(self, auth_service):
        with pytest.raises(HTTPException):
            auth_service.verify_token("invalid.token.here")

    def test_verify_token_expired(self, auth_service):
        token = auth_service.create_access_token(
            {"sub": "user123"},
            expires_delta=timedelta(seconds=-1),
        )
        with pytest.raises(HTTPException):
            auth_service.verify_token(token)


class TestSupabaseAuth:
    def test_missing_jwt_secret_dev_bypass(self):
        settings = Settings(SUPABASE_JWT_SECRET=None, ENVIRONMENT="development")
        result = validate_supabase_token(None, settings)
        assert result["user_id"] == "development"

    def test_missing_bearer_token(self):
        settings = Settings(SUPABASE_JWT_SECRET="secret", ENVIRONMENT="production")
        with pytest.raises(AuthenticationError) as exc:
            validate_supabase_token(None, settings)
        assert exc.value.error_code == "TOKEN_MISSING"

    def test_invalid_token(self):
        settings = Settings(SUPABASE_JWT_SECRET="secret", ENVIRONMENT="production")
        creds = type("Creds", (), {"credentials": "bad.token"})()
        with pytest.raises(AuthenticationError) as exc:
            validate_supabase_token(creds, settings)
        assert exc.value.error_code == "TOKEN_INVALID"

    def test_hs256_valid_token(self):
        settings = Settings(
            SUPABASE_JWT_SECRET="test-secret",
            ENVIRONMENT="production",
        )
        token = jwt.encode({"sub": "user-123"}, "test-secret", algorithm="HS256")
        creds = type("Creds", (), {"credentials": token})()
        result = validate_supabase_token(creds, settings)
        assert result["user_id"] == "user-123"

    def test_jwks_path_used_for_es256_header(self):
        settings = Settings(
            SUPABASE_URL="https://example.supabase.co",
            ENVIRONMENT="production",
        )
        token = jwt.encode(
            {"sub": "user-456"},
            "wrong-secret",
            algorithm="HS256",
            headers={"alg": "ES256", "kid": "test-kid"},
        )
        creds = type("Creds", (), {"credentials": token})()
        with patch("app.auth.supabase_auth._decode_jwks") as mock_jwks:
            mock_jwks.return_value = {"sub": "user-456"}
            result = validate_supabase_token(creds, settings)
        assert result["user_id"] == "user-456"
        mock_jwks.assert_called_once()


class TestOptionalUserDependency:
    @pytest.mark.asyncio
    async def test_invalid_token_returns_none(self):
        settings = Settings(SUPABASE_JWT_SECRET="secret", ENVIRONMENT="production")
        creds = type("Creds", (), {"credentials": "bad.token", "scheme": "Bearer"})()
        result = await get_optional_user(credentials=creds, settings=settings)
        assert result is None
