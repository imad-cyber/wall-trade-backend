"""Auth unit tests."""
from datetime import timedelta

import pytest
from fastapi import HTTPException
from jose import jwt

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
