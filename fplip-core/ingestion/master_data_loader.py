#!/usr/bin/env python3
"""
Master data loader for FPLIP Week 3.
Loads master data using full-table WRITE_TRUNCATE (no partition decorator).
"""

from datetime import datetime, timezone

import pandas as pd
from google.cloud import bigquery
from common.gcp import resolve_project_id

from ingestion.bronze_schema import get_schema

PROJECT_ID = resolve_project_id()
DATASET = "fplip_bronze"


def coerce_dataframe_types(df: pd.DataFrame, schema: list) -> pd.DataFrame:
    """
    Coerces DataFrame column types to match BigQuery schema expectations.
    Supports DATE, TIMESTAMP, and TIME.
    """
    for field in schema:
        col_name = field.name
        col_type = field.field_type.upper()

        if col_name not in df.columns:
            continue

        if col_type == "DATE":
            df[col_name] = pd.to_datetime(df[col_name]).dt.date
        elif col_type == "TIMESTAMP":
            df[col_name] = pd.to_datetime(df[col_name], utc=True)
        elif col_type == "TIME":
            df[col_name] = pd.to_datetime(df[col_name], format="%H:%M:%S").dt.time

    return df


def load_master_data(dataframe: pd.DataFrame, table_name: str, source_file: str):
    """
    Load master data using full-table WRITE_TRUNCATE.
    No partition decorator — this replaces the entire table.
    """
    client = bigquery.Client(project=PROJECT_ID)

    # Get BigQuery schema definition
    schema = get_schema(table_name)

    # Add metadata columns
    df = dataframe.copy()
    df["_ingested_at"] = datetime.now(timezone.utc)
    df["_source_file"] = str(source_file)

    # Automatically convert string columns to correct pandas datetime/date/time types
    df = coerce_dataframe_types(df, schema)

    # Full table name (no partition decorator)
    destination = f"{PROJECT_ID}.{DATASET}.{table_name}"

    # Configure load job
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    # Execute load job
    load_job = client.load_table_from_dataframe(df, destination, job_config=job_config)
    load_job.result()

    print(f"✅ Loaded {len(df)} rows into {destination}")
    return len(df)


def load_master_file(file_path: str, table_name: str):
    """Load a CSV file into a master Bronze table."""
    df = pd.read_csv(file_path)
    return load_master_data(df, table_name, file_path)
