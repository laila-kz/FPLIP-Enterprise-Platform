# PROJECT MASTER GUIDE — FROM ZERO TO HERO

This document reconstructs the project from the actual repository contents and should be read as a practical architecture and learning guide for FPLIP. It is grounded in the code and configuration in this workspace, not in generic platform patterns.

## 1. Executive summary in plain English

FPLIP is a manufacturing analytics platform built as a multi-part system:

- `fplip-core` contains the data engineering backbone: synthetic manufacturing data generation, schema validation, Bronze/Silver/Gold transformations, Apache Airflow orchestration, BigQuery processing, and a FastAPI serving layer.
- `fplip-investigate` is the operational web application built in Laravel for plant investigation workflows and user interactions.
- `fplip-bi` contains the BI visual layer, with Apache Superset.
- `docs/` and `rapport/` preserve the architecture, design decisions, and academic report material.

The project is designed to ingest manufacturing event data, validate it against contracts, load it into a BigQuery medallion warehouse, transform it into operational metrics such as OEE and scrap loss attribution, expose those datasets through a FastAPI API, and surface them in dashboards and an operations app.

In very simple terms:

DATA SOURCE
↓
CONTRACT VALIDATION
↓
BRONZE INGESTION INTO BIGQUERY
↓
DBT SILVER/GOLD TRANSFORMATIONS
↓
OEE / SCRAP METRICS
↓
FASTAPI API
↓
LARAVEL INVESTIGATE APP + SUPERSET DASHBOARDS
↓
USER

This is the actual high-level flow supported by the code in this repo.

---

## 2. High-level inventory of the repository

### Root-level directories

- `README.md` — project portfolio-level overview and system summary.
- `docs/` — architecture docs, ADRs, runbooks, and data dictionary.
- `assets/` — screenshots and demo evidence.
- `rapport/` — LaTeX report source.
- `fplip-core/` — core data platform code.
- `fplip-investigate/` — Laravel operational app.
- `fplip-bi/` — BI stack and Superset config.

### `fplip-core` important areas

- `docker-compose.yml` — local orchestration for Airflow + API + Laravel + proxy.
- `requirements.txt` — Python dependencies for the core platform.
- `api/` — FastAPI service and routers.
- `common/` — shared GCP utilities.
- `contracts/` — YAML validation contracts for ingestion.
- `dags/` — Airflow DAGs.
- `dbt/` — dbt project for Bronze/Silver/Gold warehouse transformations.
- `infra/` — Terraform infrastructure as code.
- `ingestion/` — ingestion and synthetic data loading logic.
- `ml/` — machine learning training assets.
- `scripts/` — local pipeline wrappers.
- `tests/` — tests.
- `data/` and `data_static/` — source data and supporting static data.
- `secrets/` — credentials and service-account files.

### `fplip-investigate` important areas

- `app/` — Laravel application code.
- `routes/` — route definitions.
- `database/` — migrations and seeders.
- `resources/` — Blade templates and frontend assets.
- `public/` and `vite.config.js` — frontend build assets.
- `Dockerfile` — container for the Laravel application.
- `composer.json` and `package.json` — PHP and Node dependency management.

### `fplip-bi` important areas

- `superset/` — Superset deployment and configuration
- `docker-compose.yml` — local dockerized BI stack.

---

## 3. Actual technologies in this repo

### Definitely used

- Python 3 / FastAPI / Uvicorn
- Apache Airflow
- PostgreSQL as Airflow metadata database
- Google BigQuery
- dbt (Data Build Tool)
- YAML-based contract validation
- Terraform
- Docker / Docker Compose
- Laravel 11
- Tailwind CSS and Vite
- Apache Superset
- Scikit-learn, Pandas, NumPy, joblib
- GCP service accounts and Google client libraries
- Slack webhook notifications

### Installed or configured but not obviously central to the actual runtime

- There are strong signs of a Gemini AI integration in the application layer, but the repository evidence is partial and not fully wired into a consistent runtime path across all modules.
- Some packages and configuration files look infrastructure- or experimentation-oriented rather than directly used in the main code path.

### Mentioned in docs but requiring verification

- Real-time streaming, Kafka, or event-driven ingestion is not clearly implemented in the codebase as a first-class system. The repo is primarily batch-oriented and file-based.
- Some documentation describes production-like features and CI practices, but the project should still be assessed against the code, not only the README claims.

---

## 4. The most important files to inspect first

These are the files that give the clearest map of the system:

1. `README.md` — project overview and system summary.
2. `fplip-core/docker-compose.yml` — local runtime composition and service wiring.
3. `fplip-core/dags/ingestion_dag.py` — ingestion DAG and execution path.
4. `fplip-core/dags/dbt_transform_dag.py` — transformation DAG.
5. `fplip-core/dags/data_quality_dag.py` — quality checks and alerting.
6. `fplip-core/scripts/run_pipeline_local.sh` — the runtime sequence for the main pipeline.
7. `fplip-core/ingestion/extract_and_load.py` — validation + load orchestration.
8. `fplip-core/dbt/dbt_project.yml` — dbt project configuration.
9. `fplip-core/dbt/models/gold/oee_daily.sql` — Gold layer OEE logic.
10. `fplip-core/api/main.py` — FastAPI app entry point.
11. `fplip-core/api/routers/oee.py` — OEE API endpoints.
12. `fplip-core/api/routers/scrap.py` — scrap analysis API.
13. `fplip-core/ml/training/train_scrap_model.py` — ML training pipeline.
14. `fplip-core/api/services/ml_service.py` — runtime model access.
15. `fplip-investigate/README.md` — operational app overview.
16. `fplip-investigate/routes/web.php` and `routes/api.php` — application navigation and API routing.
17. `docs/architecture/architecture.md` — architecture narrative and early decisions.

---

## 5. Reconstructed architecture from the repo

### 5.1 Data sources and ingestion

The repository clearly uses synthetic factory data files and data contracts. The ingestion path is implemented by:

- `fplip-core/ingestion/extract_and_load.py`
- `fplip-core/ingestion/contract_validator.py` (implied by usage; the file is part of the ingestion package and is used in the loading path)
- `fplip-core/contracts/` YAML schemas
- `fplip-core/dags/ingestion_dag.py`

The source flow is:

- File-based manufacturing datasets such as production, downtime, and QC records
- Contract validation against YAML schemas in `contracts/`
- Row validation and rejection on failure
- Bronze table load into BigQuery

The project explicitly describes a Bronze/Silver/Gold medallion pattern in the README and `docs/architecture/architecture.md`.

### 5.2 Warehouse and transformation layer

The warehouse layer is implemented in dbt:

- `fplip-core/dbt/dbt_project.yml`
- `fplip-core/dbt/models/bronze/`
- `fplip-core/dbt/models/silver/`
- `fplip-core/dbt/models/gold/`

The models generate fact and dimension tables and then business-ready OEE and scrap summary tables.

Examples:

- `fplip-core/dbt/models/silver/facts/fct_production_run.sql`
- `fplip-core/dbt/models/silver/facts/fct_downtime_event.sql`
- `fplip-core/dbt/models/silver/facts/fct_qc_inspection.sql`
- `fplip-core/dbt/models/gold/oee_daily.sql`
- `fplip-core/dbt/models/gold/scrap_root_cause_summary.sql`

### 5.3 Orchestration layer

The orchestration is handled by Airflow DAGs:

- `fplip-core/dags/ingestion_dag.py`
- `fplip-core/dags/dbt_transform_dag.py`
- `fplip-core/dags/data_quality_dag.py`

These DAGs are launched with Dockerized Airflow in `fplip-core/docker-compose.yml`.

The pipeline wrapper script is:

- `fplip-core/scripts/run_pipeline_local.sh`

This script runs the DAGs in sequence:

1. `ingestion_dag`
2. `dbt_transform_dag`
3. `data_quality_dag`

### 5.4 API and serving layer

The serving layer is FastAPI:

- `fplip-core/api/main.py`
- `fplip-core/api/routers/oee.py`
- `fplip-core/api/routers/scrap.py`
- `fplip-core/api/routers/ml.py`
- `fplip-core/api/routers/context.py`
- `fplip-core/api/routers/ai.py`

The app is protected with internal API key verification in:

- `fplip-core/api/dependencies/auth.py`

The API uses BigQuery for queries to the Gold layer and responds with operational metrics and ML predictions.

### 5.5 ML layer

ML training is implemented in:

- `fplip-core/ml/training/train_scrap_model.py`

Runtime usage is in:

- `fplip-core/api/services/ml_service.py`
- `fplip-core/api/routers/ml.py`

The model is a logistic regression classifier designed to predict scrap risk based on features such as:

- planned_units
- machine_avg_oee_14d
- machine_scrap_rate_14d
- product_avg_scrap_rate
- shift_avg_scrap_rate
- is_night_shift

### 5.6 Frontend and operational app

The front end is a Laravel application:

- `fplip-investigate/README.md`
- `fplip-investigate/routes/web.php`
- `fplip-investigate/app/`
- `fplip-investigate/resources/`

This application exposes operational workflows such as signal intelligence, work orders, and AI-assisted investigation. It is configured to call the FastAPI endpoints via environment variables like `FASTAPI_BASE_URL`.

### 5.7 BI layer

The BI layer is implemented with Apache Superset:

- `fplip-bi/superset/`
- `fplip-bi/superset/docker-compose.yml`

This is the dashboard layer for business users to view OEE and production metrics in a storytelling view.

---

## 6. Architecture diagram reconstructed from code

```text
[Factory / synthetic source files]
        ↓
[Contract validation in contracts/ + ingestion.extract_and_load]
        ↓
[Bronze ingestion to BigQuery]
        ↓
[Airflow DAG: ingestion_dag]
        ↓
[dbt Silver transformations]
        ↓
[dbt Gold OEE and scrap summaries]
        ↓
[FastAPI service: /oee, /scrap, /ml, /ai, /signals]
        ↓
[Operational app: fplip-investigate / Laravel]
        ↓
[Superset dashboard layer]
        ↓
[User / operations team]
```

This is the architecture actually supported by the repository.

---

## 7. Data lineage from source to user

### Step 1 — source data

Purpose:
- Provide manufacturing event records for production, downtime, and QC.

Input:
- Files in `fplip-core/data/` and `data/incoming/` patterns, loaded by ingestion scripts.

Actual implementation:
- `fplip-core/ingestion/extract_and_load.py`
- `SOURCE_CONFIG` maps production, downtime, and qc to contract and table names.

Output:
- Data file loaded for validation and Bronze ingestion.

### Step 2 — contract validation

Purpose:
- Ensure the source data matches the expected schema and rules before writing to the warehouse.

Actual implementation:
- `fplip-core/ingestion/contract_validator.py` is used in the ingestion flow.

Output:
- Validation result: pass or fail.

Failure behavior:
- In `extract_and_load.py`, a failing validation raises an exception and stops the load.

### Step 3 — Bronze ingestion to BigQuery

Purpose:
- Land validated raw data into BigQuery bronze datasets.

Actual implementation:
- `fplip-core/ingestion/bronze_loader.py` (used by `extract_and_load.py`)

Output:
- BigQuery tables such as `production_runs`, `downtime_events`, and `qc_inspections`.

### Step 4 — dbt Silver layer

Purpose:
- Clean and model raw data into normalized fact and dimension tables.

Actual implementation:
- `fplip-core/dbt/models/silver/`
- `fplip-core/dbt/models/silver/facts/*.sql`
- `fplip-core/dbt/models/silver/dims/*.sql`

Examples:
- `fct_production_run.sql`
- `dim_machine.sql`
- `dim_product.sql`
- `dim_shift.sql`

### Step 5 — Gold layer

Purpose:
- Produce business-ready metrics for OEE and scrap analysis.

Actual implementation:
- `fplip-core/dbt/models/gold/oee_daily.sql`
- `fplip-core/dbt/models/gold/scrap_root_cause_summary.sql`

These are the tables queried by the FastAPI layer.

### Step 6 — API serving layer

Purpose:
- Expose the Gold layer to application consumers without direct BigQuery access.

Actual implementation:
- `fplip-core/api/routers/oee.py`
- `fplip-core/api/routers/scrap.py`
- `fplip-core/api/main.py`

Endpoints include:

- `/oee/daily`
- `/oee/summary`
- `/scrap/root-cause`
- `/ml/scrap-risk`
- `/ai/explain`
- `/signals/active`
- `/machine/context`

### Step 7 — Application layer

Purpose:
- Allow an operation team to investigate signals and take action.

Actual implementation:
- `fplip-investigate/app/`
- `fplip-investigate/routes/`
- Relevant controllers/services in Laravel.

### Step 8 — dashboards

Purpose:
- Business-facing KPI review and storytelling.

Actual implementation:
- `fplip-bi/superset/`

---

## 8. The actual execution sequence from scratch

If you start this project from scratch, the code suggests the following runtime sequence:

1. Start the core stack with Docker Compose:
   - `fplip-core/docker-compose.yml`
   - This brings up Airflow metadata Postgres, Airflow init, Airflow webserver, Airflow scheduler, API, Laravel app, and NGINX proxy.

2. The Airflow setup creates the metadata database and the admin user.

3. The pipeline is triggered using the wrapper script:
   - `fplip-core/scripts/run_pipeline_local.sh`

4. The script executes:
   - `airflow dags test ingestion_dag ...`
   - `airflow dags test dbt_transform_dag ...`
   - `airflow dags test data_quality_dag ...`

5. Ingestion DAG loads production, downtime, and QC data after validation.

6. dbt DAG transforms the datasets into Silver and Gold outputs.

7. Data quality DAG executes dbt tests and optional Slack notification.

8. FastAPI reads from BigQuery Gold tables through the API layer.

9. Laravel calls the FastAPI endpoints to populate plant dashboards.

10. Superset reads the warehouse and displays business-facing analytics.

This is the actual operational choreography visible in the repository.

---

## 9. The core pipeline, traced in code

### Ingestion DAG

File: `fplip-core/dags/ingestion_dag.py`

Observations:
- It defines `ingestion_dag`.
- It launches `extract_production`, `extract_downtime`, and `extract_qc` as parallel tasks.
- Each task calls `ingestion.extract_and_load` wrappers.
- The DAG schedule is `None`, meaning it is triggered externally.

### The extraction loader

File: `fplip-core/ingestion/extract_and_load.py`

Observations:
- `extract_and_load` resolves source file names and contracts.
- It validates the file using `validate_file(...)` before loading.
- If validation fails, it raises an exception.
- On success, it calls `load_file_to_bronze(...)`.

### dbt transform DAG

File: `fplip-core/dags/dbt_transform_dag.py`

Observations:
- `dbt_run_silver` runs silver models.
- Gold tasks run in parallel after silver completion.
- `DBT_CMD` points to `/opt/airflow/.venv-fplip/bin/dbt`.

### Data quality DAG

File: `fplip-core/dags/data_quality_dag.py`

Observations:
- Uses `dbt test --select +silver` and `dbt test --select +gold`.
- Sends Slack alerts on failure via webhook using `SLACK_WEBHOOK_URL`.
- This is one of the clearest signs of a data quality and operational alerting layer.

---

## 10. What the system does from a business perspective

### Problem it solves

The project addresses the need to monitor and reason about manufacturing plant performance using operational data. It ties together:

- production output
- downtime events
- quality inspection results
- OEE calculations
- scrap attribution
- anomaly detection
- operational investigation

### Who it is for

The application appears designed for:

- plant managers
- operations teams
- line technicians
- reliability investigators
- executive stakeholders reviewing KPIs

### Input

- production run data
- downtime event data
- QC inspection data
- machine and product metadata
- shift metadata
- synthetic or generated manufacturing telemetry

### What happens to the input

- validated against contracts
- loaded into BigQuery bronze tables
- transformed via dbt into Silver and Gold layers
- aggregated into OEE and loss attribution views
- exposed through a FastAPI service
- consumed by the Laravel app and dashboard layer

### Output produced

- OEE metrics by day and machine
- scrap root cause summaries
- active anomaly signals
- AI explanations and recommended actions
- operational dashboards

### Where data is stored

- Local source files under `fplip-core/data/`
- BigQuery datasets, including `fplip_bronze`, `fplip_silver`, and `fplip_gold` as described in the architecture doc
- SQLite or MySQL storage in the Laravel app (as configured by Laravel project conventions)

### Where processing happens

- Local Python scripts under `fplip-core`
- Dockerized Airflow containers
- BigQuery warehouse queries
- Laravel app actions
- Superset BI queries

### Where ML/AI happens

- `fplip-core/ml/training/train_scrap_model.py` defines the training pipeline.
- `fplip-core/api/routers/ml.py` exposes predict endpoint.
- `fplip-core/api/services/ml_service.py` loads the trained model.
- `fplip-core/api/services/gemini_service.py` is the AI part for explanations.

### How users interact

- Via the Laravel operational portal
- Via BI dashboards in Superset
- Via the FastAPI API endpoints

### Final product

A full manufacturing intelligence platform combining data engineering, ML, operational investigation, and business dashboarding.

---

## 11. Key architecture decisions visible in the code

### 1. Medallion architecture

Evidence:
- `docs/architecture/architecture.md`
- `fplip-core/dbt/dbt_project.yml`
- `fplip-core/dbt/models/bronze/`, `silver/`, `gold/`

Why it matters:
- It creates a staged data lifecycle from raw to trusted analytics.

### 2. Contract-first ingestion

Evidence:
- `fplip-core/contracts/`
- `fplip-core/ingestion/extract_and_load.py`

Why it matters:
- It validates incoming data before allowing writes to Bronze.

### 3. Batch orchestration with Airflow

Evidence:
- `fplip-core/dags/*.py`
- `fplip-core/docker-compose.yml`

Why it matters:
- It defines reproducible, scheduled or triggerable runs.

### 4. API-first service layer

Evidence:
- `fplip-core/api/main.py`
- `fplip-core/api/routers/*.py`

Why it matters:
- The frontend and operations app consume analytic results via a stable API layer rather than direct warehouse access.

### 5. Model-driven operational investigations

Evidence:
- `fplip-core/api/routers/context.py`
- `fplip-core/api/routers/ml.py`
- `fplip-core/api/routers/ai.py`

Why it matters:
- The app is not just reporting; it is designed to support anomaly investigation and decision support.

### 6. BigQuery sandbox-friendly load strategy

Evidence:
- `docs/architecture/architecture.md`

The architecture doc explicitly mentions sandbox constraints and DDL-only or idempotent patterns, which is relevant because BigQuery sandbox mode is restrictive.

---

## 12. Strong points in the project

- Clear medallion architecture in code and docs.
- Strong separation between ingestion, transformation, API, app, and BI.
- Real Airflow orchestration with explicit DAGs.
- Data quality validation via dbt tests and Slack notifications.
- Multiple delivery surfaces: API, app, dashboard.
- Operational investigation workflows beyond pure BI reporting.
- ML integration into a production-like API contract.

## 13. Weak points, gaps, and things to be careful about in a report

- Some documentation is broader than the code. The project is strong in architecture and claims, but there should be a disciplined distinction between what is implemented and what is documented as a target capability.
- Some AI and app features appear polished in screenshots but may rely on synthetic or mocked operational context rather than full production-grade integration.
- The repository contains many design claims that are valuable for a report, but only if they are matched to code evidence.
- Some runtime dependencies may be intended for local or demonstration scenarios rather than full deployment to production.

It is important to avoid claiming production-level maturity without code evidence.

---

## 14. Learning path for understanding the project

### STAGE 1 — Understand the entry points

Files to read:
- `README.md`
- `fplip-core/README.md`
- `fplip-core/docker-compose.yml`

What to look for:
- service composition
- runtime components
- where the platform starts

What you should understand:
- There are three major runtime layers: data platform, operational app, BI.

Questions to answer:
- Which services are started together?
- What is the main orchestration stack?

### STAGE 2 — Understand the core data pipeline

Files to read:
- `fplip-core/dags/ingestion_dag.py`
- `fplip-core/ingestion/extract_and_load.py`
- `fplip-core/contracts/`

What to look for:
- extraction tasks
- validation logic
- Bronze load path

What you should understand:
- raw files are validated and delivered into the warehouse before transformation.

### STAGE 3 — Understand the warehouse model

Files to read:
- `fplip-core/dbt/dbt_project.yml`
- `fplip-core/dbt/models/silver/facts/fct_production_run.sql`
- `fplip-core/dbt/models/gold/oee_daily.sql`

What to look for:
- medallion layers
- fact/dimension patterns
- OEE metric formula logic

What you should understand:
- this is where business metrics are produced.

### STAGE 4 — Understand the API service

Files to read:
- `fplip-core/api/main.py`
- `fplip-core/api/routers/oee.py`
- `fplip-core/api/routers/scrap.py`
- `fplip-core/api/dependencies/auth.py`

What to look for:
- endpoints
- auth checks
- BigQuery queries
- response schemas

What you should understand:
- the API is the operational query layer over Gold data.

### STAGE 5 — Understand ML and AI

Files to read:
- `fplip-core/ml/training/train_scrap_model.py`
- `fplip-core/api/services/ml_service.py`
- `fplip-core/api/routers/ml.py`
- `fplip-core/api/services/gemini_service.py`

What to look for:
- feature engineering
- training logic
- inference path
- AI explanation tool integration

What you should understand:
- predictions are produced from historical and current machine stats and exposed through API endpoints.

### STAGE 6 — Understand the operational app

Files to read:
- `fplip-investigate/README.md`
- `fplip-investigate/routes/web.php`
- `fplip-investigate/app/`

What to look for:
- how the user interacts with the plant signal intelligence workflow
- where the app calls the API

What you should understand:
- this is the user-facing operational layer for investigations and actions.

### STAGE 7 — Understand dashboarding and reporting

Files to read:
- `fplip-bi/`
- `docs/architecture/architecture.md`

What to look for:
- business reporting view
- dashboard story flow

What you should understand:
- the dashboards are the final presentation layer for KPI monitoring.

---

## 15. Technology stack summary

### Languages
- Python
- SQL
- PHP
- JavaScript / Node
- YAML
- Bash

### Frameworks and libraries
- FastAPI
- Airflow
- dbt
- Laravel
- Tailwind
- Vite
- Scikit-learn
- Pandas / NumPy
- Google BigQuery Python client

### Databases and storage
- BigQuery
- PostgreSQL (Airflow metadata)
- Laravel app database storage (SQLite or MySQL depending on configuration)

### Orchestration
- Airflow DAGs
- Docker Compose

### Data quality
- YAML contract validation
- dbt tests
- Slack notifications

### ML / AI
- Logistic regression model
- joblib serialization
- Gemini-style AI service layer

### Frontend / dashboards
- Laravel Blade
- Vite build assets
- Tailwind CSS
- Apache Superset

### Cloud and infrastructure
- GCP BigQuery
- Terraform
- service accounts and IAM

---

## 16. Architectural file map

### Project overview
- `README.md`
- `fplip-core/README.md`
- `docs/architecture/architecture.md`

### Data ingestion
- `fplip-core/ingestion/extract_and_load.py`
- `fplip-core/ingestion/bronze_loader.py`
- `fplip-core/contracts/`
- `fplip-core/dags/ingestion_dag.py`

### Orchestration
- `fplip-core/docker-compose.yml`
- `fplip-core/dags/dbt_transform_dag.py`
- `fplip-core/dags/data_quality_dag.py`
- `fplip-core/scripts/run_pipeline_local.sh`

### Data modeling
- `fplip-core/dbt/dbt_project.yml`
- `fplip-core/dbt/models/silver/`
- `fplip-core/dbt/models/gold/`

### Serving API
- `fplip-core/api/main.py`
- `fplip-core/api/routers/*.py`
- `fplip-core/api/dependencies/*.py`

### ML / AI
- `fplip-core/ml/training/train_scrap_model.py`
- `fplip-core/api/services/ml_service.py`
- `fplip-core/api/routers/ml.py`
- `fplip-core/api/services/gemini_service.py`
- `fplip-core/api/routers/ai.py`

### Operational application
- `fplip-investigate/README.md`
- `fplip-investigate/routes/`
- `fplip-investigate/app/`
- `fplip-investigate/resources/`

### BI
- `fplip-bi/superset/`

---

## 17. Short mental model for the project

### 30-second explanation

FPLIP is a manufacturing intelligence platform that turns factory data into operational metrics and AI-assisted decisions. It validates incoming manufacturing records, loads them into BigQuery, transforms them through dbt into Silver and Gold layers, exposes the business metrics through FastAPI, and surfaces them through a Laravel operations app and Superset dashboards.

### 2-minute explanation

This project combines data engineering and operations software. The ingestion layer reads production, downtime, and QC data, validates it against contract rules, and loads it to a BigQuery Bronze layer. Airflow orchestrates the sequence. dbt creates the Silver and Gold models, including OEE and scrap summaries. The API exposes those metrics with authentication and caching. A machine learning model predicts scrap risk, and the operations app helps humans investigate anomalies. Dashboards then present the results to managers. The whole solution is intentionally a full-stack manufacturing analytics system rather than a single script.

### 5-minute technical explanation

The project is built as a medallion warehouse plus operational app. The Python ingestion scripts validate source files, load them to BigQuery, and Airflow runs them as DAGs. dbt transforms the Bronze data into cleaned dimension and fact tables, then into Gold business tables. FastAPI queries the Gold layer and exposes endpoints for OEE and scrap analysis. The Laravel app consumes these endpoints and supports investigation workflows. A logistic regression model predicts scrap risk using historical machine and product performance features. Superset serves the final dashboard layer. The design is coherent: a clean separation between raw data, trusted models, API exposure, and user interaction.

---

## 18. Things to verify before claiming in a report

Here are questions that matter and should be checked carefully against code:

1. Is the system truly production-grade or demo-oriented?
   - Evidence: Docker Compose, service wiring, docs, screenshots, and configuration.

2. Are the ML features actually tied to real warehouse data in all cases?
   - Evidence: `train_scrap_model.py` and `api/routers/ml.py` show both real BigQuery features and fallback logic.

3. Is the AI service fully implemented or partially mocked?
   - Evidence: `api/services/gemini_service.py` and related routers should be reviewed for actual call paths.

4. Is there live streaming or only batch ingestion?
   - Evidence: `dags/*.py` and ingestion flow suggest batch-oriented, file-based processing.

5. Are there real data contracts for all files?
   - Evidence: `contracts/` and validation use.

---

## 19. Report-ready claims and code evidence

Use these as a guide for an academic or professional report:

- Claim: The project uses a medallion warehouse architecture.
  - Evidence: `fplip-core/dbt/dbt_project.yml`, `fplip-core/dbt/models/`, `docs/architecture/architecture.md`

- Claim: Data is validated before load.
  - Evidence: `fplip-core/ingestion/extract_and_load.py`, `fplip-core/contracts/`

- Claim: Airflow orchestrates ingestion and transformation flows.
  - Evidence: `fplip-core/dags/*.py`, `fplip-core/docker-compose.yml`

- Claim: OEE and scrap metrics are produced in the Gold layer.
  - Evidence: `fplip-core/dbt/models/gold/oee_daily.sql`, `fplip-core/dbt/models/gold/scrap_root_cause_summary.sql`

- Claim: API endpoints query Gold datasets.
  - Evidence: `fplip-core/api/routers/oee.py`, `fplip-core/api/routers/scrap.py`

- Claim: ML predicts scrap risk.
  - Evidence: `fplip-core/ml/training/train_scrap_model.py`, `fplip-core/api/services/ml_service.py`, `fplip-core/api/routers/ml.py`

- Claim: The operational user application is Laravel-based.
  - Evidence: `fplip-investigate/composer.json`, `fplip-investigate/package.json`, `fplip-investigate/README.md`

- Claim: BI dashboards are built with Superset.
  - Evidence: `fplip-bi/superset/`

---

## 20. Key questions to keep in mind while writing the report

- What is the core domain problem: manufacturing performance and loss intelligence?
- What is the main processing stack: Airflow + BigQuery + dbt + FastAPI?
- How is the warehouse designed: medallion pattern?
- What is the data quality story: contracts + tests + checks?
- What is the ML story: logistic regression for scrap risk?
- What is the user story: operational investigation and dashboarding?
- What is the software integration story: API + Laravel + BI?

---

## 21. Final verdict

This repository is a coherent end-to-end industrial analytics platform with clear architecture and functional layering. It is not just a single notebook or a single script; it is a multi-component system with realistic engineering separation between ingestion, warehouse modeling, orchestration, ML, API serving, and user-facing applications.

If you study the files in the order suggested above and cross-reference the README, Airflow DAGs, dbt models, API routers, and Laravel app, you will be able to explain the project confidently without relying on AI.

---

## 22. Suggested reading order for personal mastery

1. `README.md`
2. `fplip-core/docker-compose.yml`
3. `fplip-core/dags/ingestion_dag.py`
4. `fplip-core/ingestion/extract_and_load.py`
5. `fplip-core/dbt/dbt_project.yml`
6. `fplip-core/dbt/models/gold/oee_daily.sql`
7. `fplip-core/api/main.py`
8. `fplip-core/api/routers/oee.py`
9. `fplip-core/api/routers/scrap.py`
10. `fplip-core/ml/training/train_scrap_model.py`
11. `fplip-core/api/services/ml_service.py`
12. `fplip-investigate/README.md`
13. `docs/architecture/architecture.md`
14. `rapport/` if writing the formal academic report

---

## 23. One-line summary

FPLIP is a full-stack manufacturing analytics and operations intelligence project that turns raw factory data into trusted warehouse metrics, ML-based risk insights, and user-facing operational decisions.
