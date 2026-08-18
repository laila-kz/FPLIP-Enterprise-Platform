# ADR-008: OEE Edge Case Handling

## Status
Accepted (2026-07-31)

## Data Discovery (2026-07-31)

| Check | Finding |
|-------|---------|
| `dim_product` versions | Type 1 (1 version per product) |
| `dim_machine` versions | Type 1 (1 version per machine) |
| Shift data | 3 shifts: Morning (06-14), Afternoon (14-22), Night (22-06) |
| `standard_cycle_time_sec` | 0 NULL values (all 20 products have cycle time) |
| Bad run durations | 39 out of 101 runs have NULL/zero timestamps (38.6%) |

---

## Edge Case Decisions

| # | Edge Case | Decision |
|---|-----------|----------|
| 1 | Night shift crosses midnight | Calculate duration as: if `end_time < start_time`, add 24 hours |
| 2 | No downtime logged | Availability = 1.0 (use `COALESCE(downtime_sum, 0)`) |
| 3 | Shift duration = 0 | Exclude the row (should not occur with valid Shift Master) |
| 4 | Run duration = 0 or NULL | **Exclude this run from Performance calculation** (39 runs affected) |
| 5 | Produced units = 0 | Performance = 0; Quality = NULL if all runs have 0 produced |
| 6 | `standard_cycle_time_sec` = NULL | Performance = NULL → OEE = NULL (not applicable — 0 NULLs in data) |
| 7 | `cycle_time_confidence = 'unconfirmed'` | Calculate normally, carry confidence flag through to output |
| 8 | Multiple runs in same shift | **Duration-weighted average** for Performance roll-up |
| 9 | Performance > 100% | Allow >100%, don't cap OEE |

---

## Calculation Formulas

### Duration-Weighted Performance Formula
```sql
Performance = SUM(run_performance * run_duration_sec) / NULLIF(SUM(run_duration_sec), 0)

```

### Availability Formula

```sql
shift_duration_sec = CASE
  WHEN end_time < start_time THEN (24 - EXTRACT(HOUR FROM start_time) + EXTRACT(HOUR FROM end_time)) * 3600
  ELSE (EXTRACT(HOUR FROM end_time) - EXTRACT(HOUR FROM start_time)) * 3600
END;

Availability = (shift_duration_sec - COALESCE(total_downtime_sec, 0)) / NULLIF(shift_duration_sec, 0);

```

### Performance Formula

```sql
run_duration_sec = TIMESTAMP_DIFF(run_end_time, run_start_time, SECOND);

run_performance = (produced_units * standard_cycle_time_sec) / NULLIF(run_duration_sec, 0);

-- Note: Only include runs where run_duration_sec > 0

```

### Quality Formula

```sql
Quality = SUM(good_units) / NULLIF(SUM(produced_units), 0);

```

### OEE Formula

```sql
OEE = Availability * Performance * Quality;

```

---

## Data Quality Notes

**Bad duration runs (39/101 = 38.6%):**

A significant portion of production runs have missing or invalid timestamps. These runs will be **excluded from Performance calculation**, which means their production volume will NOT contribute to Performance. This is a data quality issue that should be addressed at the Silver layer if these runs represent real production events.

---

## Date

2026-07-31
