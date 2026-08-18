# ADR-003: dbt Snapshots Blocked by BigQuery Sandbox DML Restriction

## Status
Accepted (2026-07-24)

## Context
We need to implement SCD Type 2 history-tracking for `dim_machine` and `dim_product` as specified in the frozen blueprint. The recommended dbt approach is using `dbt snapshot`, which depends on `MERGE` statements for its second and subsequent runs.

## Test Performed
A throwaway spike was executed with:
- dbt version: 1.12.0
- dbt-bigquery adapter: 1.12.0
- Target: `flip-dev-503300` (BigQuery Sandbox mode, no billing account linked)

### First Run (CREATE TABLE)
```bash
dbt snapshot --select spike_snapshot
```
**Result:** ✅ Success. The first run issued `CREATE OR REPLACE TABLE ... AS SELECT` (DDL, allowed in Sandbox).

### Second Run (MERGE)
After modifying the source seed data and rerunning with `--debug`:
```bash
dbt snapshot --select spike_snapshot --debug
```
**Result:** ❌ Failed with the following error:
```
Database Error in snapshot spike_snapshot (snapshots\spike_snapshot.sql)
Billing has not been enabled for this project. Enable billing at https://console.cloud.google.com/billing. 
DML queries are not allowed in the free tier. Set up a billing account to remove this restriction.
```

### Literal SQL Attempted
The `--debug` output shows dbt attempted to execute:
```sql
merge into `flip-dev-503300`.`fplip_silver`.`spike_snapshot` as DBT_INTERNAL_DEST
using `flip-dev-503300`.`fplip_silver`.`spike_snapshot__dbt_tmp115838700790` as DBT_INTERNAL_SOURCE
on DBT_INTERNAL_SOURCE.dbt_scd_id = DBT_INTERNAL_DEST.dbt_scd_id
when matched 
   and DBT_INTERNAL_DEST.dbt_valid_to is null 
   and DBT_INTERNAL_SOURCE.dbt_change_type in ('update', 'delete')
    then update
    set dbt_valid_to = DBT_INTERNAL_SOURCE.dbt_valid_to
when not matched
   and DBT_INTERNAL_SOURCE.dbt_change_type = 'insert'
    then insert (`id`, `status`, `updated_at`, `dbt_updated_at`, `dbt_valid_from`, `dbt_valid_to`, `dbt_scd_id`)
    values (`id`, `status`, `updated_at`, `dbt_updated_at`, `dbt_valid_from`, `dbt_valid_to`, `dbt_scd_id`)
```

## Decision
**dbt snapshots are NOT compatible with BigQuery Sandbox mode** due to their reliance on `MERGE` statements for SCD2 history-tracking.

## Options Moving Forward

### Option A: Full-Refresh, Current-State-Only Dimensions
Accept `dim_machine` and `dim_product` as current-state-only tables (no history-tracking). History would be explicitly deferred, not silently dropped.
- **Pros:** Simple, works with Sandbox, requires no custom code
- **Cons:** Loses the SCD2 history requirement from the blueprint

### Option B: Hand-Rolled DDL-Only History Mechanism
Implement a custom SCD2 mechanism using only DDL and `SELECT` statements (no `MERGE`), using a `CREATE OR REPLACE TABLE AS SELECT` pattern that preserves history by unioning previous state with current changes.
- **Pros:** Preserves SCD2 history, works within Sandbox restrictions
- **Cons:** More complex, requires custom SQL logic, needs careful verification

## Chosen Path
**Option B: Hand-Rolled DDL-Only History Mechanism**

**Reasoning:** The blueprint explicitly requires SCD2 history-tracking for `dim_machine` and `dim_product`. While Option A would be simpler, it would violate a core architectural requirement. The hand-rolled approach, while more work, preserves the history-tracking capability while staying within Sandbox constraints.

## Implementation Approach (To Be Built on Day 4)
The DDL-only SCD2 mechanism will use:
1. A current-state snapshot view (`_current_machine_snapshot`) timestamped with `CURRENT_TIMESTAMP()`
2. A history table (`dim_machine_history`) built via `CREATE OR REPLACE TABLE AS SELECT` that:
   - Preserves unchanged rows from previous history
   - Closes out rows that changed (sets `valid_to`)
   - Inserts new current versions with `valid_to = NULL`
3. A final `dim_machine` view/table that filters to `is_current = TRUE`

## Verification Plan (To Be Executed on Day 4)
The hand-rolled mechanism will be verified by:
1. Manually changing a machine's `line_id` in the source data
2. Rerunning the master-data loader and the history refresh
3. Querying the history table to confirm:
   - Old row closed (`valid_to` populated)
   - New row open (`valid_to = NULL`) with updated attributes
   - All other rows unchanged

## Related Documents
- ADR-001: Warehouse Selection (BigQuery Sandbox)
- ADR-002: Idempotent Bronze Loading Pattern

## Date
2026-07-24