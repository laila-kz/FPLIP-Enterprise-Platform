# Cold-Restart Test Plan

## Definition of "Cold"
- **Fresh GCP project** (no resources, no service accounts, no datasets)
- **Existing development machine** (Python, dbt, Terraform, gcloud already installed)
- **Fresh terminal session** (no pre-set environment variables)

## Pass/Fail Criteria
The test passes if every step below completes with its documented expected outcome, using **only** commands present in the current README, with zero commands typed that aren't already documented.

## Test Steps

### Phase 1: Project Setup
1. `git clone <repository-url>`
2. `cd FPLIP_project`
3. `gcloud projects create fplip-coldstart-test --name="FPLIP Cold Start Test"`
4. Verify no billing account is linked: Check Billing page in GCP Console
5. Enable BigQuery API
6. Confirm Sandbox mode is active

**Expected Outcome:** GCP project exists, no billing account, BigQuery API enabled, Sandbox banner visible.

---

### Phase 2: Environment Setup
7. `python -m venv .venv-fplip`
8. `source .venv-fplip/bin/activate` (or `.venv-fplip\Scripts\activate` on Windows)
9. `pip install -r requirements.txt`
10. `pip install dbt-core dbt-bigquery`
11. `gcloud auth login`
12. `gcloud auth application-default login`
13. `gcloud config set project fplip-coldstart-test`

**Expected Outcome:** Virtual environment created, dependencies installed, gcloud authenticated to the new project.

---

### Phase 3: Terraform Infrastructure
14. `cd infra`
15. `cp terraform.tfvars.example terraform.tfvars`
16. Edit `terraform.tfvars` with the new project ID
17. `terraform init`
18. `terraform plan`
19. `terraform apply -auto-approve`

**Expected Outcome:** Three datasets (`fplip_bronze`, `fplip_silver`, `fplip_gold`) created. Three service accounts created (`terraform-admin`, `ingestion-sa`, `api-sa`). Keys generated in `secrets/`.

---

### Phase 4: Generate and Load Synthetic Data
20. `cd ..`
21. `python ingestion/synthetic/generate_sample_data.py --date 2026-08-10 --rows 50`
22. `export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/secrets/ingestion-sa-key.json`
23. `python -c "from ingestion.master_data_loader import load_master_file; load_master_file('data/incoming/machines.csv', 'machines'); load_master_file('data/incoming/products.csv', 'products'); load_master_file('data/incoming/shifts.csv', 'shifts'); load_master_file('data/incoming/downtime_reasons.csv', 'downtime_reasons'); load_master_file('data/incoming/defect_types.csv', 'defect_types')"`
24. `python -c "from ingestion.extract_and_load import extract_and_load_production, extract_and_load_downtime, extract_and_load_qc; from datetime import date; extract_and_load_production(date(2026, 8, 10)); extract_and_load_downtime(date(2026, 8, 10)); extract_and_load_qc(date(2026, 8, 10))"`

**Expected Outcome:** All Bronze tables populated with synthetic data.

---

### Phase 5: dbt Transformations
25. `cd dbt`
26. `dbt deps`
27. `dbt run --select fplip_silver`
28. `dbt run --select fplip_gold`
29. `dbt test --select fplip_silver fplip_gold`

**Expected Outcome:** All Silver and Gold models built, all tests passing.

---

### Phase 6: API Validation
30. `cd ..`
31. `pip install -r api/requirements.txt`
32. `export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/secrets/api-sa-key.json`
33. `uvicorn api.main:app --host 0.0.0.0 --port 8000 &`
34. `curl http://localhost:8000/health`
35. `curl "http://localhost:8000/oee/daily?start_date=2026-08-10&end_date=2026-08-10"`
36. `curl "http://localhost:8000/oee/summary?start_date=2026-08-10&end_date=2026-08-10"`
37. `curl "http://localhost:8000/scrap/root-cause?start_date=2026-08-10&end_date=2026-08-10"`

**Expected Outcome:** All endpoints return HTTP 200 with valid data (not empty arrays).

---

### Phase 7: Verification
38. Query `fplip_gold.oee_daily` for row count
39. Query `fplip_gold.scrap_root_cause_summary` for row count

**Expected Outcome:** Both Gold tables have > 0 rows.

---

## Overall Pass/Fail
The test passes if ALL steps above complete successfully with their expected outcomes, using ONLY commands from the README.

## Date
2026-08-08