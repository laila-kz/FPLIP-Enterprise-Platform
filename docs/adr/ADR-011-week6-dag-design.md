# ADR-011: Week 6 DAG Design — Three-DAG Structure

## Status
Accepted (2026-08-03)

## Context
The production orchestration layer must run Bronze ingestion, Silver/Gold transformations, and data quality verification in a GitHub Actions-friendly way without requiring a persistent Airflow scheduler or database.

## Decision
Split the pipeline into three DAGs and execute them sequentially via `airflow dags test` in an ephemeral GitHub Actions job.

### DAGs
1. `ingestion_dag`
   - Purpose: extract, validate, and load Bronze data
   - Tasks: `extract_production`, `extract_downtime`, `extract_qc`, `validate_contracts`, `load_bronze_bigquery`
2. `dbt_transform_dag`
   - Purpose: run Silver and Gold dbt transformations
   - Tasks: `dbt_run_silver`, `dbt_run_gold_oee`, `dbt_run_gold_scrap`
3. `data_quality_dag`
   - Purpose: validate output data quality
   - Tasks: `dbt_test_silver`, `dbt_test_gold`, `notify_success`

### Execution Pattern
`airflow dags test` is used for synchronous execution in CI, with DAGs chained at the shell level:

```bash
airflow dags test ingestion_dag <date> && \
airlow dags test dbt_transform_dag <date> && \
airflow dags test data_quality_dag <date>
```

### Retry Policy
```python
default_args = {
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=10),
    "execution_timeout": timedelta(minutes=10),  # per task
}
```

## Consequences
- No persistent scheduler or metadata database is required for CI.
- Limited parallelism, but the task count is low enough that sequential execution is acceptable.
- This design is well-suited to GitHub Actions ephemeral runners.

## Date
2026-08-03