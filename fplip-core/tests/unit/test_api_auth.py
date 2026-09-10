"""
Unit tests for FastAPI service-to-service authentication (X-Internal-Key).
"""

import os
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.core.config import Settings, get_settings


@pytest.fixture
def client():
    return TestClient(app)


def test_public_health_endpoint_no_auth(client):
    """Test that public endpoints (/health) do not require authentication."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json().get("app") == "ok"


def test_protected_endpoint_valid_internal_key(client):
    """Test that protected endpoints succeed when valid X-Internal-Key header is provided."""
    dummy_settings = Settings()
    dummy_settings.internal_api_key = "test-secret-key"
    dummy_settings.enforce_internal_key = True

    app.dependency_overrides[get_settings] = lambda: dummy_settings

    try:
        response = client.get(
            "/machine/context",
            headers={"X-Internal-Key": "test-secret-key"},
            params={"machine_id": "M01", "start_date": "2026-01-01", "end_date": "2026-01-02"},
        )
        # Should not fail with 401 Unauthorized
        assert response.status_code != 401
    finally:
        app.dependency_overrides.clear()


def test_protected_endpoint_missing_key_strict_mode(client):
    """Test that protected endpoints return 401 in strict mode when header is missing."""
    dummy_settings = Settings()
    dummy_settings.internal_api_key = "test-secret-key"
    dummy_settings.enforce_internal_key = True

    app.dependency_overrides[get_settings] = lambda: dummy_settings

    try:
        response = client.get(
            "/machine/context",
            params={"machine_id": "M01", "start_date": "2026-01-01", "end_date": "2026-01-02"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or missing X-Internal-Key header"
    finally:
        app.dependency_overrides.clear()


def test_protected_endpoint_wrong_key_strict_mode(client):
    """Test that protected endpoints return 401 in strict mode when wrong key is provided."""
    dummy_settings = Settings()
    dummy_settings.internal_api_key = "test-secret-key"
    dummy_settings.enforce_internal_key = True

    app.dependency_overrides[get_settings] = lambda: dummy_settings

    try:
        response = client.get(
            "/machine/context",
            headers={"X-Internal-Key": "wrong-secret-key"},
            params={"machine_id": "M01", "start_date": "2026-01-01", "end_date": "2026-01-02"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or missing X-Internal-Key header"
    finally:
        app.dependency_overrides.clear()


def test_protected_endpoint_missing_key_soft_mode(client):
    """Test that in soft mode (enforce=False), missing keys do not trigger 401."""
    dummy_settings = Settings()
    dummy_settings.internal_api_key = "test-secret-key"
    dummy_settings.enforce_internal_key = False

    app.dependency_overrides[get_settings] = lambda: dummy_settings

    try:
        response = client.get(
            "/machine/context",
            params={"machine_id": "M01", "start_date": "2026-01-01", "end_date": "2026-01-02"},
        )
        assert response.status_code != 401
    finally:
        app.dependency_overrides.clear()
