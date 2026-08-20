"""
Bronze table schemas for FPLIP Week 2.
Each schema matches its corresponding YAML contract exactly.
"""

from google.cloud import bigquery


def production_runs_schema():
    """
    Schema for fplip_bronze.production_runs.
    Matches contracts/production.yaml.
    """
    return [
        bigquery.SchemaField("log_reference_number", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("machine_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("shift_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("product_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("run_date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("run_sequence_number", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("run_start_time", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("run_end_time", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("planned_units", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("produced_units", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("good_units", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("operator_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("notes", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("data_entry_method", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("entered_by", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("entered_at", "TIMESTAMP", mode="REQUIRED"),
        # Metadata columns (added during load)
        bigquery.SchemaField("_ingested_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("_source_file", "STRING", mode="REQUIRED"),
    ]


def downtime_events_schema():
    """
    Schema for fplip_bronze.downtime_events.
    Matches contracts/downtime.yaml.
    """
    return [
        bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("machine_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("shift_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("event_date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("reason_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("reason_free_text", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("start_time", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("end_time", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("duration_sec", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("data_entry_method", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("entered_by", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("entered_at", "TIMESTAMP", mode="REQUIRED"),
        # Metadata columns
        bigquery.SchemaField("_ingested_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("_source_file", "STRING", mode="REQUIRED"),
    ]


def qc_inspections_schema():
    """
    Schema for fplip_bronze.qc_inspections.
    Matches contracts/qc.yaml.
    """
    return [
        bigquery.SchemaField("inspection_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("machine_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("production_run_reference", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("inspection_date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("defect_type_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("units_inspected", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("units_rejected", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("inspector_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("data_entry_method", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("entered_by", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("entered_at", "TIMESTAMP", mode="REQUIRED"),
        # Metadata columns
        bigquery.SchemaField("_ingested_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("_source_file", "STRING", mode="REQUIRED"),
    ]


def get_schema(table_name: str):
    """Return the schema for a given table name."""
    schemas = {
        "production_runs": production_runs_schema,
        "downtime_events": downtime_events_schema,
        "qc_inspections": qc_inspections_schema,
        "machines": machines_schema,
        "products": products_schema,
        "shifts": shifts_schema,
        "downtime_reasons": downtime_reasons_schema,
        "defect_types": defect_types_schema,
    }
    return schemas[table_name]()


def machines_schema():
    """Schema for fplip_bronze.machines (master data)."""
    return [
        bigquery.SchemaField("machine_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("machine_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("machine_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("line_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("location", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("manufacturer", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("install_date", "DATE", mode="NULLABLE"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
        bigquery.SchemaField(
            "nominal_capacity_units_per_hour", "INTEGER", mode="NULLABLE"
        ),
        bigquery.SchemaField("data_entry_method", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("last_updated_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("last_updated_by", "STRING", mode="NULLABLE"),
        # Metadata
        bigquery.SchemaField("_ingested_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("_source_file", "STRING", mode="REQUIRED"),
    ]


def products_schema():
    """Schema for fplip_bronze.products (master data)."""
    return [
        bigquery.SchemaField("product_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("product_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("product_family", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("unit_of_measure", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("standard_cycle_time_sec", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("cycle_time_source", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("cycle_time_confidence", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("standard_weight_kg", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("active_flag", "BOOLEAN", mode="REQUIRED"),
        bigquery.SchemaField("data_entry_method", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("last_updated_at", "TIMESTAMP", mode="REQUIRED"),
        # Metadata
        bigquery.SchemaField("_ingested_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("_source_file", "STRING", mode="REQUIRED"),
    ]


def shifts_schema():
    """Schema for fplip_bronze.shifts (master data)."""
    return [
        bigquery.SchemaField("shift_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("shift_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("start_time", "TIME", mode="REQUIRED"),
        bigquery.SchemaField("end_time", "TIME", mode="REQUIRED"),
        bigquery.SchemaField("crosses_midnight", "BOOLEAN", mode="REQUIRED"),
        bigquery.SchemaField("active_flag", "BOOLEAN", mode="REQUIRED"),
        # Metadata
        bigquery.SchemaField("_ingested_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("_source_file", "STRING", mode="REQUIRED"),
    ]


def downtime_reasons_schema():
    """Schema for fplip_bronze.downtime_reasons (master data)."""
    return [
        bigquery.SchemaField("reason_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("reason_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("reason_category", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("oee_loss_category", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("description", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("active_flag", "BOOLEAN", mode="REQUIRED"),
        # Metadata
        bigquery.SchemaField("_ingested_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("_source_file", "STRING", mode="REQUIRED"),
    ]


def defect_types_schema():
    """Schema for fplip_bronze.defect_types (master data)."""
    return [
        bigquery.SchemaField("defect_type_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("defect_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("defect_category", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("severity", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("description", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("active_flag", "BOOLEAN", mode="REQUIRED"),
        # Metadata
        bigquery.SchemaField("_ingested_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("_source_file", "STRING", mode="REQUIRED"),
    ]
