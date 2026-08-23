# FPLIP Academic Report & Deliverable Guide

This directory contains the complete academic report for the **Factory Performance & Loss Intelligence Platform (FPLIP)** final deliverable.

---

## 📁 Files Included

- **`report.tex`**: Master LaTeX source code containing the full 12-chapter academic report + 4 appendices with embedded figures.
- **`references.bib`**: BibTeX file containing 17 academic and industry citations formatted for IEEE style.
- **`README.md`**: Compilation instructions, screenshot insertion guide, and template guidelines.

---

## 🛠️ How to Compile the LaTeX Report

### Option 1: Local Compilation (Command Line)
If you have TeX Live, MiKTeX, or TinyTeX installed:

```bash
cd rapport
pdflatex -interaction=nonstopmode report.tex
biber report
pdflatex -interaction=nonstopmode report.tex
pdflatex -interaction=nonstopmode report.tex
```

Alternatively, using `latexmk`:
```bash
latexmk -pdf report.tex
```

### Option 2: Using Overleaf
1. Create a **New Project** $\rightarrow$ **Blank Project** named `FPLIP_Academic_Report`.
2. Upload `report.tex` and `references.bib`.
3. Upload the `assets/` directory (containing `screenshots/` and `demo-screenshots/`).
4. Set Compiler to **pdfLaTeX** and TeX Live version to **2024 / 2025**.
5. Click **Recompile**.

---

## 🖼️ Embedded Figures Directory & Tags

The LaTeX report incorporates 16 figures embedded directly from `../assets/screenshots/` and `../assets/demo-screenshots/`:

| Figure Label | Description | Image Asset Path |
| :--- | :--- | :--- |
| `fig:high_level_arch` | High-Level Platform Architecture | Native TikZ Vector Diagram |
| `fig:bq_sandbox_active` | GCP BigQuery Sandbox Project Workspace | `assets/screenshots/bq_sandbox_active.png` |
| `fig:lineage_graph` | dbt Medallion Lineage Graph (Bronze $\rightarrow$ Gold) | `assets/screenshots/lineage_graph_week5.png` |
| `fig:contract_validation` | Shift-Left YAML Data Contract Validation | `assets/screenshots/contract_validator.png` |
| `fig:partitioned_tables` | BigQuery Day-Partitioned Table Layout | `assets/screenshots/week2_day3_partitioned_table.png` |
| `fig:dbt_transform_run` | dbt Model Build Execution Log | `assets/demo-screenshots/05_dbt_silver_gold_models_execution.png` |
| `fig:dbt_test_suite` | dbt Automated Test Suite Execution (85 tests) | `assets/demo-screenshots/07_dbt_test_suite_execution.png` |
| `fig:airflow_dags` | Apache Airflow Web UI DAG Overview | `assets/demo-screenshots/13_airflow_dags_overview.png` |
| `fig:ci_workflow` | GitHub Actions 5-Job CI/CD Workflow Success | `assets/screenshots/ci_workflow_success.png` |
| `fig:laravel_login` | FPLIP Investigate Web App Authentication | `assets/demo-screenshots/15_laravel_investigate_login.png` |
| `fig:plant_signals_dash` | Plant Signal Intelligence Dashboard | `assets/demo-screenshots/16_plant_signal_intelligence_dashboard.png` |
| `fig:active_plant_signals` | Active Anomaly Signal Cards | `assets/demo-screenshots/17_active_plant_signals_cards.png` |
| `fig:gemini_ai_diagnostic` | Grounded Gemini AI Operational Diagnostic | `assets/demo-screenshots/18_gemini_ai_operational_diagnostic.png` |
| `fig:technician_work_order` | Line Technician Root Cause Work Order Form | `assets/demo-screenshots/19_technician_root_cause_submission_form.png` |
| `fig:superset_dashboard` | Apache Superset 4-Row Storytelling Dashboard | `assets/screenshots/superset_dashboard_export.jpg` |
| `fig:ml_scrap_training` | Scikit-learn Logistic Regression Training Report | `assets/demo-screenshots/12_full_dataset_ml_training_metrics.png` |

---

## 📊 Summary of Covered Concepts

| Area | Applied Concepts & Technologies |
|------|--------------------------------|
| **Data Warehouse** | GCP BigQuery Sandbox, DDL-only SCD Type 2, Partition Decorator loads, `WRITE_TRUNCATE` |
| **Transformations** | dbt (Bronze, Silver, Gold), Generic Schema Tests, Custom Singular Tests, Model Contracts |
| **Governance** | Shift-Left YAML Data Contracts, Pre-Ingestion Validation, Audit Logging |
| **Serving & Web** | FastAPI, In-Memory TTL Cache (4h), Laravel 11, Role-Based Access Control (RBAC) |
| **Analytics & ML/AI** | Apache Superset (4-Row Layout), Logistic Regression Scrap Risk, Tool-Calling Grounded AI Copilot |
| **CI/CD & DevOps** | Airflow Orchestration, GitHub Actions (5-job workflow), Ephemeral Per-PR Dataset Isolation |

---

## 🎓 Academic Approval Metadata

- **Institution**: National School of Applied Sciences (ENSA Safi)
- **Program**: Master of Engineering in Data Engineering & Artificial Intelligence (IDIA)
- **Academic Year**: 2025–2026
