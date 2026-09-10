"""
Unit tests verifying that FastAPI endpoints perform read-only queries suitable for api-sa permissions.
"""

from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.core.config import Settings, get_settings
from api.dependencies.bigquery import get_bigquery_client


@pytest.fixture
def mock_bq_client():
    mock_client = MagicMock()
    return mock_client


@pytest.fixture
def client(mock_bq_client):
    dummy_settings = Settings()
    dummy_settings.internal_api_key = "test-secret-key"
    dummy_settings.enforce_internal_key = True

    app.dependency_overrides[get_settings] = lambda: dummy_settings
    app.dependency_overrides[get_bigquery_client] = lambda: mock_bq_client
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_read_only_queries_oee(mock_bq_client, client):
    """Verify that OEE router issues SELECT read query and handles result."""
    mock_query_job = MagicMock()
    mock_query_job.result.return_value = [
        {
            "factory_id": "FAC01",
            "machine_id": "M01",
            "shift_id": "S1",
            "date_id": "2026-04-14",
            "oee_date": "2026-04-14",
            "planned_production_time_min": 480,
            "operating_time_min": 420,
            "planned_units": 1000,
            "produced_units": 950,
            "good_units": 900,
            "availability": 0.875,
            "performance": 0.95,
            "quality": 0.947,
            "oee": 0.787,
            "cycle_time_confidence": "HIGH",
            "availability_loss_sec": 3600,
            "performance_loss_sec": 1200,
            "unmapped_loss_sec": 0,
        }
    ]
    mock_bq_client.query.return_value = mock_query_job

    headers = {"X-Internal-Key": "test-secret-key"}
    response = client.get("/oee/daily", headers=headers, params={"start_date": "2026-04-01", "end_date": "2026-04-14"})

    assert response.status_code == 200
    assert mock_bq_client.query.called
    query_text = mock_bq_client.query.call_args[0][0]
    assert query_text.strip().upper().startswith("SELECT")
    assert "INSERT" not in query_text.upper()
    assert "UPDATE" not in query_text.upper()
    assert "DELETE" not in query_text.upper()


def test_read_only_queries_scrap(mock_bq_client, client):
    """Verify that scrap router issues SELECT read query."""
    mock_query_job = MagicMock()
    mock_query_job.result.return_value = []
    mock_bq_client.query.return_value = mock_query_job

    headers = {"X-Internal-Key": "test-secret-key"}
    response = client.get("/scrap/root-cause", headers=headers, params={"start_date": "2026-04-01", "end_date": "2026-04-14"})

    assert response.status_code == 200
    assert mock_bq_client.query.called
    query_text = mock_bq_client.query.call_args[0][0]
    assert query_text.strip().upper().startswith("SELECT")
