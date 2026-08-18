# ADR-009: Data Quality Findings (Week 5 Discovery)

## Status
Accepted (2026-07-31)

## Discovery Date
2026-07-31

## Findings

### 1. Bad Duration Runs (⚠️ HIGH)
- **39 out of 101 production runs** (38.6%) have NULL or invalid timestamps
- These runs cannot contribute to Performance calculation
- **Impact:** Performance and OEE will be calculated from only 62% of runs

### 2. Null Cycle Times (✅ GOOD)
- **0 NULL** `standard_cycle_time_sec` values in `dim_product`
- All 20 products have cycle times defined

### 3. Cycle Time Confidence (⚠️ MEDIUM)
| Confidence | Count | Percentage |
|------------|-------|------------|
| unconfirmed | 9 | 45% |
| estimated | 7 | 35% |
| verified | 4 | 20% |

**Impact:** 80% of products have unconfirmed or estimated cycle times. OEE numbers for these products should be flagged as provisional.

## Action Items

1. **Investigate bad duration runs** — are these real production events with missing timestamps, or data quality issues in the synthetic generator?

2. **Document in data dictionary** — note that Performance excludes runs with NULL/zero timestamps

3. **Consider confidence flag propagation** — ensure `cycle_time_confidence` is carried through to `oee_daily` output

## Related ADRs
- ADR-008: OEE Edge Case Handling (defines handling of bad runs)

## Date
2026-07-31