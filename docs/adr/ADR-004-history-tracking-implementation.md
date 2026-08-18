# ADR-004: Hand-Rolled DDL-Only SCD2 History Tracking

## Status
Accepted (2026-07-24)

## Context
BigQuery Sandbox blocks DML statements (`INSERT`, `UPDATE`, `DELETE`, `MERGE`). The recommended dbt snapshot approach for SCD Type 2 history tracking depends on `MERGE` and is therefore incompatible with the environment.

## Problem Statement
We must preserve SCD2 history for `dim_machine` and `dim_product` as required by the blueprint, while remaining fully compatible with Sandbox restrictions.

## Decision
Implement a hand-rolled, DDL-only SCD2 history mechanism using `CREATE OR REPLACE TABLE AS SELECT` and history preservation logic.

## Rationale
1. **Sandbox compatibility:** DML is blocked, so dbt snapshot and merge-based approaches cannot be used.
2. **History requirement:** The blueprint explicitly requires history-tracking for key dimensions.
3. **Controlled complexity:** A custom DDL-only solution preserves history while keeping the implementation explicit and auditable.

## Implementation
- Use `CREATE OR REPLACE TABLE AS SELECT` to rebuild dimension history tables on each run.
- Preserve unchanged rows from the previous version.
- Close out changed rows by setting `valid_to`.
- Insert new current versions with `valid_to = NULL`.
- Provide a current-state view or table filtered to `valid_to IS NULL` for joins.

## Consequences
- Requires custom SQL logic instead of standard dbt snapshot semantics.
- History refresh is fully idempotent and compatible with Sandbox.
- Dimension joins remain simple because the current dimension can be represented as Type 1 for Gold.

## Related ADRs
- ADR-001: Warehouse Selection (BigQuery Sandbox)
- ADR-002: Idempotent Bronze Loading Pattern
- ADR-003: dbt Snapshots Blocked by BigQuery Sandbox DML Restriction

## Date
2026-07-24
