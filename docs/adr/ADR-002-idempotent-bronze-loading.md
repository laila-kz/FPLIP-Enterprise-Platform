# ADR-002: Idempotent Bronze Loading Pattern

## Status
Accepted (2026-07-23)

## Context
We need to load daily batch data into BigQuery Bronze tables with the following requirements:
- Data must be safely rerunnable (reprocessing a past date should not duplicate data)
- The solution must work within BigQuery Sandbox's DML restrictions
- The solution must be compatible with the medallion architecture

## Problem Statement
BigQuery Sandbox blocks DML statements (`INSERT`, `UPDATE`, `DELETE`, `MERGE`). A naive `WRITE_APPEND` load would duplicate data on any rerun. We needed a pattern that:
1. Works without DML
2. Is idempotent (safe to rerun)
3. Is operationally simple

## Decision
Use **partition-decorator + `WRITE_TRUNCATE` load jobs**.

### Implementation Details
```python
destination = f"{PROJECT_ID}.{DATASET}.{table_name}${partition_suffix}"
job_config = LoadJobConfig(
    write_disposition=WriteDisposition.WRITE_TRUNCATE,
)
load_job = client.load_table_from_dataframe(df, destination, job_config=job_config)
```

## Date
2026-07-23