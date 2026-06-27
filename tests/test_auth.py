"""
Tests for authentication service.
"""
import pytest
from app.auth import AuthService


class TestAuthServiceLegacy:
    """Legacy auth tests (package import path)."""

    @pytest.fixture
    def auth_service(self):
        return AuthService()

    def test_hash_password(self, auth_service):
        password = "test_password_123"
        hashed = auth_service.hash_password(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password(self, auth_service):
        password = "test_password_123"
        hashed = auth_service.hash_password(password)
        assert auth_service.verify_password(password, hashed) is True
        assert auth_service.verify_password("wrong_password", hashed) is False

    def test_create_access_token(self, auth_service):
        data = {"sub": "user123"}
        token = auth_service.create_access_token(data)
        assert token is not None
        assert isinstance(token, str)

    def test_verify_token(self, auth_service):
        data = {"sub": "user123"}
        token = auth_service.create_access_token(data)
        decoded = auth_service.verify_token(token)
        assert decoded["sub"] == "user123"
