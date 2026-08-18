#!/usr/bin/env python3
"""
Idempotent Bronze loader for FPLIP Week 2.
Uses partition-decorator + WRITE_TRUNCATE for idempotent loads.
"""

from datetime import datetime, timezone

import socket
import traceback

import pandas as pd
from google.cloud import bigquery
from common.gcp import resolve_project_id
from google.api_core import exceptions as google_exceptions

# Import schemas
from ingestion.bronze_schema import get_schema

PROJECT_ID = resolve_project_id()
DATASET = "fplip_bronze"


def load_to_bronze(
    dataframe: pd.DataFrame, table_name: str, target_date, source_file: str
):
    """
    Load a DataFrame into a Bronze table using partition-decorator + WRITE_TRUNCATE.

    This is the core idempotent load pattern:
    - Uses partition decorator (table$YYYYMMDD) to target a specific date partition
    - Uses WRITE_TRUNCATE to replace that partition's contents entirely
    - Never uses DML (INSERT/UPDATE/DELETE/MERGE), so it works in BigQuery Sandbox

    Args:
        dataframe: Pandas DataFrame to load
        table_name: Name of the table (e.g., "production_runs")
        target_date: Date of the data (will be used for partition decorator)
        source_file: Path to the source file (for _source_file metadata)

    Returns:
        int: Number of rows loaded
    """
    client = bigquery.Client(project=PROJECT_ID)

    # Defensive network timeout applied to socket operations that can otherwise
    # hang inside google-resumable-media during multipart uploads. We set a
    # conservative global socket timeout for the duration of the upload and
    # restore the previous value afterwards.
    UPLOAD_SOCKET_TIMEOUT = 120  # seconds
    JOB_RESULT_TIMEOUT = 120  # seconds to wait for the load job to finish
    prev_socket_timeout = socket.getdefaulttimeout()

    # Add metadata columns
    df = dataframe.copy()
    # Record the actual ingestion time so source freshness checks
    # reflect when data arrived.
    #df["_ingested_at"] = datetime.now(timezone.utc)
    # Use the target date for partitioning, not current timestamp
    df["_ingested_at"] = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)

    df["_source_file"] = str(source_file)

    # ----- : Convert date columns -----
    # Ensure run_date is date type (not string)
    if "run_date" in df.columns:
        df["run_date"] = pd.to_datetime(df["run_date"]).dt.date

    if "event_date" in df.columns:
        df["event_date"] = pd.to_datetime(df["event_date"]).dt.date

    if "inspection_date" in df.columns:
        df["inspection_date"] = pd.to_datetime(df["inspection_date"]).dt.date

    # Also ensure timestamp columns are datetime
    timestamp_cols = [
        "run_start_time",
        "run_end_time",
        "entered_at",
        "start_time",
        "end_time",
    ]
    for col in timestamp_cols:
        if col in df.columns and df[col].notna().any():
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Build partition decorator: table$YYYYMMDD
    partition_suffix = target_date.strftime("%Y%m%d")
    destination = f"{PROJECT_ID}.{DATASET}.{table_name}${partition_suffix}"

    # Get schema for the table
    schema = get_schema(table_name)

    # Configure load job
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        time_partitioning=bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="_ingested_at",
        ),
        # ADD CLUSTERING to match the table
        clustering_fields=["machine_id", "run_date"]
        if table_name == "production_runs"
        else ["machine_id", "event_date"]
        if table_name == "downtime_events"
        else ["inspection_date"],
    )
    # Fail fast on any schema / row issues during CI
    job_config.max_bad_records = 0

    # Execute load job with defensive timeouts and error handling.
    try:
        socket.setdefaulttimeout(UPLOAD_SOCKET_TIMEOUT)
        print(f"⏳ Starting BigQuery load to {destination} (socket timeout={UPLOAD_SOCKET_TIMEOUT}s)")
        load_job = client.load_table_from_dataframe(df, destination, job_config=job_config)

        # Wait for job completion but fail fast if it exceeds JOB_RESULT_TIMEOUT
        load_job.result(timeout=JOB_RESULT_TIMEOUT)

        print(f"✅ Loaded {len(df)} rows into {destination}")
        return len(df)
    except google_exceptions.GoogleAPICallError as ge:
        # BigQuery / network API error - bubble up with context
        print("❌ BigQuery API call error during load:")
        print(ge)
        traceback.print_exc()
        raise
    except google_exceptions.RetryError as re:
        print("❌ BigQuery retry error during load:")
        print(re)
        traceback.print_exc()
        raise
    except Exception as e:
        # Catch broad exceptions (including socket timeouts) and re-raise so
        # Airflow / CI can fail fast instead of hanging for hours.
        print("❌ Unexpected error during BigQuery load:")
        print(e)
        traceback.print_exc()
        raise
    finally:
        # Restore previous global socket timeout
        socket.setdefaulttimeout(prev_socket_timeout)


def load_file_to_bronze(file_path: str, table_name: str, target_date):
    """
    Load a CSV file into a Bronze table.
    Wraps load_to_bronze with file reading.
    """
    df = pd.read_csv(file_path)
    return load_to_bronze(df, table_name, target_date, file_path)
