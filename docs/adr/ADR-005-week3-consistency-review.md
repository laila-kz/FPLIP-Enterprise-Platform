# ADR-005: Week 3 Consistency Review

## Status
Accepted (2026-07-24)

## Review Date
2026-07-24

## ADRs Reviewed
- ADR-001: Warehouse Selection (BigQuery Sandbox)
- ADR-002: Idempotent Bronze Loading Pattern
- ADR-003: dbt Snapshots Blocked by BigQuery Sandbox DML Restriction
- ADR-004: Hand-Rolled DDL-Only SCD2 History Tracking

## Consistency Findings

| Check | Result |
|-------|--------|
| Do all ADRs agree that BigQuery Sandbox blocks DML? | ✅ Yes — ADR-001, ADR-002, ADR-003, and ADR-004 all reference this constraint consistently |
| Is the hand-rolled SCD2 approach (ADR-004) compatible with the DML restriction? | ✅ Yes — uses only `SELECT`, `CREATE OR REPLACE TABLE AS SELECT`, and DDL |
| Does the Bronze load pattern (ADR-002) conflict with the history-tracking approach (ADR-004)? | ✅ No — Bronze uses partition-decorator `WRITE_TRUNCATE`; Silver uses DDL-only SCD2 — they operate on different layers and don't conflict |
| Is the architecture's overall DML posture consistent? | ✅ Yes — every layer (Bronze load, Silver materialization, SCD2 history) is built without `INSERT`/`UPDATE`/`DELETE`/`MERGE` |

## Cross-Week Consistency

| Week | Decision | Consistent with Others? |
|------|----------|------------------------|
| Week 1 (ADR-001) | BigQuery Sandbox with no billing | ✅ Foundation of all subsequent decisions |
| Week 2 (ADR-002) | Partition-decorator + `WRITE_TRUNCATE` for Bronze loads | ✅ Works in Sandbox (load jobs, not DML) |
| Week 3 (ADR-003) | dbt snapshots blocked by Sandbox | ✅ Confirms the constraint |
| Week 3 (ADR-004) | Hand-rolled DDL-only SCD2 | ✅ Works in Sandbox |

## Conclusion
No contradictions found. All ADRs are internally consistent and correctly reflect the Sandbox constraint.

## Date
2026-07-24