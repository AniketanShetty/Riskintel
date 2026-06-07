"""
tests/test_health.py

Phase 1 acceptance criteria — Task 1.2:
    - Flask app starts without errors.
    - GET / returns HTTP 200.
    - Response body contains {"status": "ok"}.

Run from project root:
    cd backend/
    pytest ../tests/test_health.py -v
"""
import sys
import os

# Ensure the backend/app package is importable when pytest is run from root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
from app import create_app


@pytest.fixture
def client():
    """Provide a Flask test client with TESTING mode enabled."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestHealthCheck:
    """Task 1.2 acceptance criteria."""

    def test_health_returns_200(self, client):
        """GET / must return HTTP 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_health_status_field(self, client):
        """Response JSON must contain status: ok."""
        data = client.get("/").get_json()
        assert data["status"] == "ok"

    def test_health_service_field(self, client):
        """Response JSON must identify the service name."""
        data = client.get("/").get_json()
        assert data["service"] == "RiskIntel API"

    def test_health_content_type_json(self, client):
        """Response Content-Type must be application/json."""
        response = client.get("/")
        assert response.content_type.startswith("application/json")
