#!/usr/bin/env python3
from google.cloud import bigquery

from common.gcp import resolve_project_id

PROJECT = resolve_project_id()
CLIENT = bigquery.Client(project=PROJECT)
DATASET = "fplip_bronze"

TABLES = [
    "production_runs",
    "downtime_events",
    "qc_inspections",
]

DDLS = {
    "production_runs": '''
CREATE TABLE `{project}.{dataset}.production_runs` (
  log_reference_number STRING,
  machine_id STRING NOT NULL,
  shift_id STRING NOT NULL,
  product_id STRING NOT NULL,
  run_date DATE NOT NULL,
  run_sequence_number INT64 NOT NULL,
  run_start_time TIMESTAMP,
  run_end_time TIMESTAMP,
  planned_units INT64,
  produced_units INT64 NOT NULL,
  good_units INT64 NOT NULL,
  operator_id STRING,
  notes STRING,
  data_entry_method STRING NOT NULL,
  entered_by STRING NOT NULL,
  entered_at TIMESTAMP NOT NULL,
  _ingested_at TIMESTAMP NOT NULL,
  _source_file STRING NOT NULL
)
PARTITION BY DATE(_ingested_at)
CLUSTER BY machine_id, run_date;
''',
    "downtime_events": '''
CREATE TABLE `{project}.{dataset}.downtime_events` (
  event_id STRING NOT NULL,
  machine_id STRING NOT NULL,
  shift_id STRING NOT NULL,
  event_date DATE NOT NULL,
  reason_id STRING,
  reason_free_text STRING,
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP,
  duration_sec INT64 NOT NULL,
  data_entry_method STRING NOT NULL,
  entered_by STRING NOT NULL,
  entered_at TIMESTAMP NOT NULL,
  _ingested_at TIMESTAMP NOT NULL,
  _source_file STRING NOT NULL
)
PARTITION BY DATE(_ingested_at)
CLUSTER BY machine_id, event_date;
''',
    "qc_inspections": '''
CREATE TABLE `{project}.{dataset}.qc_inspections` (
  inspection_id STRING NOT NULL,
  machine_id STRING,
  production_run_reference STRING,
  inspection_date DATE NOT NULL,
  defect_type_id STRING,
  units_inspected INT64 NOT NULL,
  units_rejected INT64 NOT NULL,
  inspector_id STRING,
  data_entry_method STRING NOT NULL,
  entered_by STRING NOT NULL,
  entered_at TIMESTAMP NOT NULL,
  _ingested_at TIMESTAMP NOT NULL,
  _source_file STRING NOT NULL
)
PARTITION BY DATE(_ingested_at)
CLUSTER BY inspection_date;
''',
}


def main():
    print("Deleting existing tables (if any) and recreating as partitioned...")
    for t in TABLES:
        tid = f"{PROJECT}.{DATASET}.{t}"
        try:
            print(f"Deleting table {tid} (if exists)")
            CLIENT.delete_table(tid, not_found_ok=True)
        except Exception as e:
            print(f"Warning deleting {tid}: {e}")
    # Create tables
    for t in TABLES:
        ddl = DDLS[t].format(project=PROJECT, dataset=DATASET)
        print(f"Creating table {PROJECT}.{DATASET}.{t}")
        job = CLIENT.query(ddl)
        job.result()
        print("Created")

    # Verify
    print("\nVerifying partitioning status via INFORMATION_SCHEMA:")
    check_sql = f"""
SELECT table_name, partitioning_type
FROM `{PROJECT}.{DATASET}.INFORMATION_SCHEMA.TABLES`
WHERE table_name IN ({','.join([f"'{x}'" for x in TABLES])})
ORDER BY table_name
"""
    for row in CLIENT.query(check_sql):
        print(row['table_name'], row['partitioning_type'])

    print('\nDone')


if __name__ == '__main__':
    main()
