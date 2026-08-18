# FPLIP Architecture — Week 1 Foundation

## Overview
This document captures the real resource names and architectural decisions made during Week 1.

## System Overview
FPLIP is a medallion-style analytics platform that ingests factory floor, downtime, and quality data into a BigQuery Sandbox project, transforms it through Bronze/Silver/Gold layers, and exposes metrics through a FastAPI service. The system is designed for zero-cost experimentation with strict sandbox and IAM constraints.

## Cloud Foundation

| Component | Name | Notes |
|-----------|------|-------|
| GCP Project | `flip-dev-503300` | Sandbox mode — no billing account linked |
| Billing Status | No billing account | Confirmed via Billing page |

## BigQuery Datasets

| Dataset | Purpose | Location | Status |
|---------|---------|----------|--------|
| `fplip_bronze` | Raw ingested data | `us` | Created |
| `fplip_silver` | Cleaned/transformed | `us` | Created |
| `fplip_gold` | Aggregated/business-ready | `us` | Created |

## Service Accounts

| Account | Purpose | Permissions |
|---------|---------|-------------|
| `terraform-admin` | Terraform IaC execution | `bigquery.admin`, `iam.serviceAccountAdmin` (project-level) |
| `ingestion-sa` | Airflow ingestion & dbt | `bigquery.dataEditor` on all three datasets + `bigquery.jobUser` (project-level) |
| `api-sa` | Read-only API service | `bigquery.dataViewer` on `fplip_gold` + `bigquery.jobUser` (project-level) |

## IAM and Security

- `terraform-admin` is used only for infrastructure provisioning and has project-level admin rights for BigQuery and service account management.
- `ingestion-sa` is scoped to dataset write access and project-level job execution in order to load data and run dbt jobs.
- `api-sa` is scoped to read-only Gold dataset access and BigQuery job execution required by the API.
- `API_KEY` is stored in environment variables and validated by FastAPI for app-level authentication.
- BigQuery Sandbox prohibits DML statements, so all writes use DDL or idempotent load patterns.

## Dataset Source Files

We have two environment-specific datasets:

| Environment | Location | Row Count | Purpose |
|-------------|----------|-----------|---------|
| Development | `data/development/` | ~1,000 rows | Local testing |
| Production | `data/production/` | ~40,000 rows | Production-realistic |

### Files per environment (10 files):
- **Dimensions:** `dim_date`, `dim_defect_type`, `dim_downtime_reason`, `dim_machine`, `dim_operator`, `dim_product`, `dim_shift`
- **Facts:** `fct_downtime_event`, `fct_production_run`, `fct_qc_inspection`

## Key Constraints

| Constraint | Impact |
|------------|--------|
| BigQuery Sandbox mode | No DML statements. Use `CREATE OR REPLACE` or partition-decorator pattern. |
| No object storage | Data loaded directly from local files to BigQuery via Python client. |
| Single-region (us) | All datasets in `us` multi-region for cross-dataset query support. |

## Week 1 Deliverables

- ✅ GCP project created, no billing account
- ✅ BigQuery API enabled, Sandbox confirmed
- ✅ `gcloud` CLI installed and authenticated
- ✅ Repository scaffolded with `.gitignore`
- ✅ `terraform-admin` service account created
- ✅ Three BigQuery datasets provisioned via Terraform
- ✅ `ingestion_sa` and `api_sa` created with verified least-privilege IAM
- ✅ Data contracts defined from Source Data Contract document
- ✅ Local Python environment configured
- ✅ Complete synthetic dataset generated (development + production)
- ✅ End-to-end connectivity test passing
- ✅ ADR-001 and architecture document created

## Next Steps (Week 2)
- Airflow local setup (Docker Compose)
- Bronze ingestion DAGs with partition-decorator pattern
- Load development dataset into BigQuery



## Bronze Layer

### Flow Diagram
Source CSV Files (data/incoming/)
↓
Contract Validation (contract_validator.py)
↓
Idempotent Load (bronze_loader.py)
↓
Time-Partitioned Bronze Tables (fplip_bronze.*)



### Bronze Tables

| Table | Source | Partitioning | Clustering |
|-------|--------|--------------|------------|
| `production_runs` | Production Run Log | `_ingested_at` (DAY) | `machine_id`, `run_date` |
| `downtime_events` | Downtime Event Log | `_ingested_at` (DAY) | `machine_id`, `event_date` |
| `qc_inspections` | QC Inspection Log | `_ingested_at` (DAY) | `inspection_date` |

### Idempotent Load Pattern

All Bronze loads use the **partition-decorator + WRITE_TRUNCATE** pattern:
- Target: `table$YYYYMMDD`
- Write disposition: `WRITE_TRUNCATE`
- Result: Safe to rerun any date without duplication

### Key Files
- `ingestion/bronze_schema.py` — Explicit table schemas
- `ingestion/bronze_loader.py` — Idempotent load logic
- `ingestion/extract_and_load.py` — Validation + load orchestration
- `dags/extract_*.py` — Airflow DAGs

### Verification
- ✅ Idempotency verified: rerun does not duplicate rows
- ✅ Failure path verified: malformed data is rejected with specific error
- ✅ Integration tests automated

## Silver Layer

### Purpose
The Silver layer cleans and validates Bronze data, applies contract rules and edge-case handling, and prepares fact-level tables using DDL-only transformations.

### Key Models
- `stg_production_runs`
- `stg_downtime_events`
- `stg_qc_inspections`
- `dim_machine`
- `dim_product`
- `fct_production_run`
- `fct_downtime_event`
- `fct_qc_inspection`

### Silver Design Notes
- Uses `CREATE OR REPLACE TABLE AS SELECT` for safe Sandbox writes
- Implements hand-rolled DDL-only SCD2 history tracking for dimensions
- Excludes invalid runs with NULL/zero duration from performance calculations
- Ensures fact grain consistency for downstream OEE metrics

## Gold Layer

### Purpose
The Gold layer produces business-ready marts for operations and reporting.

### Gold Models
- `oee_daily`
- `scrap_root_cause_summary`

### Gold Design Notes
- `oee_daily` includes availability, performance, quality, and loss attribution metrics
- `scrap_root_cause_summary` surfaces root-cause defect metrics for manufacturing scrap
- Gold outputs are optimized for BI consumption with simple joins and daily aggregation

## CI/CD

### CI Architecture

GitHub PR → GitHub Actions → fplip-ci project
↓
Lint (ruff, sqlfluff)
Contract Check (pytest)
dbt-test (ephemeral per-PR dataset)
Terraform Plan (drift detection)
Docker Build (image verification)


### Per-PR Ephemeral Dataset

Each pull request gets its own isolated dataset:
- Name: `fplip_ci_pr_<PR_NUMBER>`
- Seeded with synthetic fixtures (8 tables)
- `dbt build` runs against it
- Teardown happens via `if: always()` even on failure

### CI Service Account

- Name: `ci-service-account@fplip-ci.iam.gserviceaccount.com`
- Role: `roles/bigquery.admin` on `fplip-ci` project only
- **NOT** present in production project


## Week 6: Production Orchestration

### Three-DAG Structure

| DAG | Purpose | Tasks |
|-----|---------|-------|
| `ingestion_dag` | Bronze ingestion | extract_production, extract_downtime, extract_qc (parallel) |
| `dbt_transform_dag` | Silver/Gold transformations | dbt_run_silver → dbt_run_gold_oee + dbt_run_gold_scrap (parallel) |
| `data_quality_dag` | Quality validation | dbt_test_silver → dbt_test_gold → notify_success |

### Chaining Mechanism

DAGs are chained at the shell level using `scripts/run_pipeline.sh`:
```bash
airflow dags test ingestion_dag <date> &&
airflow dags test dbt_transform_dag <date> &&
airflow dags test data_quality_dag <date>
```

## API Layer

### API Overview

The FPLIP API provides a RESTful interface to Gold layer data, enabling dashboards and external tools to query OEE and scrap metrics without direct BigQuery access.

### Endpoints

| Endpoint | Method | Description | Query Parameters |
|----------|--------|-------------|------------------|
| `/health` | GET | Health check | None |
| `/oee/daily` | GET | Daily OEE data | `start_date`, `end_date`, `machine_id` (optional) |
| `/oee/summary` | GET | OEE summary by machine | `start_date`, `end_date`, `machine_id` (optional) |
| `/scrap/root-cause` | GET | Scrap root cause analysis | `start_date`, `end_date`, `machine_id`, `product_id`, `defect_category` |

### Authentication

- **GCP Authentication:** `api_sa` service account with:
  - `BigQuery Data Viewer` on `fplip_gold`
  - `BigQuery Job User` at project level
- **App-Level Authentication:** `X-API-Key` header (single static key)

### Caching

- **Type:** In-memory TTL cache
- **TTL:** 4 hours (14,400 seconds)
- **Key:** MD5 hash of endpoint + parameters
- **Performance:** 94-263x speedup on cache hits

### Deployment

- **Container:** Docker via `docker compose up api`
- **Credentials:** Volume-mounted (never baked into image)
- **Port:** 8000

### Performance Metrics

| Endpoint | Cache-Cold | Cache-Warm | Speedup |
|----------|------------|------------|---------|
| `/oee/daily` | 4.447s | 0.017s | 263x |
| `/oee/summary` | 1.619s | 0.017s | 94x |
| `/scrap/root-cause` | 1.624s | 0.008s | 192x |

### ADRs

- ADR-001: Data Warehouse Selection
- ADR-002: Idempotent Bronze Loading Pattern
- ADR-003: dbt Snapshots Blocked by BigQuery Sandbox DML Restriction
- ADR-004: Hand-Rolled DDL-Only SCD2 History Tracking
- ADR-005: Week 3 Consistency Review
- ADR-006: Fact Grain Validation & Derivation Rule
- ADR-007: Foundation Phase Consistency Review
- ADR-008: Gold Dimension Join Pattern
- ADR-009: OEE Edge Case Handling
- ADR-010: Data Quality Findings
- ADR-011: Loss Attribution Output Shape
- ADR-012: Week 6 DAG Design — Three-DAG Structure
- ADR-013: Production Schedule Cron Time
- ADR-014: Airflow Executor Choice for Production
- ADR-015: Slack Alerting Split
- ADR-016: API Key Storage
- ADR-017: Caching TTL