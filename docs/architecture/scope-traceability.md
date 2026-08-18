# Scope and Requirements Traceability

## Section 4 — In-Scope Items

| Item | Status | Location |
|------|--------|----------|
| Bronze layer ingestion | ✅ | `ingestion/` |
| Silver layer transformations | ✅ | `dbt/models/silver/` |
| Gold layer aggregations | ✅ | `dbt/models/marts/gold/` |
| OEE calculation | ✅ | `dbt/models/marts/gold/oee_daily.sql` |
| Scrap root-cause analysis | ✅ | `dbt/models/marts/gold/scrap_root_cause_summary.sql` |
| Data quality tests | ✅ | `dbt/tests/` |
| CI/CD pipeline | ✅ | `.github/workflows/ci.yml` |
| Production orchestration | ✅ | `.github/workflows/production-schedule.yml` |
| FastAPI serving layer | ✅ | `api/` |
| Documentation | ✅ | `docs/` |

## Section 5 — Functional Requirements

| FR | Description | Location |
|----|-------------|----------|
| FR-01 | Extract raw production data | `ingestion/extract_and_load.py` |
| FR-02 | Validate data against contracts | `ingestion/contract_validator.py` |
| FR-03 | Load Bronze tables | `ingestion/bronze_loader.py` |
| FR-04 | Transform to Silver (clean) | `dbt/models/silver/` |
| FR-05 | Build Gold dimensions | `dbt/models/silver/dims/` |
| FR-06 | Build Gold facts | `dbt/models/silver/facts/` |
| FR-07 | Build Gold marts | `dbt/models/marts/gold/` |
| FR-08 | OEE calculation | `oee_daily.sql` |
| FR-09 | Scrap root-cause analysis | `scrap_root_cause_summary.sql` |
| FR-10 | CI/CD pipeline | `.github/workflows/ci.yml` |
| FR-11 | Production orchestration | `.github/workflows/production-schedule.yml` |
| FR-12 | API serving layer | `api/` |
| FR-13 | Data lineage | `dbt docs` (GitHub Pages) |
| FR-14 | Data dictionary | `docs/data_dictionary.md` |

## Out-of-Scope (Section 4)

| Item | Status |
|------|--------|
| Energy Meter Log (Phase 2) | Not implemented (deferred) |
| Employee/Operator Master | Not implemented (out of scope) |
| Maintenance Work Order Log | Not implemented (out of scope) |
| Raw Material Inventory | Not implemented (out of scope) |
| Bill of Materials | Not implemented (out of scope) |
| Power BI Dashboard | Not implemented (out of scope) |

## Completion Status

**All in-scope items are complete. All functional requirements are satisfied.**

## Date
2026-08-09