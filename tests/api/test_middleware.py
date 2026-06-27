"""Middleware API tests."""
import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


def test_request_id_header_present(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0


def test_process_time_header_present(client):
    response = client.get("/health")
    assert "X-Process-Time" in response.headers
    assert response.headers["X-Process-Time"].endswith("ms")


def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "walltrade_request_total" in response.text
