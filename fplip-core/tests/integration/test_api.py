"""
Integration tests for the FPLIP API.
Tests against a running container or local instance.
"""

import pytest
import httpx
from datetime import date, timedelta

BASE_URL = "http://localhost:8000"


@pytest.fixture
def client():
    """Create an HTTP client for testing."""
    return httpx.Client(base_url=BASE_URL, timeout=30.0)


def test_health(client):
    """Test the health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "ok"
    assert data["bigquery"] == "ok"


def test_oee_daily_success(client):
    """Test OEE daily endpoint with valid date range."""
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    response = client.get(
        "/oee/daily",
        params={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
    )
    assert response.status_code == 200
    # Empty array is valid (no data for this date range)
    assert isinstance(response.json(), list)


def test_oee_daily_malformed_date(client):
    """Test OEE daily with malformed date (should return 400)."""
    response = client.get(
        "/oee/daily",
        params={
            "start_date": "2026-07-25",
            "end_date": "2026-07-20",  # End date before start date
        }
    )
    assert response.status_code == 400
    assert "start_date must be before or equal to end_date" in response.text


def test_oee_daily_machine_filter(client):
    """Test OEE daily with machine filter."""
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    response = client.get(
        "/oee/daily",
        params={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "machine_id": "M01",  # Non-existent machine, but valid filter
        }
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_oee_summary_success(client):
    """Test OEE summary endpoint."""
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    response = client.get(
        "/oee/summary",
        params={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_scrap_root_cause_success(client):
    """Test scrap root cause endpoint."""
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    response = client.get(
        "/scrap/root-cause",
        params={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_scrap_root_cause_with_filter(client):
    """Test scrap root cause with defect category filter."""
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    response = client.get(
        "/scrap/root-cause",
        params={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "defect_category": "N/A - Pass",  # Valid category
        }
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_oee_summary_malformed_date(client):
    """Test OEE summary with malformed date range."""
    response = client.get(
        "/oee/summary",
        params={
            "start_date": "2026-07-25",
            "end_date": "2026-07-20",
        }
    )
    assert response.status_code == 400


def test_scrap_root_cause_malformed_date(client):
    """Test scrap root cause with malformed date range."""
    response = client.get(
        "/scrap/root-cause",
        params={
            "start_date": "2026-07-25",
            "end_date": "2026-07-20",
        }
    )
    assert response.status_code == 400


def test_oee_daily_invalid_date_format(client):
    """Test OEE daily with invalid date format."""
    response = client.get(
        "/oee/daily",
        params={
            "start_date": "not-a-date",
            "end_date": "2026-07-20",
        }
    )
    assert response.status_code == 422  # Validation error from Pydantic