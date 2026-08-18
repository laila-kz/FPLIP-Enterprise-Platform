#!/usr/bin/env python3
"""
One-time setup script for Bronze tables.
Creates time-partitioned tables in fplip_bronze with explicit schemas.
Run once as ingestion_sa.
"""

import os
import sys
from pathlib import Path

from google.cloud import bigquery
from common.gcp import resolve_project_id

# Make project root importable when running this file directly
# (so `python ingestion/setup_bronze_tables.py` works)
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import schemas
from ingestion.bronze_schema import get_schema

PROJECT_ID = resolve_project_id()
DATASET = "fplip_bronze"


def create_partitioned_table(client, table_name: str, schema):
    """
    Create a time-partitioned table in fplip_bronze.
    Uses exists_ok=True to be idempotent.
    """
    table_ref = f"{PROJECT_ID}.{DATASET}.{table_name}"

    table = bigquery.Table(table_ref, schema=schema)

    # Configure time partitioning on _ingested_at
    # table.time_partitioning = bigquery.TimePartitioning(
    #     type_=bigquery.TimePartitioningType.DAY,
    #     field="_ingested_at",
    # )

    # time partitioning should only be set for transactional tables :
    # Configure time partitioning ONLY for transactional tables
    if table_name in ["production_runs", "downtime_events", "qc_inspections"]:
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="_ingested_at",
        )

    # Set clustering for common query patterns
    # table.clustering_fields = ["machine_id", "run_date"] \
    #     if table_name == "production_runs" else ["machine_id", "event_date"] \
    #     if table_name == "downtime_events" else ["inspection_date"]

    # Set clustering for common query patterns (only for transactional tables)
    if table_name == "production_runs":
        table.clustering_fields = ["machine_id", "run_date"]
    elif table_name == "downtime_events":
        table.clustering_fields = ["machine_id", "event_date"]
    elif table_name == "qc_inspections":
        table.clustering_fields = ["inspection_date"]
    else:
        # Master tables don't need clustering
        table.clustering_fields = None
    try:
        # If table exists, inspect partitioning. BigQuery does not allow
        # changing partitioning on an existing table, so if the table exists
        # but is not partitioned, delete and recreate it.
        try:
            existing = client.get_table(table_ref)
            # existing.time_partitioning is None for non-partitioned tables
            if (
                table_name in ["production_runs", "downtime_events", "qc_inspections"]
                and existing.time_partitioning is None
            ):
                print(f"⚠️ Existing table {table_ref} is not partitioned — recreating as partitioned table")
                client.delete_table(table_ref, not_found_ok=True)
                table = client.create_table(table)
            else:
                # Table exists and is partitioned (or master table); confirm
                print(f"✅ Confirmed existing table: {table_ref}")
                if existing.time_partitioning:
                    print("   Partitioned by: DAY on _ingested_at")
                if existing.clustering_fields:
                    print(f"   Clustered by: {existing.clustering_fields}")
        except Exception:
            # Table does not exist — create it
            table = client.create_table(table)
            print(f"✅ Created table: {table_ref}")
            if table.time_partitioning:
                print("   Partitioned by: DAY on _ingested_at")
            if table.clustering_fields:
                print(f"   Clustered by: {table.clustering_fields}")

        return True
    except Exception as e:
        print(f"❌ Failed to create or recreate {table_ref}: {e}")
        return False


def main():
    """Create all three Bronze tables."""
    # Set credentials
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        print("⚠️  GOOGLE_APPLICATION_CREDENTIALS not set")
        print(
            "   Run: export GOOGLE_APPLICATION_CREDENTIALS="
            "secrets/ingestion-sa-key.json"
        )
        return 1

    print(f"Using credentials: {creds_path}")
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET}")
    print("=" * 50)

    client = bigquery.Client(project=PROJECT_ID)

    # Create each table
    # In setup_bronze_tables.py, update the tables list:
    tables = [
        ("production_runs", get_schema("production_runs")),
        ("downtime_events", get_schema("downtime_events")),
        ("qc_inspections", get_schema("qc_inspections")),
        ("machines", get_schema("machines")),
        ("products", get_schema("products")),
        ("shifts", get_schema("shifts")),
        ("downtime_reasons", get_schema("downtime_reasons")),
        ("defect_types", get_schema("defect_types")),
    ]

    success_count = 0
    for table_name, schema in tables:
        print(f"\nCreating {table_name}...")
        if create_partitioned_table(client, table_name, schema):
            success_count += 1

    print("\n" + "=" * 50)
    print(f"✅ {success_count}/{len(tables)} tables created successfully")

    if success_count == len(tables):
        print("🎉 All Bronze tables are ready for ingestion!")
        return 0
    else:
        print("⚠️  Some tables failed to create. Check the errors above.")
        return 1


if __name__ == "__main__":
    exit(main())
