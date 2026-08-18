# ADR-001: Data Warehouse Selection

## Status
Accepted (2026-07-22)

## Context
We need a data warehouse for the Factory Performance & Loss Intelligence Platform (FPLIP) that:
- Supports the medallion architecture (Bronze → Silver → Gold)
- Can run for 8-12 weeks of development without incurring cloud costs
- Has no time-bound trial expiration
- Is accessible from Python and orchestration tools

## Decision
Use **Google BigQuery in Sandbox mode** with a GCP project that has **no billing account linked**.

## Rationale
1. **Zero-cost foundation:** BigQuery Sandbox provides 10 GB of active storage and 1 TB of monthly query processing indefinitely — no 30-day or 90-day expiration clock.
2. **Native medallion support:** BigQuery datasets (`fplip_bronze`, `fplip_silver`, `fplip_gold`) directly map to the three layers.
3. **Python ecosystem:** The `google-cloud-bigquery` client library is mature and well-documented.
4. **IAM granularity:** Dataset-scoped IAM bindings allow least-privilege service accounts.

## Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| Snowflake 30-day trial | Time-boxed trial would expire mid-project, killing momentum |
| AWS Redshift/Athena | No indefinite free tier; would require paid accounts |
| Azure Synapse | Requires ADLS Gen2 for staging; adds unnecessary complexity |
| GCP with billing account | Violates the zero-cost requirement; no "unlink billing" path back to Sandbox |

## Consequences
- **Accepted limitations:** Sandbox blocks DML statements (`INSERT`, `UPDATE`, `DELETE`) and streaming inserts. All writes must use idempotent `CREATE OR REPLACE` or partition-decorator patterns.
- **No object storage:** Following Blueprint v3.0, there is no GCS bucket. Data goes directly from local files to BigQuery via the Python client.
- **Single-region constraint:** All datasets are in the `us` multi-region. Cross-dataset queries work natively.

## Real Resource Names (Week 1)
- **Project ID:** `flip-dev-503300`
- **Datasets:** `fplip_bronze`, `fplip_silver`, `fplip_gold`
- **Service Accounts:**
  - `terraform-admin@flip-dev-503300.iam.gserviceaccount.com`
  - `ingestion-sa@flip-dev-503300.iam.gserviceaccount.com`
  - `api-sa@flip-dev-503300.iam.gserviceaccount.com`

## Date
2026-07-22
"@ | Out-File -FilePath docs/adr/ADR-001-warehouse-selection.md -Encoding utf8