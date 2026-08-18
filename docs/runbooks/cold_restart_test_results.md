# Cold-Restart Test Results

## Date
2026-08-09

## Total Time
Test started at: 08/09/2026 03:16:48
Test completed in: 17.698675915 minutes

## Data Verification
| Table | Row Count |
|-------|-----------|
| `fplip_bronze.production_runs` | 50 |
| `fplip_bronze.downtime_events` | 25 |
| `fplip_bronze.qc_inspections` | 25 |
| `fplip_gold.oee_daily` | 22 |
| `fplip_gold.scrap_root_cause_summary` | 11 |

## API Verification
| Endpoint | Status |
|----------|--------|
| `/health` | PASS ({"app":"ok","bigquery":"ok"}) |
| `/oee/daily` | PASS (returned valid rows after granting roles) |
| `/oee/summary` | PASS (returned valid aggregated rows after granting roles) |
| `/scrap/root-cause` | PASS (returned valid rows after granting roles) |

## Deviations Found
| Issue | Fix Applied |
|-------|-------------|
| PROJECT_ID hardcoded in loaders | Updated to fplip-coldstart-test |
| Service account dataset/table permissions | Granted `roles/bigquery.dataViewer` and `roles/bigquery.jobUser` to `api-sa@fplip-coldstart-test.iam.gserviceaccount.com` |

## Overall Status
- [x] PASSED
- [ ] FAILED

## Notes
- `GOOGLE_APPLICATION_CREDENTIALS` environment variable was not set in the Python process used for checks, but the service account key file exists at `secrets/api-sa-key.json`.
- Service account info from local key file: project_id=`fplip-coldstart-test`, client_email=`api-sa@fplip-coldstart-test.iam.gserviceaccount.com`.
- `/health` returned `{"app":"ok","bigquery":"ok"}`.
- After granting `roles/bigquery.dataViewer` and `roles/bigquery.jobUser` to `api-sa@fplip-coldstart-test.iam.gserviceaccount.com`, the API returned valid data for `/oee/daily`, `/oee/summary`, and `/scrap/root-cause`.
