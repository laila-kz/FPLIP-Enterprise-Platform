# ADR-013: Airflow Executor Choice for Production

## Status
Accepted (2026-08-05)

## Decision
Use `airflow dags test` with `SequentialExecutor` (via GitHub Actions runner), not `LocalExecutor` with a persistent Postgres database.

## Reasoning
- `LocalExecutor` requires a real database backend (Postgres) for task coordination
- This project runs in an ephemeral GitHub Actions job — no persistent infrastructure
- `SequentialExecutor` with SQLite is simpler, faster to bootstrap, and sufficient for this task count (3 DAGs, ~8 tasks total)

## Tradeoffs
- Pros: No persistent infrastructure, zero cost, simple setup, fast bootstrap
- Cons: No parallel task execution (but task count is low, so this doesn't matter)

## Implementation
- DAGs are chained at the shell level via `run_pipeline.sh`
- Each DAG runs via `airflow dags test` (synchronous, in-process execution)
- No scheduler or webserver running in production
- Airflow metadata stored in SQLite (ephemeral, per-run)

## Performance
- Verified execution time: ~6m 38s (well within GitHub Actions limits)

## Date
2026-08-05