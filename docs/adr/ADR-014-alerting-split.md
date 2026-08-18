# ADR-014: Slack Alerting Split (Airflow Callback + Workflow Backstop)

## Status
Accepted (2026-08-05)

## Decision
Slack alerting is implemented at two levels:

### Level 1: Airflow `on_failure_callback` (Task-Level)
- Fires per-task when a task exhausts its retries
- Provides task-level detail (which DAG, which task, error message)
- Implemented in `data_quality_dag.py` via `notify_failure` callback

### Level 2: GitHub Actions `if: failure()` (Workflow-Level)
- Fires when any step in the workflow fails
- Catches failures before Airflow runs (e.g., setup errors, import errors)
- Implemented in `production-schedule.yml` as a backstop

## Reasoning
- The two mechanisms cover different failure surfaces
- `on_failure_callback` catches DAG-level failures (e.g., `dbt test` failing)
- Workflow-level catches infrastructure failures (e.g., Python import error, setup failure)

## Implementation
- Shared `slack_alert.py` helper for both paths
- `notify_success` task for success messages
- `if: failure()` step in `production-schedule.yml`

## Verification
- Deliberate break tests confirmed both paths work
- Production run confirmed success notification works

## Date
2026-08-05