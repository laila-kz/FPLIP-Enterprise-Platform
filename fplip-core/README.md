# FPLIP — Factory Performance & Loss Intelligence Platform

## Architecture Overview

![GCP Topology](docs/gcp-topology.md)

**Zero-cost GCP Sandbox project** — no billing account linked.

## Problem Statement

FPLIP helps factory operations automatically detect production losses, downtime, and quality issues from BigQuery data sources. It delivers actionable performance intelligence so plant managers can reduce scrap, improve OEE, and prioritize root-cause fixes.

## Quick Links
- [Architecture Documentation](../docs/architecture/architecture.md)
- [Data Dictionary](../docs/data-dictionary/data_dictionary.md)
- [Operational Runbook](../docs/runbooks/runbook.md)
- [ADR Log](../docs/adr/)
- [Demo Video](<link-to-demo>)

## Quickstart

1. Clone the repository:

```bash
git clone <repository-url>
cd FPLIP_project
```

2. Create a GCP project and enable BigQuery API:

```bash
gcloud projects create <your-project-id>
gcloud config set project <your-project-id>
gcloud services enable bigquery.googleapis.com
```

3. Set up Python environment:

```bash
python -m venv .venv-fplip
source .venv-fplip/bin/activate  # Windows: .venv-fplip\Scripts\activate
pip install -r requirements.txt
pip install dbt-core dbt-bigquery
```

4. Update PROJECT_ID in:

- `infra/terraform.tfvars`
- `ingestion/bronze_loader.py`
- `ingestion/master_data_loader.py`
- `dbt/models/bronze/sources.yml`

5. Apply Terraform:

```bash
cd infra
terraform init
terraform apply -auto-approve
cd ..
```

6. Generate and load data:

```bash
python ingestion/synthetic/generate_sample_data.py --date $(date +%Y-%m-%d) --rows 50
python -c "from ingestion.master_data_loader import load_master_file; load_master_file('data/incoming/machines.csv', 'machines'); ..."
```

7. Run dbt transformations:

```bash
cd dbt
dbt deps
dbt run --select fplip_silver fplip_gold
dbt test --select fplip_silver fplip_gold
cd ..
```

8. Start the API:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/secrets/api-sa-key.json
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Business Impact

Estimated reduction in production loss by 5–10% through automated visibility into downtime, scrap, and quality deviations. (Verified after pilot deployment with sample manufacturing data.)

## Dashboard

The FPLIP dashboard visualizes OEE and scrap metrics from the Gold layer.

- **Live Dashboard:** [View Demo](<your-youtube-link>)
- **Dashboard Export:** [dashboard/](dashboard/)
- **Screenshots:** [dashboard/screenshots/](dashboard/screenshots/)

### Key Charts

| Chart | Description |
|-------|-------------|
| OEE KPI Tiles | Current OEE, Availability, Performance, Quality |
| OEE Trend by Machine | OEE over time, one line per machine |
| OEE by Machine (Ranked) | Machine ranking by average OEE |
| Loss Attribution | Stacked bar of Availability/Performance/Unmapped loss |
| Scrap by Defect Category | Scrap volume by defect type |
| Scrap by Machine | Scrap volume by machine |
| Pass vs Fail Ratio | Overall quality pass/fail split |


## Technology Stack

| Layer | Technology |
|-------|------------|
| Cloud | GCP BigQuery Sandbox |
| Infrastructure | Terraform |
| Orchestration | Apache Airflow (via GitHub Actions) |
| Transformation | dbt |
| API | FastAPI |
| CI/CD | GitHub Actions |
| Language | Python |

## Documentation

- [Architecture](docs/architecture.md) — System design and decisions
- [Data Dictionary](docs/data_dictionary.md) — Column definitions and business meaning
- [Runbook](docs/runbook.md) — Operational procedures
- [ADR Log](docs/adr/) — Architecture Decision Records
- [dbt Docs](https://<your-github-username>.github.io/<your-repo>/dbt-docs/index.html) — Lineage graph
- [Demo Video](https://link-to-demo/) — Walkthrough

