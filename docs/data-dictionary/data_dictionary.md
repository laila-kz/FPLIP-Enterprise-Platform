# FPLIP Data Dictionary — Silver Layer

## Overview
This document describes the business meaning of each column in the Silver layer dimensions, beyond what the schema itself provides.

---

## `dim_machine`

**Purpose:** Current state of each production machine (history available in `dim_machine_history`).

| Column | Business Meaning |
|--------|------------------|
| `machine_id` | Natural key used by operators on the shop floor (e.g., "M01") |
| `machine_name` | Display name shown in dashboards |
| `machine_type` | Equipment category used for benchmarking (Block Press, Tile Press, Mixer, Curing Chamber, Other) |
| `line_id` | Production line the machine belongs to (L1, L2, etc.) — null if unassigned |
| `location` | Physical location in the factory (e.g., "Building A - Bay 2") |
| `manufacturer` | Equipment manufacturer (Masa Group, Hess, etc.) |
| `install_date` | Date the machine entered service — use for age/depreciation analysis |
| `status` | Current operational status: Active, Inactive, Maintenance, Decommissioned |
| `nominal_capacity_units_per_hour` | Nameplate rated capacity — cross-check against `standard_cycle_time_sec` for plausibility |
| `data_entry_method` | How this record was captured (Manual, ERP Export, Machine Export) — affects trust/lineage |
| `last_updated_at` | Last modification timestamp — drives SCD2 versioning |
| `valid_from` | Timestamp when this version became the active version |
| `valid_to` | Timestamp when this version was superseded — null means current version |
| `is_current` | True if this is the current version of the machine |

---

## `dim_machine_history`

**Purpose:** Full SCD2 history of all machine changes (all versions).

**Same columns as `dim_machine`, plus:**
- Every change to a machine's attributes creates a new row
- Old rows get `valid_to` populated (the time of the change)
- New rows get `valid_to = null` and `is_current = true`

**Business Use:** This table powers trend analysis ("how many machines were active in Q1?") and point-in-time joins ("what was machine M01's line_id on April 14?").

---

## `dim_product`

**Purpose:** Current state of each product/SKU (history available in `dim_product_history`).

| Column | Business Meaning |
|--------|------------------|
| `product_id` | Natural key (e.g., P-BLOCK-01) |
| `product_name` | Display name for dashboards |
| `product_family` | High-level grouping for benchmarking (Concrete Block, Pavement Block, Zellige, Other) |
| `unit_of_measure` | Unit counted in (unit, m2, piece) — determines dashboard labels |
| `standard_cycle_time_sec` | Expected time (seconds) to produce one unit under normal conditions — **HIGHEST RISK FIELD** |
| `cycle_time_source` | Where the cycle time came from (Manufacturer Spec, Manufacturing Engineering Estimate, Historical Average, Unconfirmed) |
| `cycle_time_confidence` | **CRITICAL FIELD** — Confidence tag for trusting OEE calculations: |
| | - `verified`: Cycle time has been confirmed against real production data |
| | - `estimated`: Cycle time is an engineering estimate, not yet verified |
| | - `unconfirmed`: Cycle time is unverified — OEE numbers using this product should be flagged as provisional |
| `standard_weight_kg` | Nominal unit weight (optional, used for future cost module) |
| `active_flag` | True if product is currently in production — false means discontinued |
| `valid_from` | Timestamp when this version became active |
| `valid_to` | Timestamp when superseded — null means current |
| `is_current` | True if current version |

**⚠️ Important:** If you see an unexpectedly high or low OEE number for a product, **check `cycle_time_confidence` first**. An `unconfirmed` cycle time is the most likely cause of a skewed OEE Performance component.

---

## `dim_product_history`

**Purpose:** Full SCD2 history of all product changes (all versions).

**Same columns as `dim_product`, plus:** History of changes to any product attribute, including cycle time revisions.

**Business Use:** Track when a product's cycle time was revised — critical for understanding OEE trend shifts.

---

## `dim_shift`

**Purpose:** Shift pattern definitions.

| Column | Business Meaning |
|--------|------------------|
| `shift_id` | Unique shift identifier (S1, S2, S3) |
| `shift_name` | Display name (Morning, Afternoon, Night) |
| `start_time` | Shift start in local time (06:00:00, 14:00:00, 22:00:00) |
| `end_time` | Shift end in local time |
| `crosses_midnight` | True if shift spans two calendar dates (Night shift) |
| `active_flag` | True if currently in use |

**Business Use:** Every production run and downtime event is associated with a shift — this dimension provides the shift window for Availability calculation.

---

## `dim_date`

**Purpose:** Calendar date spine — one row per day.

| Column | Business Meaning |
|--------|------------------|
| `date_day` | Calendar date |
| `year` | Year (e.g., 2026) |
| `month` | Month number (1-12) |
| `day` | Day of month (1-31) |
| `day_of_week` | Day name (Monday, Tuesday, etc.) |
| `month_name` | Month name (January, February, etc.) |
| `quarter` | Quarter number (1-4) |
| `is_weekend` | True if Saturday or Sunday |

**Business Use:** Every fact table joins to `dim_date` on its date field — enables time-based aggregations (weekly, monthly, quarterly).

**Date Range:** 2026-01-01 through 2028-01-01 (covers all synthetic data and future room).

---

## `dim_defect_type`

**Purpose:** Standardized defect classification taxonomy.

| Column | Business Meaning |
|--------|------------------|
| `defect_type_id` | Unique defect code (e.g., DEF-CRACK) |
| `defect_name` | Display name for dashboards |
| `defect_category` | High-level grouping for Pareto analysis (Dimensional, Visual, Structural, Material, Other) |
| `severity` | Defect severity for prioritization: Minor, Major, Critical |
| `description` | Extended explanation for QC staff |
| `active_flag` | True if currently assignable |

**Business Use:** QC Inspection Log joins to this dimension — enables root-cause analysis by defect type.

---

## `dim_downtime_reason`

**Purpose:** Standardized stop-reason taxonomy.

| Column | Business Meaning |
|--------|------------------|
| `reason_id` | Unique reason code (e.g., DT-CHG-01) |
| `reason_name` | Display name for dashboards |
| `reason_category` | High-level grouping for Pareto analysis (Planned, Unplanned, Changeover, Maintenance, Material Shortage, Other) |
| `oee_loss_category` | **CRITICAL FIELD** — Which OEE component this reason affects: |
| | - `Availability Loss`: Counts against machine availability (e.g., breakdown, changeover) |
| | - `Performance Loss`: Counts against machine performance (e.g., running below ideal speed) |
| | - `Not Applicable`: Doesn't affect OEE (e.g., "Other" reasons) |
| `description` | Extended explanation for maintenance staff |
| `active_flag` | True if currently assignable |

**⚠️ Important:** Without `oee_loss_category`, OEE calculations would misattribute downtime reasons. This field resolves the ambiguity between availability-based and performance-based losses.

---

## Data Lineage

Run `dbt docs serve` to see the full lineage graph.

Key paths:

Bronze → Staging → Silver Dimensions

products → stg_products → dim_product (via dim_product_history)
machines → stg_machines → dim_machine (via dim_machine_history)
shifts → stg_shifts → dim_shift
downtime_reasons → stg_downtime_reasons → dim_downtime_reason
defect_types → stg_defect_types → dim_defect_type


**History Tracking (SCD2):**

machines → stg_machines → _current_machine_snapshot → dim_machine_history → dim_machine (current only)
products → stg_products → _current_product_snapshot → dim_product_history → dim_product (current only)


The history tables (`dim_*_history`) contain all versions. The final dimensions (`dim_*`) filter to `is_current = true`.

---

## Testing Coverage

All six dimensions have tests in `models/silver/dims/schema.yml`:
- `unique` + `not_null` on all primary keys
- `accepted_values` on all categorical fields
- Data quality gates enforced at model build time

To run tests:
```bash
dbt test
dbt test --select silver.dims
``` 

**Verify:**
- Read each entry back as someone with no other context.
- Would they understand what `cycle_time_confidence = unconfirmed` actually implies for trusting a specific OEE number?

**Common mistake:** Documenting only column names and types (which `dbt docs` already provides) without the business-meaning layer.

---

### TASK 3 — ADR Consistency Review

**What / Purpose:** Confirm this week's decisions (ADR-003, ADR-004) don't quietly contradict earlier ones (ADR-001, ADR-002).

**Steps / Expected output:**

**1. Read all four ADRs in sequence:**

```powershell
cat docs/adr/ADR-001-warehouse-selection.md
cat docs/adr/ADR-002-idempotent-bronze-loading.md
cat docs/adr/ADR-003-scd2-blocked-by-sandbox-dml.md
cat docs/adr/ADR-004-history-tracking-implementation.md

## Fact Tables

### `fct_production_run`

**Purpose:** Production run facts — one row per (machine, shift, product, date, run_sequence_number)

| Column | Description |
|--------|-------------|
| `run_id` | Surrogate key |
| `machine_id` | Machine that ran |
| `shift_id` | Shift during the run |
| `product_id` | Product produced |
| `run_date` | Calendar date |
| `run_sequence_number` | Distinguishes multiple runs on same machine/shift/product/day |
| `produced_units` | Total units produced |
| `good_units` | Units meeting spec |
| `scrap_units` | Units scrapped (produced - good) |
| `attainment_rate` | produced / planned_units |

### `fct_downtime_event`

**Purpose:** Downtime event facts — one row per machine stop

| Column | Description |
|--------|-------------|
| `event_id` | Surrogate key |
| `machine_id` | Machine that stopped |
| `shift_id` | Shift when stopped |
| `event_date` | Calendar date |
| `reason_id` | Standardized reason (nullable by design) |
| `reason_free_text` | Raw text (populated when reason_id is null) |
| `duration_sec` | Stop duration |

### `fct_qc_inspection`

**Purpose:** QC inspection facts — one row per inspection batch

| Column | Description |
|--------|-------------|
| `inspection_id` | Surrogate key |
| `production_run_reference` | Link to production run (nullable by design) |
| `inspection_date` | Calendar date |
| `defect_type_id` | Defect found (nullable for passed inspections) |
| `units_inspected` | Units inspected |
| `units_rejected` | Units failing inspection |
| `rejection_rate` | rejected / inspected |

### Test Severity Notes

The following relationships use `severity: warn` (not `error`):
- `fct_downtime_event.reason_id` → `dim_downtime_reason` (unmapped reasons are valid by design)
- `fct_qc_inspection.production_run_reference` → `fct_production_run` (inspections may not always tie to a run)
- `fct_qc_inspection.defect_type_id` → `dim_defect_type` (passed inspections have no defect)

All other relationships use `severity: error`.


## Gold Layer — OEE Daily

### `oee_daily`

**Purpose:** OEE Daily — one row per machine per shift per day. Computes Availability, Performance, Quality, and OEE. Includes loss attribution breakdown.

**Grain:** One row per `(machine_id, shift_id, date_id)`

| Column | Business Meaning | Formula / Source |
|--------|------------------|------------------|
| `machine_id` | Machine identifier | From `dim_machine` |
| `shift_id` | Shift identifier (S1, S2, S3) | From `dim_shift` |
| `date_id` | Date of the shift | From `fct_production_run.run_date` |
| `availability` | % of scheduled time machine was running | `(shift_duration - downtime) / shift_duration` |
| `shift_duration_sec` | Scheduled shift duration in seconds | From `dim_shift` (handles overnight shifts) |
| `total_downtime_sec` | Total downtime seconds logged | SUM from `fct_downtime_event` |
| `performance` | Speed efficiency vs ideal cycle time | Duration-weighted average of run Performance |
| `quality` | % of produced units that were good | `SUM(good_units) / SUM(produced_units)` |
| `oee` | Overall Equipment Effectiveness | `availability * performance * quality` |
| `cycle_time_confidence` | Confidence level for cycle time data | `verified`, `estimated`, `unconfirmed` |
| `availability_loss_sec` | Downtime seconds attributed to Availability loss | Uses `oee_loss_category = 'Availability Loss'` |
| `performance_loss_sec` | Downtime seconds attributed to Performance loss | Uses `oee_loss_category = 'Performance Loss'` |
| `unmapped_loss_sec` | Downtime seconds with no mapped reason | `reason_id` is NULL or unmapped |
| `total_loss_sec` | Total loss seconds | Sum of all three loss categories |

**Metric Owner:** Production Manager owns `availability`'s definition; Quality Manager owns `quality`'s definition.

**Update Frequency:** Daily (full refresh)

**Test Coverage:**
- 6 unit tests covering all edge cases
- 3 singular tests (bounds, quality ceiling, loss-tree reconciliation)
- Model contract enforced

**Edge Cases Handled:**
- Night shifts (cross midnight) → duration calculated with +24 hours
- Zero downtime → Availability = 1.0
- Zero duration runs → excluded from Performance
- NULL cycle time → Performance and OEE = NULL
- `unconfirmed` confidence → carried through to output
- Multiple runs → duration-weighted average Performance

### `scrap_root_cause_summary` (Scaffold)

**Status:** Placeholder — full implementation scheduled for Week 6.

**Purpose:** Analyze scrap by defect type to identify root causes.

**Grain:** One row per `(machine_id, shift_id, date_id, product_id, defect_type_id)`

**Expected Sources:**
- `fct_qc_inspection` → defect data
- `dim_defect_type` → defect classification
- `fct_production_run` → scrap volume context (`produced_units - good_units`)