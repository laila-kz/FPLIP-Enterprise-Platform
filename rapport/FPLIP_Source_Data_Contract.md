# FPLIP — Source Data Contract
## Complete Operational Data Model Specification (Fixed Schema)
### For synthetic dataset generation — small (development) and large (production-realistic)

This document specifies the complete set of source datasets FPLIP ingests, as they would realistically exist inside a medium-sized concrete block / pavement block / zellige manufacturer — not as an ERP redesign, but as the operational data surfaces a Data Engineering platform reads from. No data is generated here. This schema is intended to remain fixed for the life of the project.

---

## Task 1 — Source Dataset Inventory

A real factory of this size and product mix generates more operational data than FPLIP ingests. The table below lists everything that realistically exists, and marks which datasets are in scope for this platform's Bronze ingestion versus which exist at the factory but are deliberately not ingested — consistent with the frozen blueprint's stated scope (production, downtime, QC; energy optional/Phase 2).

| # | Dataset | Type | Owner | Business Process | In Scope? |
|---|---|---|---|---|---|
| 1 | Machine Master | Master Data | Maintenance / Production Engineering | Asset registration when equipment is installed or reassigned | Yes |
| 2 | Product Master | Master Data | Production Engineering / Planning | SKU/mold/recipe definition when a new product is approved for production | Yes |
| 3 | Shift Master | Master Data | HR / Production Planning | Shift pattern definition, set once, rarely changed | Yes |
| 4 | Downtime Reason Code Master | Master Data | Maintenance | Standardized stop-reason taxonomy, defined once, occasionally extended | Yes |
| 5 | Defect Type Master | Master Data | Quality | Standardized defect classification taxonomy | Yes |
| 6 | Production Run Log | Transactional | Production Department (operators / shift supervisors) | End-of-shift or end-of-run manual logging of quantities produced | Yes |
| 7 | Downtime Event Log | Transactional | Production / Maintenance | Manual logging of each machine stop, with a reason | Yes |
| 8 | QC Inspection Log | Transactional | Quality Department | Batch/sample inspection and defect recording | Yes |
| 9 | Energy Meter Log | Transactional | Utilities / Maintenance | Manual or automated meter readings per machine | Optional — Phase 2 only, if meter data exists |
| — | Employee/Operator Master | Master Data | HR | Personnel records | **Out of scope** — see PII note below |
| — | Maintenance Work Order Log | Transactional | Maintenance | Corrective/preventive maintenance ticketing | **Out of scope** — would enrich downtime root-cause analysis but is not part of the frozen MVP; a real candidate for Section 32 (Future Improvements) |
| — | Raw Material Inventory | Transactional | Warehouse | Cement/aggregate stock movements | **Out of scope** — no current KPI in the platform consumes it |
| — | Bill of Materials (BOM) | Master Data | Production Engineering | Recipe composition per product | **Out of scope** — not required for OEE or scrap-by-defect-type; would matter for a future cost/yield module, not this platform |

**Why the Employee/Operator Master is excluded, not just deprioritized**: recording individually-identifiable operator performance data raises a real data-protection consideration under Morocco's Law 09-08 on personal data protection, and — separate from legal exposure — individually-attributable production data risks becoming a blame tool on the shop floor, a concern already flagged for the `scrap_by_shift` KPI in the platform's design review. Where an operator reference is operationally necessary (Task 2, Production Run Log), the schema uses an internal badge/employee code, never a name, and that code is treated as an internal lineage/traceability field, not a dimension exposed on any dashboard.

---

## Design Principles Applied Throughout (Task 6 — Senior Data Engineer Review, Applied Up Front)

Rather than presenting a first-draft schema and then a separate corrected one per dataset, the review findings below are already baked into every schema in Task 2 — each decision is stated once here so it isn't repeated nine times.

1. **Naming convention**: `snake_case` throughout; `_id` for surrogate/business keys, `_code` for short enumerated codes, `_date` for dates, `_at` for timestamps, `_flag` for booleans. No column name is reused with a different meaning across datasets.
2. **Timezone**: all timestamps are recorded in `Africa/Casablanca` local time (no DST observed since 2018, per current Moroccan practice) and stored with an explicit timezone-aware type — not naive local time — to avoid the exact partition-date drift risk called out in the platform's Week 2 implementation guide.
3. **`cycle_time_confidence` on Product Master**: carried forward directly from the frozen blueprint's Section 8 data contract as the fix for the platform's single largest validity risk — an unverified `standard_cycle_time_sec` silently corrupting OEE. This field is not optional polish; it is a required column.
4. **`data_entry_method` on every transactional table**: added during this review. A row entered via manual paper transcription carries materially different trust than one exported directly from a machine controller or ERP, and the platform's data contracts (blueprint Section 8) already require a `confidence` concept — this column is the row-level equivalent, letting a future Silver model or dashboard filter or flag manually-entered rows differently from system-sourced ones without needing a separate lookup.
5. **Nullable foreign keys where paper-based reality demands it**: `reason_id` on Downtime Event Log and `defect_type_id` on QC Inspection Log are nullable by design, not by oversight — a paper-based stop-reason sheet will produce free-text or blank entries before a mapping exercise standardizes them, and a QC pass record has no defect type at all. Forcing these to `NOT NULL` would make the schema look cleaner while making it lie about how the data actually arrives.
6. **The Production Log vs. QC Inspection "good units" tension, resolved explicitly**: `fct_production_run`'s `good_units` (operator self-reported at the point of production) and QC Inspection's rejection counts (an independent quality check, often on a sample, not 100% of units) are two different measurements of the same underlying reality, and they will not always agree. This schema does not force them into artificial agreement. `good_units` on the Production Run Log is the authoritative input to the OEE quality component (it's available for every run, not just inspected ones); the QC Inspection Log is authoritative for defect-type root-cause detail. A documented data-quality expectation (not a hard constraint) is that aggregated QC rejection rates and Production Log-derived scrap rates should track within a reasonable band — a persistent, large divergence between the two is itself a signal worth surfacing, not an error to silently reconcile away.
7. **Line-level normalization deliberately avoided**: a separate "Production Line Master" was considered and rejected. At this factory's likely scale (a handful of machines across one to three lines), `line_id` as a plain attribute on Machine Master carries all the information a separate master table would, without an extra join and an extra table to keep governed. This mirrors the platform's stated philosophy elsewhere of rejecting normalization that doesn't earn its complexity at this scale.
8. **Natural keys vs. surrogate keys on transactional logs**: where the physical source has its own reference number (a paper form's ticket number), that reference is captured as `log_reference_number` and preserved for lineage, but it is not relied upon as the primary key — paper-based systems produce duplicate or missing ticket numbers often enough that a derived composite natural key (machine + shift + product/date + sequence) is the more robust choice, with `log_reference_number` kept as a traceability field back to the physical document.

---

## Validation Against Analytical Requirements (Task 5)

**Would this support OEE correctly?**
Yes, with one deliberate modeling decision stated explicitly: Availability is computed at the **machine + shift + day** grain (shift duration, from Shift Master, minus total logged downtime for that machine/shift/day from the Downtime Event Log), not at the individual run grain — a single shift can contain multiple runs, but only one meaningful "was the machine available" measure per shift. Performance and Quality are computed at the **run** grain (per corrected grain, blueprint Section 15) and rolled up. This means Production Run Log and Downtime Event Log both need reliable `shift_id` and `machine_id` join keys, which both schemas below provide as required, non-nullable fields — this is not optional.

**Would this support Scrap Analysis?**
Yes — `produced_units - good_units` from the Production Run Log gives the scrap volume per run; the QC Inspection Log's `defect_type_id` gives the root-cause breakdown. The one dependency this places on data quality: `run_reference` on QC Inspection Log should be populated for a meaningful share of records, or root-cause attribution degrades to defect-type-by-day/machine rather than defect-type-by-specific-run. This is treated as a data-quality monitoring target (Section on Data Quality Rules, per dataset below), not a hard schema constraint, for the same paper-based-reality reason `reason_id` is nullable.

**Would this support Downtime Analysis?**
Yes, contingent on the reason-code mapping effort the platform's own risk assessment already flags as its highest-probability early risk. The schema supports the analysis; whether the *data* supports it depends on how much of `reason_free_text` gets mapped to `reason_id` during the factory's first weeks of use — which is exactly why `reason_free_text` is preserved as a permanent column, not discarded once mapped, so the mapping quality itself is auditable over time.

**Would this support Quality KPIs?**
Yes, via the QC Inspection Log and Defect Type Master, with the good-units-source resolution described in Design Principle 6 above.

**One addition made specifically to close a gap found during this review**: `oee_loss_category` was added to the Downtime Reason Code Master (not present in the platform's earlier draft contracts) because "downtime reason" alone doesn't tell an OEE calculation whether a given stop should count against Availability or against Performance (e.g., running below the ideal cycle time due to a minor unlogged stoppage is a Performance loss, not an Availability loss) — without this column, the OEE formula's loss attribution would be ambiguous by construction, not just imprecise.

---

## Task 2, 3, 4 — Complete Dataset Specifications

---

### Dataset: Machine Master

**Purpose**: authoritative registry of every production machine, feeding `dim_machine` (with SCD Type 2 history per the frozen blueprint).
**Business Owner**: Maintenance / Production Engineering
**Source System**: Manually maintained Excel/spreadsheet at this factory's scale (ERP asset module if Nizzar's asset module is in use — unconfirmed, treat Excel as the baseline assumption)
**Refresh Frequency**: Ad hoc on change (installation, reassignment, decommission); re-exported as a full snapshot on each ingestion run regardless of whether anything changed, to keep the SCD2 mechanism simple
**Primary Key**: `machine_id`
**Foreign Keys**: none (Machine Master is a root master dataset)
**Description**: One row per physical production machine currently or historically in service.

**Schema Table**

| Column | Data Type | Nullable | PK | FK | Description | Business Meaning | Example | Allowed Values / Constraints | Validation Rule | Default |
|---|---|---|---|---|---|---|---|---|---|---|
| `machine_id` | string(10) | No | Yes | — | Unique machine identifier | The natural key operators use on the shop floor | `M01` | Pattern `M[0-9]{2}` | Must be unique across all rows (including historical SCD2 versions of the same machine) | — |
| `machine_name` | string(100) | No | — | — | Human-readable machine name | Displayed in dashboards | `Vibro-Compactor Line 1` | — | Non-empty | — |
| `machine_type` | string(50) | No | — | — | Equipment category | Groups similar machines for benchmarking | `Block Press` | `Block Press`, `Tile Press`, `Mixer`, `Curing Chamber`, `Other` | Must be one of allowed values | `Other` |
| `line_id` | string(10) | Yes | — | — | Production line the machine belongs to | Groups machines by physical production line | `L1` | Pattern `L[0-9]` | — | Null |
| `location` | string(100) | Yes | — | — | Physical location within the factory | Traceability / maintenance routing | `Building A - Bay 2` | — | — | Null |
| `manufacturer` | string(100) | Yes | — | — | Equipment manufacturer | Maintenance/spare-parts context | `Masa Group` | — | — | Null |
| `install_date` | date | Yes | — | — | Date the machine entered service | Age/depreciation context | `2019-03-15` | Must be ≤ current date | — | Null |
| `status` | string(20) | No | — | — | Current operational status | Filters active vs. retired equipment from analysis | `Active` | `Active`, `Inactive`, `Maintenance`, `Decommissioned` | Must be one of allowed values | `Active` |
| `nominal_capacity_units_per_hour` | integer | Yes | — | — | Nameplate rated capacity | Cross-check against `standard_cycle_time_sec` on Product Master for plausibility | `450` | > 0 if present | — | Null |
| `data_entry_method` | string(20) | No | — | — | How this record was captured | Trust/lineage signal (Design Principle 4) | `Manual` | `Manual`, `ERP Export`, `Machine Export` | Must be one of allowed values | `Manual` |
| `last_updated_at` | timestamp (tz-aware) | No | — | — | Last modification timestamp | Drives the SCD2 snapshot strategy | `2026-02-10T09:15:00+01:00` | Must be ≥ `install_date` if both present | — | Record creation time |
| `last_updated_by` | string(50) | Yes | — | — | Badge/employee code of the person who last edited this record | Audit trail; not a personal name (Design Principle 4/PII note) | `EMP-0231` | — | — | Null |

**Relationships**: one Machine → many Production Run Log rows; one Machine → many Downtime Event Log rows; one Machine → many Energy Meter Log rows (if Phase 2 is built).

**Business Rules**: a machine's `status` cannot move directly from `Decommissioned` back to `Active` (a decommissioned machine that returns to service should receive a new `machine_id`, to keep historical OEE trend lines meaningful). `line_id`, if populated, should be consistent for a machine across time unless a real reassignment occurred — a reassignment is exactly the kind of change the SCD2 snapshot is designed to capture.

**Data Quality Rules**: `machine_id` uniqueness enforced at Silver; `status` restricted to the allowed-values list; a warning (not a hard failure) if `nominal_capacity_units_per_hour` implies a cycle time wildly inconsistent (more than, say, 3x) with the corresponding product's `standard_cycle_time_sec` — this is exactly the kind of cross-dataset plausibility check that can catch a bad `standard_cycle_time_sec` value before it reaches Gold.

**Expected Daily Growth**: effectively zero new rows per day; occasional `status`/`line_id` updates, at most a few per month.

**Expected Development Dataset Size**: 8–12 machines, with 1–2 of them carrying a second SCD2 version (to exercise the snapshot logic, per the Week-3/Week-4 implementation guide's explicit requirement to test SCD2 with a real change).

**Expected Final Dataset Size**: 10–15 machines, with 15–25 total rows once SCD2 history from roughly 18–24 months of realistic occasional reassignments/status changes is included.

---

### Dataset: Product Master

**Purpose**: authoritative SKU/recipe catalog, feeding `dim_product`.
**Business Owner**: Production Engineering / Planning
**Source System**: Manually maintained Excel
**Refresh Frequency**: Ad hoc, low volume — new products are rare events
**Primary Key**: `product_id`
**Foreign Keys**: none
**Description**: One row per distinct product/SKU the factory manufactures.

**Schema Table**

| Column | Data Type | Nullable | PK | FK | Description | Business Meaning | Example | Allowed Values / Constraints | Validation Rule | Default |
|---|---|---|---|---|---|---|---|---|---|---|
| `product_id` | string(20) | No | Yes | — | Unique product identifier | Natural key | `P-BLOCK-01` | Pattern `P-[A-Z]+-[0-9]{2}` | Unique across all rows | — |
| `product_name` | string(150) | No | — | — | Descriptive product name | Dashboard display | `Hollow Block 20x20x40` | — | Non-empty | — |
| `product_family` | string(30) | No | — | — | High-level product grouping | Groups related SKUs for benchmarking | `Concrete Block` | `Concrete Block`, `Pavement Block`, `Zellige`, `Other` | Must be one of allowed values | — |
| `unit_of_measure` | string(10) | No | — | — | Unit the product is counted in | Determines dashboard unit labels | `unit` | `unit`, `m2`, `piece` | Must be one of allowed values | `unit` |
| `standard_cycle_time_sec` | decimal(8,2) | No | — | — | Expected time to produce one unit under normal conditions | Direct input to the OEE Performance component — the platform's single highest-risk field | `12.50` | > 0 | Must be present before the product can be used in `fct_production_run` | — |
| `cycle_time_source` | string(50) | No | — | — | Where the cycle time figure came from | Governance trail for the confidence tag | `Manufacturing Engineering Estimate` | `Manufacturer Spec`, `Manufacturing Engineering Estimate`, `Historical Average`, `Unconfirmed` | Must be one of allowed values | `Unconfirmed` |
| `cycle_time_confidence` | string(20) | No | — | — | Confidence tag surfaced to dashboard consumers | Directly implements blueprint Section 8's contract requirement | `estimated` | `verified`, `estimated`, `unconfirmed` | Must be one of allowed values; `verified` requires `cycle_time_source` ≠ `Unconfirmed` | `unconfirmed` |
| `standard_weight_kg` | decimal(6,2) | Yes | — | — | Nominal unit weight | Optional cross-check / future cost-module input | `18.50` | > 0 if present | — | Null |
| `active_flag` | boolean | No | — | — | Whether the product is currently in production | Filters discontinued SKUs from active dashboards | `true` | `true`/`false` | — | `true` |
| `data_entry_method` | string(20) | No | — | — | Capture method | Trust/lineage signal | `Manual` | `Manual`, `ERP Export` | Must be one of allowed values | `Manual` |
| `created_at` | timestamp (tz-aware) | No | — | — | Record creation time | — | `2025-11-02T10:00:00+01:00` | — | — | Record creation time |
| `last_updated_at` | timestamp (tz-aware) | No | — | — | Last modification time | Drives SCD2 | `2026-01-14T08:30:00+01:00` | Must be ≥ `created_at` | — | Same as `created_at` |

**Relationships**: one Product → many Production Run Log rows.

**Business Rules**: `standard_cycle_time_sec` must never be blank for any product referenced by a Production Run Log row — if a true value is genuinely unknown, `cycle_time_confidence` must be `unconfirmed` and the field still populated with a best estimate, never left null, since the OEE formula cannot compute without it. This is the schema-level enforcement of the platform's Section 8 governance requirement.

**Data Quality Rules**: `cycle_time_confidence = verified` should never coexist with `cycle_time_source = Unconfirmed` (checked as a cross-column rule); any product with `cycle_time_confidence != verified` should be visibly flagged wherever `oee_daily.performance` is displayed downstream, per the frozen blueprint's Gold-layer design.

**Expected Daily Growth**: near zero; a new SKU or a cycle-time revision might occur a handful of times per year.

**Expected Development Dataset Size**: 15–20 products, deliberately including at least one with `cycle_time_confidence = unconfirmed` to exercise the confidence-flagging logic end to end during development.

**Expected Final Dataset Size**: 20–35 products active at any time, 30–50 total rows including discontinued/superseded SKUs and cycle-time revisions accumulated over 18–24 months.

---

### Dataset: Shift Master

**Purpose**: shift pattern definitions, feeding `dim_shift`.
**Business Owner**: HR / Production Planning
**Source System**: Manual entry, essentially static configuration
**Refresh Frequency**: Set once, changed only if the factory's shift structure itself changes
**Primary Key**: `shift_id`
**Foreign Keys**: none
**Description**: One row per defined shift pattern.

**Schema Table**

| Column | Data Type | Nullable | PK | FK | Description | Business Meaning | Example | Allowed Values / Constraints | Validation Rule | Default |
|---|---|---|---|---|---|---|---|---|---|---|
| `shift_id` | string(5) | No | Yes | — | Unique shift identifier | Natural key | `S1` | Pattern `S[0-9]` | Unique | — |
| `shift_name` | string(30) | No | — | — | Descriptive shift name | Dashboard display | `Morning` | — | Non-empty | — |
| `start_time` | time | No | — | — | Shift start (local time) | Basis for Availability's planned-time denominator | `06:00:00` | — | — | — |
| `end_time` | time | No | — | — | Shift end (local time) | Basis for Availability's planned-time denominator | `14:00:00` | — | — | — |
| `crosses_midnight` | boolean | No | — | — | Whether the shift spans two calendar dates | Correct date-partitioning of downtime/production events near midnight | `false` | `true`/`false` | If `end_time` < `start_time`, must be `true` | `false` |
| `active_flag` | boolean | No | — | — | Whether this shift pattern is currently in use | — | `true` | `true`/`false` | — | `true` |

**Relationships**: one Shift → many Production Run Log rows; one Shift → many Downtime Event Log rows.

**Business Rules**: shift windows for `active_flag = true` shifts should not overlap for the same date, or Availability's denominator becomes ambiguous.

**Data Quality Rules**: exactly the expected number of active shifts (2 or 3, per factory operating pattern) should be present at any time — a data-quality alert (not a hard failure) if this count changes unexpectedly.

**Expected Daily Growth**: zero.

**Expected Development Dataset Size**: 2–3 rows.

**Expected Final Dataset Size**: 2–3 rows (this table is not expected to meaningfully grow even over a multi-year horizon).

---

### Dataset: Downtime Reason Code Master

**Purpose**: standardized stop-reason taxonomy, feeding `dim_downtime_reason`.
**Business Owner**: Maintenance
**Source System**: Manually maintained Excel, likely formalized partway through the project as free-text reasons get standardized (see Design Principle 5)
**Refresh Frequency**: Ad hoc, extended occasionally as new stop-reason patterns are observed
**Primary Key**: `reason_id`
**Foreign Keys**: none
**Description**: One row per standardized downtime reason code.

**Schema Table**

| Column | Data Type | Nullable | PK | FK | Description | Business Meaning | Example | Allowed Values / Constraints | Validation Rule | Default |
|---|---|---|---|---|---|---|---|---|---|---|
| `reason_id` | string(15) | No | Yes | — | Unique reason code | Natural key | `DT-CHG-01` | Pattern `DT-[A-Z]{3}-[0-9]{2}` | Unique | — |
| `reason_name` | string(100) | No | — | — | Descriptive name | Dashboard display | `Product Changeover` | — | Non-empty | — |
| `reason_category` | string(30) | No | — | — | High-level grouping | Pareto/trend grouping | `Changeover` | `Planned`, `Unplanned`, `Changeover`, `Maintenance`, `Material Shortage`, `Other` | Must be one of allowed values | `Other` |
| `oee_loss_category` | string(30) | No | — | — | Which OEE component this reason affects | Resolves the OEE loss-attribution ambiguity identified in the Task 5 review | `Availability Loss` | `Availability Loss`, `Performance Loss`, `Not Applicable` | Must be one of allowed values | `Availability Loss` |
| `description` | string(255) | Yes | — | — | Extended explanation | Reference for whoever maintains the mapping | `Time to switch mold/product on the press` | — | — | Null |
| `active_flag` | boolean | No | — | — | Whether this code is currently assignable | Retiring a reason code without deleting its history | `true` | `true`/`false` | — | `true` |

**Relationships**: one Reason → many Downtime Event Log rows (0..1 per event, since the FK is nullable on the transactional side).

**Business Rules**: a reason code should never be hard-deleted once it has been referenced by any Downtime Event Log row — retire it via `active_flag = false` instead, to preserve historical reporting integrity.

**Data Quality Rules**: the share of Downtime Event Log rows with a non-null `reason_id` (i.e., successfully mapped from free text) is tracked as an explicit data-quality metric over time — an improving trend is itself evidence the mapping/governance effort is working.

**Expected Daily Growth**: zero to near-zero; new codes added a handful of times, mostly in the project's early weeks as real downtime patterns are first observed.

**Expected Development Dataset Size**: 15–20 reason codes, covering all six `reason_category` values.

**Expected Final Dataset Size**: 25–35 reason codes as real operational nuance accumulates over 18–24 months.

---

### Dataset: Defect Type Master

**Purpose**: standardized defect classification, feeding `dim_defect_type`.
**Business Owner**: Quality Department
**Source System**: Manually maintained Excel
**Refresh Frequency**: Ad hoc, low volume
**Primary Key**: `defect_type_id`
**Foreign Keys**: none
**Description**: One row per standardized defect classification.

**Schema Table**

| Column | Data Type | Nullable | PK | FK | Description | Business Meaning | Example | Allowed Values / Constraints | Validation Rule | Default |
|---|---|---|---|---|---|---|---|---|---|---|
| `defect_type_id` | string(15) | No | Yes | — | Unique defect code | Natural key | `DEF-CRACK` | Pattern `DEF-[A-Z]+` | Unique | — |
| `defect_name` | string(100) | No | — | — | Descriptive name | Dashboard display | `Surface Crack` | — | Non-empty | — |
| `defect_category` | string(30) | No | — | — | High-level grouping | Pareto/trend grouping | `Structural` | `Dimensional`, `Visual`, `Structural`, `Material`, `Other` | Must be one of allowed values | `Other` |
| `severity` | string(10) | No | — | — | Defect severity | Prioritization in root-cause dashboards | `Major` | `Minor`, `Major`, `Critical` | Must be one of allowed values | `Minor` |
| `description` | string(255) | Yes | — | — | Extended explanation | Reference for QC staff | `Visible crack exceeding 2mm on any face` | — | — | Null |
| `active_flag` | boolean | No | — | — | Whether currently assignable | — | `true` | `true`/`false` | — | `true` |

**Relationships**: one Defect Type → many QC Inspection Log rows (0..1 per inspection; null on a pass).

**Business Rules**: retire via `active_flag = false`, never hard-delete once referenced.

**Data Quality Rules**: `defect_category` distribution monitored for plausibility — a sudden spike concentrated in one category may indicate either a real process problem or a QC data-entry pattern worth investigating (an operator defaulting to the same code for convenience).

**Expected Daily Growth**: zero to near-zero.

**Expected Development Dataset Size**: 10–15 defect types, covering all four category values.

**Expected Final Dataset Size**: 15–25 defect types.

---

### Dataset: Production Run Log

**Purpose**: core transactional record of what was produced, feeding `fct_production_run` (grain per blueprint Section 15: one row per machine + shift + product + date + `run_sequence_number`).
**Business Owner**: Production Department (operators / shift supervisors)
**Source System**: Paper form digitized manually into Excel at end of shift, or Nizzar ERP export if/where available (unconfirmed — see the platform's Section 7 fallback provision)
**Refresh Frequency**: Daily, effectively batched at end-of-shift entries
**Primary Key**: composite natural key `(machine_id, shift_id, run_date, run_sequence_number)` — see Design Principle 8 on why this is preferred over relying on `log_reference_number` alone
**Foreign Keys**: `machine_id` → Machine Master; `shift_id` → Shift Master; `product_id` → Product Master
**Description**: One row per distinct production run.

**Schema Table**

| Column | Data Type | Nullable | PK | FK | Description | Business Meaning | Example | Allowed Values / Constraints | Validation Rule | Default |
|---|---|---|---|---|---|---|---|---|---|---|
| `log_reference_number` | string(20) | Yes | — | — | The physical paper form's own ticket number, if any | Lineage back to the source document | `LOG-2026-04521` | — | — | Null |
| `machine_id` | string(10) | No | Part of PK | Yes → Machine Master | Machine that ran | — | `M01` | Must exist in Machine Master | — | — |
| `shift_id` | string(5) | No | Part of PK | Yes → Shift Master | Shift during which the run occurred | — | `S1` | Must exist in Shift Master | — | — |
| `product_id` | string(20) | No | — | Yes → Product Master | Product produced | — | `P-BLOCK-01` | Must exist in Product Master | — | — |
| `run_date` | date | No | Part of PK | — | Calendar date of the run, per Design Principle 2's timezone handling | Partition key downstream | `2026-04-14` | — | — | — |
| `run_sequence_number` | integer | No | Part of PK | — | Distinguishes multiple runs of the same machine/shift/product/day (e.g., across a changeover) | Directly implements the corrected fact grain, blueprint Section 15 | `1` | ≥ 1, increments per distinct start/stop cycle | Must be unique within `(machine_id, shift_id, product_id, run_date)` | `1` |
| `run_start_time` | timestamp (tz-aware) | Yes | — | — | Run start | Often unavailable on paper logs | `2026-04-14T06:10:00+01:00` | If present, must fall within the shift's window | — | Null |
| `run_end_time` | timestamp (tz-aware) | Yes | — | — | Run end | — | `2026-04-14T13:45:00+01:00` | If present, must be ≥ `run_start_time` | — | Null |
| `planned_units` | integer | Yes | — | — | Units the shift plan expected from this run | Optional planning context, not required for OEE itself | `800` | > 0 if present | — | Null |
| `produced_units` | integer | No | — | — | Total units produced in the run | Numerator for Performance, denominator for Quality | `750` | ≥ 0 | Must be ≥ `good_units` | — |
| `good_units` | integer | No | — | — | Units meeting spec, self-reported by the operator | Authoritative input to OEE's Quality component (Design Principle 6) | `710` | ≥ 0 | Must be ≤ `produced_units` | — |
| `operator_id` | string(15) | Yes | — | — | Internal badge/employee code, not a name | Traceability without personal identification (PII note) | `EMP-0231` | — | — | Null |
| `notes` | string(255) | Yes | — | — | Free-text operator notes | Context for anomalies | `Slow start, mold warm-up` | — | — | Null |
| `data_entry_method` | string(20) | No | — | — | Capture method | Trust/lineage signal | `Manual` | `Manual`, `ERP Export` | Must be one of allowed values | `Manual` |
| `entered_by` | string(15) | No | — | — | Badge code of whoever transcribed the record | Audit trail | `EMP-0104` | — | — | — |
| `entered_at` | timestamp (tz-aware) | No | — | — | When the record was entered into the system | Distinguishes event time from entry time | `2026-04-14T14:05:00+01:00` | Must be ≥ `run_end_time` if present | — | Record creation time |

**Relationships**: many-to-one to Machine Master, Shift Master, Product Master; one-to-many to QC Inspection Log (via `run_reference` on that table, nullable in both directions per Design Principle 5).

**Business Rules**: `run_sequence_number` must reset to 1 for each new `(machine_id, shift_id, product_id, run_date)` combination — this is the field the Week 4 grain-validation checkpoint exists specifically to exercise. `good_units` can legitimately be less than `produced_units` (scrap exists); it should never exceed it.

**Data Quality Rules**: `produced_units >= good_units` enforced as a hard test at Silver; `run_start_time`/`run_end_time` falling within the associated shift's window checked as a warning-level test (not hard failure, given paper-log timing imprecision is expected); freshness — at least one row per active machine per shift expected daily, flagged if absent for two consecutive days.

**Expected Daily Growth**: roughly 15–30 rows/day across all machines and shifts at this factory's scale (a handful of machines, up to 2–3 runs per machine per shift, 2–3 shifts).

**Expected Development Dataset Size**: 30–60 days of activity → roughly 500–1,800 rows, deliberately including at least one constructed multi-run-per-shift case per the Week 4 grain-validation requirement.

**Expected Final Dataset Size**: 18–24 months of activity (≈550–730 days) → roughly 8,000–22,000 rows.

---

### Dataset: Downtime Event Log

**Purpose**: transactional record of every machine stop, feeding `fct_downtime_event`.
**Business Owner**: Production / Maintenance
**Source System**: Paper reason-code sheet, likely free-text-heavy before standardization
**Refresh Frequency**: Daily
**Primary Key**: surrogate `event_id` (generated at Silver load, since no reliable natural key exists on a free-text paper log)
**Foreign Keys**: `machine_id` → Machine Master; `shift_id` → Shift Master; `reason_id` → Downtime Reason Code Master (nullable)
**Description**: One row per distinct machine stop event.

**Schema Table**

| Column | Data Type | Nullable | PK | FK | Description | Business Meaning | Example | Allowed Values / Constraints | Validation Rule | Default |
|---|---|---|---|---|---|---|---|---|---|---|
| `event_id` | string(30) | No | Yes | — | Surrogate identifier assigned at load time | — | `DTE-20260414-0007` | — | Unique | Generated |
| `machine_id` | string(10) | No | — | Yes → Machine Master | Machine that stopped | — | `M02` | Must exist in Machine Master | — | — |
| `shift_id` | string(5) | No | — | Yes → Shift Master | Shift during which the stop occurred | — | `S2` | Must exist in Shift Master | — | — |
| `event_date` | date | No | — | — | Calendar date of the event | Partition key downstream | `2026-04-14` | — | — | — |
| `reason_id` | string(15) | Yes | — | Yes → Downtime Reason Code Master | Standardized reason, once mapped | Root-cause grouping | `DT-CHG-01` | Must exist in Downtime Reason Master if present | — | Null |
| `reason_free_text` | string(255) | Yes | — | — | Raw text as originally logged | Preserved permanently for mapping-quality audit (Design Principle 5) | `"changeover mold 3"` | — | Required if `reason_id` is null | Null |
| `start_time` | timestamp (tz-aware) | No | — | — | Stop start | — | `2026-04-14T09:20:00+01:00` | Must fall within the shift's window | — | — |
| `end_time` | timestamp (tz-aware) | Yes | — | — | Stop end | Null if the stop was still ongoing at end-of-shift logging | `2026-04-14T09:45:00+01:00` | If present, must be ≥ `start_time` | — | Null |
| `duration_sec` | integer | No | — | — | Stop duration | Direct OEE Availability input | `1500` | > 0; if `end_time` present, must equal `end_time - start_time` | Recomputed at Silver as a cross-check against the logged value | — |
| `data_entry_method` | string(20) | No | — | — | Capture method | Trust/lineage signal | `Manual` | `Manual`, `ERP Export` | Must be one of allowed values | `Manual` |
| `entered_by` | string(15) | No | — | — | Badge code of transcriber | Audit trail | `EMP-0104` | — | — | — |
| `entered_at` | timestamp (tz-aware) | No | — | — | Entry timestamp | — | `2026-04-14T14:10:00+01:00` | — | — | Record creation time |

**Relationships**: many-to-one to Machine Master, Shift Master, Downtime Reason Code Master (optional).

**Business Rules**: exactly one of `reason_id` populated or `reason_free_text` populated must be true at initial entry (both may eventually be populated once mapped, but never neither).

**Data Quality Rules**: `reason_id IS NOT NULL` rate tracked over time as the mapping-quality metric described in the Downtime Reason Code Master section; `duration_sec` cross-checked against `end_time - start_time` when both are present, flagged (not failed) on mismatch, since manual entry error here is expected and informative rather than something to silently discard.

**Expected Daily Growth**: roughly 8–20 stop events/day across all machines.

**Expected Development Dataset Size**: 30–60 days → roughly 250–1,200 rows, including a deliberate mix of mapped and unmapped (`reason_free_text`-only) records to exercise the mapping-quality metric.

**Expected Final Dataset Size**: 18–24 months → roughly 4,000–15,000 rows.

---

### Dataset: QC Inspection Log

**Purpose**: transactional record of quality inspections, feeding `fct_qc_inspection`.
**Business Owner**: Quality Department
**Source System**: Manually maintained Excel
**Refresh Frequency**: Daily
**Primary Key**: surrogate `inspection_id`
**Foreign Keys**: `production_run_reference` → Production Run Log (nullable, composite reference); `defect_type_id` → Defect Type Master (nullable)
**Description**: One row per inspection batch/sample.

**Schema Table**

| Column | Data Type | Nullable | PK | FK | Description | Business Meaning | Example | Allowed Values / Constraints | Validation Rule | Default |
|---|---|---|---|---|---|---|---|---|---|---|
| `inspection_id` | string(30) | No | Yes | — | Surrogate identifier | — | `QC-20260414-0012` | — | Unique | Generated |
| `production_run_reference` | string(20) | Yes | — | Yes → Production Run Log (`log_reference_number`, or the composite key if that's null) | Links the inspection back to the run it covers | Enables run-level root-cause attribution (Task 5 finding) | `LOG-2026-04521` | Should resolve to an existing Production Run Log row if present | Data-quality target, not a hard constraint (see rule below) | Null |
| `inspection_date` | date | No | — | — | Date of inspection | Partition key downstream | `2026-04-14` | — | — | — |
| `defect_type_id` | string(15) | Yes | — | Yes → Defect Type Master | Defect found, if any | Null means the inspected batch passed | `DEF-CRACK` | Must exist in Defect Type Master if present | — | Null |
| `units_inspected` | integer | No | — | — | Units in the inspected sample/batch | Denominator for QC-derived rejection rate | `50` | > 0 | — | — |
| `units_rejected` | integer | No | — | — | Units failing inspection | Numerator for QC-derived rejection rate | `4` | ≥ 0 | Must be ≤ `units_inspected` | `0` |
| `inspector_id` | string(15) | Yes | — | — | Badge code of the inspector | Audit trail, not personal identification | `EMP-0318` | — | — | Null |
| `data_entry_method` | string(20) | No | — | — | Capture method | Trust/lineage signal | `Manual` | `Manual`, `ERP Export` | Must be one of allowed values | `Manual` |
| `entered_by` | string(15) | No | — | — | Badge code of transcriber | — | `EMP-0104` | — | — | — |
| `entered_at` | timestamp (tz-aware) | No | — | — | Entry timestamp | — | `2026-04-14T15:30:00+01:00` | — | — | Record creation time |

**Relationships**: many-to-one to Production Run Log (optional), Defect Type Master (optional).

**Business Rules**: `units_rejected` requires a non-null `defect_type_id`; `units_rejected = 0` implies `defect_type_id` is null (a passed inspection has no defect to record).

**Data Quality Rules**: the share of rows with a resolvable `production_run_reference` is tracked as an explicit metric (per the Task 5 finding above) — this is the number to watch if run-level scrap root-cause attribution starts looking thin; `units_rejected <= units_inspected` enforced as a hard test.

**Expected Daily Growth**: roughly 10–25 inspection records/day.

**Expected Development Dataset Size**: 30–60 days → roughly 300–1,500 rows, including a deliberate share (not 100%) with a resolvable `production_run_reference`, to make the mapping-quality metric meaningful to test against.

**Expected Final Dataset Size**: 18–24 months → roughly 5,500–18,000 rows.

---

### Dataset: Energy Meter Log (Optional — Phase 2 Only)

**Purpose**: per-machine energy consumption readings, feeding a future `energy_cost_per_unit` Gold mart, per the frozen blueprint's Phase 2 scope.
**Business Owner**: Utilities / Maintenance
**Source System**: Manual meter reading (most likely) or machine export if smart meters exist (unconfirmed)
**Refresh Frequency**: Daily or per-shift, depending on what the factory's actual meter setup supports — this is explicitly unconfirmed and should not be assumed until Phase 2 discovery
**Primary Key**: surrogate `reading_id`
**Foreign Keys**: `machine_id` → Machine Master; `shift_id` → Shift Master (nullable, if only daily aggregate readings exist)
**Description**: One row per energy meter reading.

**Schema Table**

| Column | Data Type | Nullable | PK | FK | Description | Business Meaning | Example | Allowed Values / Constraints | Validation Rule | Default |
|---|---|---|---|---|---|---|---|---|---|---|
| `reading_id` | string(30) | No | Yes | — | Surrogate identifier | — | `ENG-20260414-M01` | — | Unique | Generated |
| `machine_id` | string(10) | No | — | Yes → Machine Master | Machine metered | — | `M01` | Must exist in Machine Master | — | — |
| `reading_date` | date | No | — | — | Date of reading | Partition key | `2026-04-14` | — | — | — |
| `shift_id` | string(5) | Yes | — | Yes → Shift Master | Shift the reading covers, if metering is shift-level rather than daily | — | `S1` | Must exist in Shift Master if present | — | Null |
| `energy_kwh` | decimal(10,2) | No | — | — | Energy consumed | Numerator for cost-per-unit calculations | `142.50` | ≥ 0 | — | — |
| `data_entry_method` | string(20) | No | — | — | Capture method | Trust/lineage signal — matters more here than anywhere else, since manual vs. smart-meter readings carry very different trust | `Manual` | `Manual`, `Machine Export` | Must be one of allowed values | `Manual` |
| `entered_by` | string(15) | No | — | — | Badge code of transcriber | — | `EMP-0104` | — | — | — |
| `entered_at` | timestamp (tz-aware) | No | — | — | Entry timestamp | — | `2026-04-14T16:00:00+01:00` | — | — | Record creation time |

**Relationships**: many-to-one to Machine Master, optionally Shift Master.

**Business Rules**: none beyond the basic non-negativity of `energy_kwh` — this dataset's business rules are deliberately left minimal since its scope, granularity, and even its existence in real form are unconfirmed pending Phase 2 discovery.

**Data Quality Rules**: freshness check only — at least one reading per active machine per day expected once this stream is actually ingested.

**Expected Daily Growth**: roughly 10–30 rows/day, depending on whether metering is per-machine-per-day or per-machine-per-shift.

**Expected Development Dataset Size**: if built at all — 30–60 days → roughly 300–1,800 rows.

**Expected Final Dataset Size**: 18–24 months → roughly 5,500–22,000 rows.

---

## Task 4 — Consolidated Relationship Map

```
Machine Master (1) ──────< Production Run Log (N)
Machine Master (1) ──────< Downtime Event Log (N)
Machine Master (1) ──────< Energy Meter Log (N, optional)

Product Master (1) ──────< Production Run Log (N)

Shift Master (1) ──────< Production Run Log (N)
Shift Master (1) ──────< Downtime Event Log (N)
Shift Master (1) ──────< Energy Meter Log (0..N, optional)

Downtime Reason Code Master (1) ──────< Downtime Event Log (0..N)   [nullable FK]

Defect Type Master (1) ──────< QC Inspection Log (0..N)             [nullable FK]

Production Run Log (1) ──────< QC Inspection Log (0..N)             [nullable FK both directions]
```

**Referential integrity posture**: every master-to-transactional relationship above is enforced as a hard test at Silver *except* the two explicitly marked nullable — `reason_id` and `defect_type_id`/`production_run_reference` — which are enforced only as "must resolve if present" tests, not "must be present" tests. This asymmetry is deliberate and is the schema-level expression of Design Principle 5: a schema that pretended paper-based reason mapping and run-attribution were always complete from day one would be lying about the data it's actually going to receive.

---

## Task 7 — Summary Table

| Dataset | Purpose | Columns | Expected Daily Rows | Dev Dataset Size | Production Dataset Size |
|---|---|---|---|---|---|
| Machine Master | Equipment registry | 12 | ~0 (occasional updates) | 10–15 rows | 15–25 rows (incl. SCD2 history) |
| Product Master | SKU/recipe catalog | 12 | ~0 (occasional updates) | 15–20 rows | 30–50 rows (incl. SCD2 history) |
| Shift Master | Shift pattern definitions | 6 | 0 | 2–3 rows | 2–3 rows |
| Downtime Reason Code Master | Standardized stop-reason taxonomy | 6 | ~0 (occasional additions) | 15–20 rows | 25–35 rows |
| Defect Type Master | Standardized defect taxonomy | 6 | ~0 (occasional additions) | 10–15 rows | 15–25 rows |
| Production Run Log | Core production transactions | 15 | 15–30 | 500–1,800 rows | 8,000–22,000 rows |
| Downtime Event Log | Machine stop transactions | 12 | 8–20 | 250–1,200 rows | 4,000–15,000 rows |
| QC Inspection Log | Quality inspection transactions | 10 | 10–25 | 300–1,500 rows | 5,500–18,000 rows |
| Energy Meter Log (optional) | Energy readings | 8 | 10–30 | 300–1,800 rows (if built) | 5,500–22,000 rows (if built) |

**Total, MVP scope only (excluding Energy Meter Log)**: 5 master datasets + 3 transactional datasets, ~1,000–4,500 total development rows, ~17,500–60,000 total production-scale rows across roughly 18–24 months of simulated operation.

---

## Closing Note

This schema is designed to be generated at two very different scales without changing shape: the development dataset exercises every edge case this contract anticipates (a multi-run day, an SCD2 change, an unmapped downtime reason, an unresolvable QC-to-run reference, an `unconfirmed` cycle time) in miniature, while the production-scale dataset is the same shape stretched over a realistic operating history. Nothing in this document should need to change once generation begins — if it does, that's a signal the contract missed something real, and the correct response is a new ADR documenting the revision, not a silent edit to this file.
