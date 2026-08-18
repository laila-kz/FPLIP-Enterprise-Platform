# FPLIP BI & Dashboards (Apache Superset)

This component hosts the BI analytics and dashboard visualizations for the **Factory Performance & Loss Intelligence Platform (FPLIP)**.

---

## Features & Dashboards
- **Overall Equipment Effectiveness (OEE) Dashboard** — Track Availability, Performance, and Quality components across lines and shifts.
- **Scrap Analysis & Pareto Charts** — Identify high-yield loss defect types and scrap risk trends.
- **Downtime & Loss Attribution** — Analyze unplanned downtime events categorized by root cause.
- **Real-Time Operational Monitoring** — Visual insights generated directly from Gold BigQuery data warehouse tables.

---

## Quick Start (Docker Compose)

To spin up Apache Superset locally:

```bash
cd fplip-bi/superset
docker compose up -d
```

Access the Superset UI at `http://localhost:8088`.
Default credentials: `admin` / `admin`.

---

## Data Source Connection
Connect Superset to BigQuery Gold dataset using standard SQLAlchemy connection string:

```text
bigquery://<GCP_PROJECT_ID>/fplip_gold?credentials_path=/app/secrets/key.json
```
