"""
Tests for authentication service.
"""
import pytest
from app.auth import AuthService


class TestAuthService:
    """Test authentication service."""

    @pytest.fixture
    def auth_service(self):
        """Create auth service instance."""
        return AuthService()

    def test_hash_password(self, auth_service):
        """Test password hashing."""
        password = "test_password_123"
        hashed = auth_service.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password(self, auth_service):
        """Test password verification."""
        password = "test_password_123"
        hashed = auth_service.hash_password(password)
        
        assert auth_service.verify_password(password, hashed) is True
        assert auth_service.verify_password("wrong_password", hashed) is False

    def test_create_access_token(self, auth_service):
        """Test token creation."""
        data = {"sub": "user123"}
        token = auth_service.create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token(self, auth_service):
        """Test token verification."""
        data = {"sub": "user123"}
        token = auth_service.create_access_token(data)
        
        decoded = auth_service.verify_token(token)
        assert decoded["sub"] == "user123"
