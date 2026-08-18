#!/usr/bin/env python3
import json
import pathlib
import sys
from google.oauth2 import service_account
from google.cloud import bigquery

key_path = pathlib.Path(__file__).resolve().parents[1] / 'secrets' / 'api-sa-key.json'
if not key_path.exists():
    print(json.dumps({'error': f'service account key not found at {key_path}'}))
    sys.exit(2)

creds = service_account.Credentials.from_service_account_file(str(key_path))
client = bigquery.Client(credentials=creds, project=creds.project_id)

tables = [
    'fplip_bronze.production_runs',
    'fplip_bronze.downtime_events',
    'fplip_bronze.qc_inspections',
    'fplip_gold.oee_daily',
    'fplip_gold.scrap_root_cause_summary',
]

results = {}
for t in tables:
    full = f'`{creds.project_id}.{t}`'
    try:
        q = f'SELECT COUNT(*) as c FROM {full}'
        job = client.query(q)
        rows = list(job.result())
        c = rows[0].c if rows else None
        results[t] = {'count': c}
    except Exception as e:
        results[t] = {'error': str(e)}

print(json.dumps(results, indent=2))
