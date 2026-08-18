# FPLIP Business Impact Statement

## Status
Synthetic-data-based estimate (not verified against real factory data)

## The Numbers

### Scrap Reduction Opportunity

Based on `scrap_root_cause_summary` analysis of synthetic data:

| Metric | Value |
|--------|-------|
| Total units inspected | 50 |
| Total units rejected | 11 |
| Overall rejection rate | 22% |
| Highest defect category | Visual (34% of rejects) |
| Most impacted machine | M04 |

### OEE Improvement Opportunity

Based on `oee_daily` analysis:

| Metric | Value |
|--------|-------|
| Overall OEE range | 40-75% |
| Primary loss driver | Availability (highest impact) |
| Performance improvement opportunity | +15-20% |

### Estimated Financial Impact

**Assumptions:**
- Factory produces 10,000 units/day
- Average unit value: $10
- Current scrap rate: 22% → Target: 15%
- Improvement: 7% reduction in scrap

**Calculation:**

Daily scrap reduction = 10,000 × 7% = 700 units/day
Daily value saved = 700 × $10 = $7,000/day
Annual value saved = $7,000 × 365 = $2,555,000/year


## Label
**This is a synthetic-data-based estimate, not verified against real factory data.**

## Why This Still Matters

Even as an estimate, the platform demonstrates the capability to:
1. Identify which defect categories drive the most scrap
2. Pinpoint which machines need the most attention
3. Quantify OEE improvement opportunities
4. Provide root-cause analysis for quality issues

## Date
2026-08-09