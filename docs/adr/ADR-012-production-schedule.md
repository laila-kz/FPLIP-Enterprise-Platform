# ADR-012: Production Schedule Cron Time

## Status
Accepted (2026-08-05)

## Decision
The production pipeline runs daily at **5:05 AM UTC**.

## Reasoning
- Morocco is UTC+1 year-round (since 2018, no DST)
- 5:05 AM UTC = 6:05 AM Morocco time
- Factory shift starts at 6:00 AM, so data should be ready for morning review
- 5-minute buffer accounts for any timezone drift

## Implementation
- GitHub Actions cron: `5 5 * * *`
- `workflow_dispatch` also available for manual runs

## Verification
- Confirmed by triggering `production-schedule.yml` manually
- Execution time: ~6m 38s (well within GitHub Actions free tier limits)
- Production tables updated:
  - `oee_daily`: 2026-08-05 17:51:30
  - `scrap_root_cause_summary`: 2026-08-05 17:51:41

## Environment Isolation
- Production project (`flip-dev-503300`): ✅ Updated
- CI project (`fplip-ci`): ✅ Unchanged (only CI datasets present)

## Date
2026-08-05