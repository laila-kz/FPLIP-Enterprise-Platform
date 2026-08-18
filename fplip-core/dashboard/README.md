# FPLIP Dashboard — Apache Superset Export

## What This Folder Contains

| File | Description |
|------|-------------|
| `exports/fplip_dashboard_export.zip` | Dashboard export (re-importable into Superset) |
| `screenshots/dashboard_full.png` | Full dashboard view |
| `screenshots/dashboard_filtered.png` | Dashboard with machine filter applied |

## How to Re-Import

1. Open Superset (`http://localhost:8088`)
2. Settings → Import Dashboards
3. Upload `fplip_dashboard_export.zip`
4. Re-point to the BigQuery connection (`FPLIP - fplip_gold (api_sa)`)

## Dashboard Structure

| Row | Content |
|-----|---------|
| 1 | Headline KPIs (OEE, Availability, Performance, Quality) |
| 2 | OEE Trend by Machine + OEE by Machine (Ranked) |
| 3 | Loss Attribution by Machine |
| 4 | Scrap by Defect Category, Scrap by Machine, Pass vs Fail Ratio |

## Filters

- **Time Range:** Global date filter affecting all charts
- **Machine ID:** Multi-select machine filter
- **Product ID:** Multi-select product filter

## Date
2026-08-12