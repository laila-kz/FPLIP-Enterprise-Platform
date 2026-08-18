# 🏭 Factory Performance & Loss Intelligence Platform (FPLIP)

An end-to-end Enterprise Data Platform, Machine Learning Engine, Operational Web Application, and Business Intelligence Visualization Suite built for real-time manufacturing performance monitoring, automated loss attribution, and AI-assisted investigation workflows.

---

## 🌟 Architecture Overview

```mermaid
flowchart TD
    subgraph Data Sources & Ingestion
        A1[Factory IoT Sensors / Synthetic Data Generator] -->|CSVs| B1[Bronze Ingestion Engine]
        B1 -->|Contract Validation| B2[BigQuery Bronze Layer]
    end

    subgraph Data Transformation & Warehouse (fplip-core)
        B2 -->|dbt Models| C1[Silver Layer Cleaned & Modelled]
        C1 -->|dbt Transformations| C2[Gold Layer OEE & Loss Attribution Data Mart]
        C2 -->|Scikit-learn ML Pipeline| C3[Scrap Risk Classification Model]
    end

    subgraph Serving & Execution Layer
        C2 --> D1[FastAPI High-Performance Serving API]
        C3 --> D1
        D1 -->|Cached Endpoints| E1[Laravel Investigate Operational App]
        C2 -->|SQLAlchemy / BigQuery| E2[Apache Superset BI Dashboards]
    end

    subgraph Workflow Orchestration
        F1[Apache Airflow Docker DAGs] -->|Triggers & Validates| B1
        F1 -->|Runs| C1
    end
```

---

## 🛠️ Tech Stack & Key Technologies

| Category | Technologies |
| :--- | :--- |
| **Data Platform & Warehouse** | Google Cloud BigQuery, dbt (Data Build Tool), YAML Data Contracts |
| **Workflow Orchestration** | Apache Airflow (Dockerized LocalExecutor), Python 3.10 |
| **Serving API & ML** | FastAPI, Uvicorn, Scikit-learn, Joblib, Pydantic, Pandas, NumPy |
| **Operational Web App** | Laravel 11, SQLite/MySQL, Blade Templates, Tailwind CSS, Vite |
| **BI & Analytics** | Apache Superset, Docker Compose, ECharts |
| **Infrastructure & CI/CD** | Terraform (GCP IaC), GitHub Actions CI/CD |

---

## 📁 Repository Directory Structure

```text
.
├── fplip-core/                       # Main Data Platform, dbt, Airflow & ML Engine
│   ├── api/                          # FastAPI serving API (Endpoints, Auth, Caching)
│   ├── common/                       # GCP helper modules & authentication resolver
│   ├── contracts/                    # Data Contracts (Schema & Validation rules)
│   ├── dags/                         # Airflow DAGs (Ingestion, Transformation, Data Quality)
│   ├── data/                         # Incoming synthetic manufacturing datasets
│   ├── dbt/                          # dbt BigQuery data warehouse transformation models
│   ├── infra/                        # Terraform Infrastructure-as-Code scripts
│   ├── ingestion/                    # Extraction & synthetic generator engines
│   ├── ml/                           # ML scrap risk classification model & training scripts
│   ├── scripts/                      # Operational pipeline execution scripts
│   └── tests/                        # Integration & Unit test suite
│
├── fplip-investigate/                # Laravel 11 Operational Web Application
│   ├── app/                          # Controllers, Services, Models, AI Explanations
│   ├── database/                     # Migrations, seeders, and SQLite storage
│   ├── resources/                    # Blade templates, Tailwind CSS, Frontend assets
│   ├── routes/                       # Web & API routes
│   └── tests/                        # Application test suite
│
├── fplip-bi/                         # BI Dashboards & Visualizations
│   └── superset/                     # Apache Superset setup & configuration
│
├── docs/                             # Centralized Technical Documentation Hub
│   ├── architecture/                 # System architecture, GCP topology, performance reports
│   ├── adr/                          # Architectural Decision Records (ADR 001 - 018)
│   ├── data-dictionary/              # BigQuery Data Warehouse Data Dictionary
│   └── runbooks/                     # Operational runbooks & test execution reports
│
├── assets/                           # Portfolio Screenshots & Visual Evidence
│   └── screenshots/                  # Benchmark runs, DAG logs, GCP console verifications
│
├── .env.example                      # Global environment template
└── README.md                         # Master Portfolio Overview README
```

---

## 🚀 Key System Features

### 1. Data Pipeline & Automated Quality Controls (`fplip-core`)
- **Bronze → Silver → Gold Architecture**: Automated medallion architecture inside BigQuery.
- **Contract Enforcement**: Incoming CSV files are strictly validated against YAML data contracts before ingestion.
- **Idempotent Airflow Ingestion**: Airflow DAGs ensure idempotent execution with date partitioning.
- **ML Scrap Risk Classifier**: Machine learning model predicts high-risk scrap batches in real time.

### 2. Operational Investigation Application (`fplip-investigate`)
- **Role-Based Access**: Specialized interfaces for Plant Managers and Technicians.
- **Automated Task Management**: Triggers investigation tasks when OEE drops below 15% or scrap spikes above 20%.
- **AI-Powered Explanations**: Integrates with LLM APIs to generate plain-language explanations of complex anomaly root causes.
- **Photo Upload & Audit Trail**: Complete evidentiary tracking for plant floor resolution.

### 3. Business Intelligence & Dashboards (`fplip-bi`)
- **OEE Pareto & Trend Visualizations**: Instant visibility into Availability, Performance, and Quality losses.
- **Factory Performance Dashboard**: Deep-dive analytics on equipment downtime and scrap rate spikes.

---

## 📊 Portfolio Screenshots & Evidence

System execution, BigQuery schema enforcement, and CI workflow run verifications are documented under [`assets/screenshots/`](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/assets/screenshots):

- **[BigQuery Sandbox Active](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/assets/screenshots/BigQuery%20SandBox%20active.png)**
- **[CI Workflow Verification](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/assets/screenshots/CI-workflow%20success.png)**
- **[Data Contract Validation](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/assets/screenshots/Contract%20Validator.png)**
- **[Airflow Ingestion DAG](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/assets/screenshots/dbt_transform_dag.png)**
- **[Partitioned BigQuery Datasets](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/assets/screenshots/week2-day3-partitioned-table.png)**
- **[Data Lineage Graph](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/assets/screenshots/lineage%20graph%20week5.png)**

---

## 💻 Quick Start Guide

### 1. Run Data Platform & Serving API (`fplip-core`)
```bash
cd fplip-core
docker compose up -d
```
Access Airflow Web UI at `http://localhost:8080` (credentials: `admin` / `admin`).

### 2. Run Operational Web App (`fplip-investigate`)
```bash
cd fplip-investigate
composer install
npm install && npm run build
php artisan migrate --seed
php artisan serve --port=8081
```
Access Investigation Web App at `http://localhost:8081`.

### 3. Run BI Visualizations (`fplip-bi`)
```bash
cd fplip-bi/superset
docker compose up -d
```
Access Superset at `http://localhost:8088`.

---

## 📄 Documentation Hub
For in-depth architectural design, data dictionaries, decision records, and operational runbooks, refer to the **[Technical Documentation Hub](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/README.md)**.
