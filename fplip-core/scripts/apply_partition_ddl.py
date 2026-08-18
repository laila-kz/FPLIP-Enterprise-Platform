#!/usr/bin/env python3
from google.cloud import bigquery
from common.gcp import resolve_project_id

PROJECT = resolve_project_id()
client = bigquery.Client(project=PROJECT)

queries = [
  f'''CREATE OR REPLACE TABLE `{PROJECT}.fplip_bronze.production_runs` (
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
CLUSTER BY machine_id, run_date;''',
    f'''CREATE OR REPLACE TABLE `{PROJECT}.fplip_bronze.downtime_events` (
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
CLUSTER BY machine_id, event_date;''',
    f'''CREATE OR REPLACE TABLE `{PROJECT}.fplip_bronze.qc_inspections` (
  inspection_id STRING NOT NULL,
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
CLUSTER BY inspection_date;'''
]

for q in queries:
    print('Applying DDL...')
      job = client.query(q)
    job.result()
    print('Applied')

print('\nVerifying partitioning:')
check_sql = f'''
SELECT table_name, partitioning_type
FROM `{PROJECT}.fplip_bronze.INFORMATION_SCHEMA.TABLES`
WHERE table_name IN ('production_runs','downtime_events','qc_inspections')
ORDER BY table_name
'''
rows = client.query(check_sql)
for r in rows:
    print(r['table_name'], r['partitioning_type'])

print('\nDone')
