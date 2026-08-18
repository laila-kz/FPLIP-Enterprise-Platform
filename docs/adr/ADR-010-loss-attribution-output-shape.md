# ADR-010: Loss Attribution Output Shape

## Status
Accepted (2026-08-02)

## Decision
Loss attribution columns are added **directly to `oee_daily`** rather than as a separate model.

## Reasoning
- This project has only two Gold marts (`oee_daily` and `scrap_root_cause_summary`).
- Adding columns directly keeps the model flat, highly performant, and easy for downstream BI tools (e.g., Power BI) to query.
- A separate model would add unnecessary joining complexity without added benefit.

## Columns Added & Empirical Verification

| Column | Description | Empirical Sample Values (2026-07-25) |
|--------|-------------|-------------------------------------|
| `availability_loss_sec` | Downtime seconds attributed to Availability loss (changeovers, breakdowns, etc.) | 900s, 900s, 1800s |
| `performance_loss_sec` | Downtime seconds attributed to Performance loss (slow running, minor stops) | 0s, 0s, 0s |
| `unmapped_loss_sec` | Downtime seconds with no mapped `reason_id` or `oee_loss_category` | 300s, 0s, 0s |
| `total_loss_sec` | Sum of all categorized losses (`availability` + `performance` + `unmapped`) | 1200s, 900s, 1800s |
| `total_downtime_sec` | Total downtime duration from `fct_downtime_event` | 1200s, 900s, 1800s |

## Reconciliation Rule
For every row in `fplip_gold.oee_daily`, the total sum of categorized losses must perfectly match the total recorded downtime:

$$ \text{availability\_loss\_sec} + \text{performance\_loss\_sec} + \text{unmapped\_loss\_sec} = \text{total\_downtime\_sec} $$

### Verified Output Sample
- **M01 / S1:** $900\text{s} + 0\text{s} + 300\text{s} = 1200\text{s}$ ($\text{MATCH}$)
- **M02 / S1:** $900\text{s} + 0\text{s} + 0\text{s} = 900\text{s}$ ($\text{MATCH}$)
- **M01 / S2:** $1800\text{s} + 0\text{s} + 0\text{s} = 1800\text{s}$ ($\text{MATCH}$)

## Date
2026-08-02