"""
Example tests for the application.
Place your tests in this directory and run with: pytest
"""
import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test health check returns 200 with contract envelope."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "ok"
        assert "application" in data["data"]
        assert "version" in data["data"]
        assert "environment" in data["data"]
        assert "request_id" in data

    def test_health_check_response_structure(self, client):
        """Test health check response structure."""
        response = client.get("/health")
        data = response.json()
        assert isinstance(data, dict)
        assert "data" in data
        assert data["data"]["status"] == "ok"


class TestExceptionHandling:
    """Test exception handling."""

    def test_404_not_found(self, client):
        """Test 404 handling."""
        response = client.get("/nonexistent")
        assert response.status_code == 404


# Add more tests for your routes and services below
