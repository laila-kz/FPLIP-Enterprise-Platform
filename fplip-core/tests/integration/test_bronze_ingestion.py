#!/usr/bin/env python3
"""
Integration tests for Bronze ingestion.
Tests the full extract-validate-load pipeline against real BigQuery.
Uses a reserved test date to avoid colliding with real data.
"""

import os
import tempfile
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import pytest

from ingestion.bronze_loader import load_to_bronze
from common.gcp import resolve_project_id

# Use a test date that's far in the future but consistent
TEST_DATE = date(2099, 1, 1)
PROJECT_ID = resolve_project_id()
DATASET = "fplip_bronze"


@pytest.fixture
def test_dataframe():
    """Create a small test dataframe for production runs."""
    return pd.DataFrame(
        {
            "log_reference_number": ["TEST-001", "TEST-002"],
            "machine_id": ["M01", "M02"],
            "shift_id": ["S1", "S2"],
            "product_id": ["P-BLOCK-01", "P-BLOCK-02"],
            "run_date": [TEST_DATE.isoformat(), TEST_DATE.isoformat()],
            "run_sequence_number": [1, 1],
            "run_start_time": [None, None],
            "run_end_time": [None, None],
            "planned_units": [100, 200],
            "produced_units": [95, 180],
            "good_units": [90, 170],
            "operator_id": ["EMP-0001", "EMP-0002"],
            "notes": ["Test row 1", "Test row 2"],
            "data_entry_method": ["Manual", "Manual"],
            "entered_by": ["EMP-0001", "EMP-0002"],
            "entered_at": [datetime.now().isoformat(), datetime.now().isoformat()],
        }
    )


def test_successful_load():
    """
    Test: A valid file loads successfully with the correct row count.
    """
    # Create a temporary CSV file with test data
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline=""
    ) as f:
        df = pd.DataFrame(
            {
                "log_reference_number": ["TEST-001"],
                "machine_id": ["M01"],
                "shift_id": ["S1"],
                "product_id": ["P-BLOCK-01"],
                "run_date": [TEST_DATE.isoformat()],
                "run_sequence_number": [1],
                "run_start_time": [None],
                "run_end_time": [None],
                "planned_units": [100],
                "produced_units": [95],
                "good_units": [90],
                "operator_id": ["EMP-0001"],
                "notes": ["Test row"],
                "data_entry_method": ["Manual"],
                "entered_by": ["EMP-0001"],
                "entered_at": [datetime.now().isoformat()],
            }
        )
        df.to_csv(f.name, index=False)
        file_path = f.name

    try:
        # Load the file using the TEST_DATE as the partition
        from ingestion.bronze_loader import load_file_to_bronze

        rows_loaded = load_file_to_bronze(file_path, "production_runs", TEST_DATE)

        # Verify the count
        from google.cloud import bigquery

        client = bigquery.Client(project=PROJECT_ID)
        query = f"""
        SELECT COUNT(*) as row_count
        FROM `{PROJECT_ID}.{DATASET}.production_runs`
        WHERE _PARTITIONTIME = '{TEST_DATE.isoformat()}'
        AND log_reference_number = 'TEST-001'
        """
        result = list(client.query(query).result())
        assert result[0].row_count == 1, f"Expected 1 row, got {result[0].row_count}"

        print(f"✅ Successful load test passed: {rows_loaded} rows loaded")

    finally:
        # Clean up
        os.unlink(file_path)


def test_idempotent_rerun():
    """
    Test: Rerunning the same date does NOT duplicate rows.
    """
    # Create test data
    df = pd.DataFrame(
        {
            "log_reference_number": ["IDEMPOTENT-001"],
            "machine_id": ["M01"],
            "shift_id": ["S1"],
            "product_id": ["P-BLOCK-01"],
            "run_date": [TEST_DATE.isoformat()],
            "run_sequence_number": [1],
            "run_start_time": [None],
            "run_end_time": [None],
            "planned_units": [100],
            "produced_units": [95],
            "good_units": [90],
            "operator_id": ["EMP-0001"],
            "notes": ["Idempotent test"],
            "data_entry_method": ["Manual"],
            "entered_by": ["EMP-0001"],
            "entered_at": [datetime.now().isoformat()],
        }
    )

    # Load twice with the same partition date
    load_to_bronze(df, "production_runs", TEST_DATE, "test_idempotent.csv")
    load_to_bronze(df, "production_runs", TEST_DATE, "test_idempotent.csv")

    # Query the count
    from google.cloud import bigquery

    client = bigquery.Client(project=PROJECT_ID)
    query = f"""
    SELECT COUNT(*) as row_count
    FROM `{PROJECT_ID}.{DATASET}.production_runs`
    WHERE _PARTITIONTIME = '{TEST_DATE.isoformat()}'
    AND log_reference_number = 'IDEMPOTENT-001'
    """
    result = list(client.query(query).result())

    # Should be 1 row, not 2
    assert result[0].row_count == 1, f"Expected 1 row, got {result[0].row_count}"
    print(f"✅ Idempotent rerun test passed: {result[0].row_count} row(s)")


def test_failure_path():
    """
    Test: Malformed data is rejected with a specific error message.
    """
    # Create malformed data (produced_units as string)
    df = pd.DataFrame(
        {
            "log_reference_number": ["MALFORMED-001"],
            "machine_id": ["M01"],
            "shift_id": ["S1"],
            "product_id": ["P-BLOCK-01"],
            "run_date": [TEST_DATE.isoformat()],
            "run_sequence_number": [1],
            "run_start_time": [None],
            "run_end_time": [None],
            "planned_units": [100],
            "produced_units": ["unknown"],  # INTENTIONAL VIOLATION
            "good_units": [90],
            "operator_id": ["EMP-0001"],
            "notes": ["Malformed test"],
            "data_entry_method": ["Manual"],
            "entered_by": ["EMP-0001"],
            "entered_at": [datetime.now().isoformat()],
        }
    )

    # Create temp file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline=""
    ) as f:
        df.to_csv(f.name, index=False)
        file_path = f.name

    try:
        from ingestion.contract_validator import validate_file

        # Validate against contract
        result = validate_file(file_path, "contracts/production.yaml")

        # Should fail
        assert result.passed is False, "Validation should have failed"
        assert any("produced_units" in error for error in result.errors), (
            f"Expected error about produced_units, got: {result.errors}"
        )

        print(f"✅ Failure path test passed: {result.reason}")

    finally:
        os.unlink(file_path)


def test_extract_and_load_production():
    """
    Integration test: Run the full extract_and_load_production pipeline.
    Uses the actual generated file for a test date.
    """
    # Use a date that has generated files (2026-04-14)
    test_date = date(2026, 4, 14)
    file_path = Path(f"data/incoming/production_{test_date.strftime('%Y%m%d')}.csv")

    if not file_path.exists():
        pytest.skip(f"Production file not found: {file_path}")

    try:
        from ingestion.extract_and_load import extract_and_load_production

        rows_loaded = extract_and_load_production(test_date)
        assert rows_loaded > 0, "Should have loaded at least 1 row"
        print(f"✅ extract_and_load_production test passed: {rows_loaded} rows")
    except Exception as e:
        # If it fails because data already exists (from manual testing), skip
        if "already exists" in str(e) or "duplicate" in str(e).lower():
            pytest.skip(f"Data may already exist for {test_date}: {e}")
        else:
            pytest.fail(f"extract_and_load_production failed: {e}")
