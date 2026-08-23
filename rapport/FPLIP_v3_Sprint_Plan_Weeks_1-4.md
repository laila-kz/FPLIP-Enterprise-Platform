# FPLIP v3.0 — Implementation Roadmap
## Sprint Plan: Weeks 1–4 (GCP Foundation & Silver Layer Phase)

**Scope note, stated explicitly rather than assumed silently:** these four weeks cover Blueprint v3.0's Foundation & Silver Layer phase — GCP/BigQuery Sandbox provisioning through a fully tested Silver layer with Slim CI in place (blueprint Sections 9–27, mapped directly onto Section 33's own Weeks 1–4). Gold-layer models, the API, the dashboard, the daily-scheduled GitHub Actions production run, and deployment hardening (blueprint Weeks 5–8+) are intentionally out of this roadmap's scope — they are the subject of a follow-up sprint plan once this foundation is verified complete.

No code is written below. No architecture is altered. Every task traces to a section of the frozen v3.0 blueprint.

---

## ⚠️ Flagged Before You Begin: A Genuine Contradiction in the Frozen Blueprint

Per your instruction to flag — not silently fix — any genuine contradiction or technical impossibility found while planning against the frozen architecture, one needs to be surfaced before Week 3 work begins, and it changes how Week 3 should be sequenced.

**The contradiction:** Blueprint Section 16/26 correctly identifies that BigQuery Sandbox mode blocks all DML statements (`INSERT`/`UPDATE`/`DELETE`/`MERGE`), and the blueprint deliberately designs around this for Bronze loads (append-only batch loads, no DML) and for Silver/Gold models (`table` materialization via `CREATE OR REPLACE TABLE AS SELECT`, explicitly *not* `incremental`, specifically because incremental models depend on `MERGE`). This reasoning is sound and consistently applied everywhere in the blueprint — except one place: **Section 14 and Section 25 both carry forward "`dim_machine` and `dim_product` are tracked via dbt snapshots (SCD Type 2), unchanged from v2.0" without acknowledging that dbt's snapshot materialization also depends on a `MERGE` statement** (dbt-bigquery implements the timestamp/check snapshot strategies via `MERGE INTO` under the hood, identical to how incremental models work) — the exact operation the blueprint already ruled out for every other model in this platform.

This is not a minor detail. If unaddressed, the Week 3 SCD2 work is scheduled against a mechanism that may simply fail to execute in a Sandbox project.

**What this roadmap does about it, and what it deliberately does not do:** it does not redesign the SCD2 approach for you — that's your call to make, and it may warrant its own ADR. Instead, Week 3 below opens with a scheduled validation spike, before any real dimension or snapshot work begins, to determine definitively whether `dbt snapshot` executes successfully against your Sandbox project. The two possible outcomes and what each implies are stated in Week 3's Task 3.1 below. Do not proceed past that spike without a clear answer either way.

---

# WEEK 1 — GCP Foundation & Repository Scaffolding

## 1. Weekly Goal
Confirm and provision the complete zero-cost GCP foundation the rest of the project depends on: a GCP project verified to be running in BigQuery Sandbox mode (no billing account linked, ever), three BigQuery datasets (`fplip_bronze`, `fplip_silver`, `fplip_gold`) and two scoped IAM service accounts (`ingestion_sa`, `api_sa`) provisioned via Terraform. In parallel, scaffold the repository, draft the three data contracts, and get a local development environment and the synthetic data generator running.

## 2. Why This Week Comes Now
Every subsequent week targets this project and these datasets/identities — there's nothing to build ingestion or dbt models against otherwise. This is also the single most important week to get exactly right for a reason specific to this blueprint's core constraint: **confirming Sandbox mode is active, and staying in it, is not a one-time check — it's a standing invariant this entire project's zero-cost premise depends on**, and the easiest way to accidentally break it is early, before you've built the habit of checking.

## 3. Prerequisites
- Blueprint v3.0 finalized (already true)
- A free Google account (no card required for this step)
- A GitHub account and an empty repository created
- Docker and Docker Compose installed locally
- Python 3.11+ installed locally

## 4. Detailed Task Breakdown

**GCP project creation and Sandbox verification — the week's highest-stakes task**
- Go to the Google Cloud Console and create a new GCP project
- **Do not** click any "Enable billing" prompt, **do not** accept any free-trial-credit offer that requires entering a card — either of these silently exits Sandbox mode
- Record the project ID
- Navigate to **Billing** for this project and confirm it explicitly states no billing account is linked — this is the authoritative check, not an assumption
- Enable the BigQuery API for the project (this is possible without billing, in Sandbox mode)
- Open the BigQuery console for this project and confirm the Sandbox mode banner/indicator is present
- Write down, in your own words, in a note you'll reference again in Week 4's risk audit: "as of [date], this project has no billing account linked, confirmed via the Billing page"

**Google Cloud SDK and authentication**
- Install the `gcloud` CLI
- Run `gcloud init`, select the project created above
- Run `gcloud auth login` for your own interactive user session
- Run `gcloud auth application-default login` **separately** — this is the credential Terraform will use, and it is a distinct authentication step from `gcloud auth login`; conflating the two is a common early mistake
- Run `gcloud config set project <project-id>`
- Verify: `gcloud config list`

**A dedicated Terraform service account**
- Create a service account (e.g., `terraform-admin`) via the console or `gcloud iam service-accounts create`
- Grant it `roles/bigquery.admin` and `roles/iam.serviceAccountAdmin` scoped to this one project only (per blueprint Section 23) — never organization-wide
- Generate a JSON key for this service account via `gcloud iam service-accounts keys create`
- Store the key file locally in a location outside the repository, or inside the repository but covered by `.gitignore` before it's ever created (sequencing matters, same principle as Week 1 of the previous Azure build)

**Repository scaffolding**
- Initialize the Git repository if not already done
- Create `.gitignore` covering: `*.tfstate`, `*.tfstate.backup`, `.terraform/`, `*.json` (service account keys — be deliberate that this pattern doesn't accidentally also ignore intentional, non-secret JSON files you might add later; a more precise pattern like `*-key.json` or a dedicated `secrets/` directory is worth considering here), `.env`, `__pycache__/`, `.venv/`
- Create top-level directories: `infra/`, `dags/`, `dbt/`, `ingestion/synthetic/`, `api/`, `contracts/`, `docs/adr/`, `tests/unit/`, `tests/integration/`, `data/sample/`, `.github/workflows/`
- Create `README.md` with section headers only
- Commit the empty scaffold

**Terraform: provider and BigQuery datasets**
- Create `infra/providers.tf` declaring the `google` provider, pointed at the project ID and a default region
- Create `infra/variables.tf` for project ID, region, dataset names, service account names
- Create `infra/main.tf`: three `google_bigquery_dataset` resources (`fplip_bronze`, `fplip_silver`, `fplip_gold`), each with an explicit location and descriptive labels
- Run `terraform init`, `terraform plan`, review carefully, `terraform apply`
- Verify each dataset exists in the BigQuery console

**Terraform: IAM service accounts and dataset-scoped bindings**
- Add `google_service_account` resources for `ingestion_sa` and `api_sa` to `main.tf`
- Add `google_bigquery_dataset_iam_member` resources (dataset-scoped, not project-scoped — this is a real, easy mistake to make with the `google` provider, which offers both a dataset-level and a project-level IAM resource type) granting `ingestion_sa` the `roles/bigquery.dataEditor` role on all three datasets
- Add a `google_bigquery_dataset_iam_member` granting `api_sa` `roles/bigquery.dataViewer` on `fplip_gold` only, plus a project-level `roles/bigquery.jobUser` binding (query execution requires this role at the project level, even for a dataset-scoped viewer — a genuine BigQuery IAM nuance worth knowing going in)
- Run `terraform plan` / `terraform apply`
- Generate JSON keys for `ingestion_sa` and `api_sa` via `gcloud iam service-accounts keys create` (deliberately *not* via Terraform's `google_service_account_key` resource, which would leave the private key material sitting in your Terraform state file — a real, avoidable security downgrade)
- Store both keys locally, gitignored

**Verify least-privilege IAM scoping actually works**
- Using the `ingestion_sa` key, run a small authenticated test (via the `google-cloud-bigquery` Python client or the `bq` CLI with `--impersonate-service-account`) confirming it can write to a test table in `fplip_bronze` but cannot, for example, delete the dataset itself
- Using the `api_sa` key, confirm it can run a `SELECT` against `fplip_gold` (even against an empty/non-existent table, a permissions-level check is what matters here) but cannot write

**Data contracts**
- Create `contracts/production.yaml`, `contracts/downtime.yaml`, `contracts/qc.yaml` per blueprint Section 8's required fields
- Cross-check against blueprint Section 7's stated source formats

**Local development environment**
- Create a Python virtual environment
- Create `requirements.txt`: `faker`, `pandas`, `pyarrow`, `google-cloud-bigquery`, `python-dotenv`, `pyyaml` — note `pyodbc` has no place in this stack at all; there is no SQL Server-family database anywhere in v3.0
- Create `.env.example` with placeholder variable names: `GCP_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS` (a file path, not a value)

**Synthetic data generator (scaffold only this week)**
- Create `ingestion/synthetic/generate_sample_data.py` as an entrypoint, one function signature per source
- Generate one day of placeholder synthetic production data, manually inspect it against `contracts/production.yaml`

**Documentation**
- Write `docs/adr/ADR-001-warehouse-selection.md` restating the BigQuery Sandbox decision and the four rejected alternatives from blueprint Section 13 in your own words. **Note on ADR numbering**: if this repository previously built toward the Azure-based v2.0 blueprint and already has an ADR-001 documenting Azure SQL Database, treat this as a fresh implementation and either start a new repository (consistent with the blueprint's own framing of v3.0 as a definitive restart) or continue the ADR sequence rather than overwriting history — an ADR that silently replaces a prior one loses exactly the auditable decision trail the ADR log exists to provide.
- Update `docs/architecture.md` with this week's real project ID and resource names

## 5. Deliverables
- A verified-Sandbox-mode GCP project with no billing account linked
- Terraform-applied: three BigQuery datasets, two IAM service accounts with dataset-scoped bindings verified to enforce least privilege
- Full repository scaffold
- Three drafted data contracts
- Local dev environment and synthetic data generator producing one inspectable sample file
- ADR-001; updated `architecture.md`

## 6. Acceptance Criteria
- The GCP project's Billing page explicitly confirms no linked billing account
- `terraform plan` shows zero pending changes
- `ingestion_sa` can write to a test table in `fplip_bronze` but cannot delete the dataset
- `api_sa` can query `fplip_gold` but cannot write to it
- All three contracts pass manual review against blueprint Section 8
- Synthetic data generator produces a schema-correct sample file

## 7. Common Mistakes
- Accidentally linking a billing account or accepting a free-trial-credit offer during project creation — this is this week's single highest-consequence mistake, directly analogous to an irreversible infrastructure setting in a different cloud, except here the "irreversible" part is a design premise (zero cost, no card) rather than a storage flag.
- Granting `ingestion_sa` or `api_sa` project-wide `roles/bigquery.admin`/`Editor` instead of dataset-scoped roles "to save time" — this defeats the entire least-privilege design the blueprint's Section 23 specifies.
- Confusing `google_bigquery_dataset_iam_member` (dataset-scoped) with a project-level IAM binding resource — double-check which one you're actually applying.
- Using Terraform's `google_service_account_key` resource and leaving a live private key sitting in `terraform.tfstate`, which then needs to be treated as sensitive forever.
- Conflating `gcloud auth login` with `gcloud auth application-default login` — Terraform specifically needs the latter, and skipping it produces a confusing authentication error that looks unrelated to the actual cause.

## 8. Recommended Commit Strategy
1. `chore: initialize repository structure and gitignore`
2. `docs: add README skeleton`
3. `infra: add Terraform provider and BigQuery datasets`
4. `infra: add IAM service accounts and dataset-scoped bindings`
5. `docs: add data contracts for production, downtime, and QC sources`
6. `docs: add ADR-001 (BigQuery Sandbox warehouse selection)`
7. `chore: add local dev environment (requirements, .env.example)`
8. `feat: scaffold synthetic data generator entrypoint`

## 9. Estimated Difficulty
- **Technical difficulty:** Medium-High. The GCP resource/IAM model, and specifically the dataset-vs-project IAM scoping distinction, is genuinely new; the Sandbox-mode verification step is conceptually simple but must be treated with real seriousness given what it protects.
- **Time required:** A full week, front-loaded by GCP/Terraform ramp-up, the same shape as any first cloud-foundation week.
- **Learning curve:** Steep but one-time — nothing in Weeks 2–4 introduces new Terraform or IAM concepts beyond what's used here.

## 10. End-of-Week Checklist
- [ ] GCP project created, Sandbox mode (no billing account) explicitly confirmed
- [ ] Three BigQuery datasets created via Terraform
- [ ] `ingestion_sa` and `api_sa` created with dataset-scoped IAM roles, verified least-privilege
- [ ] `terraform plan` shows no drift
- [ ] Repository structure matches the blueprint
- [ ] Three data contracts drafted and self-reviewed
- [ ] Local dev environment and synthetic data generator working
- [ ] ADR-001 written; `architecture.md` updated
- [ ] All work committed in logical, separate commits

---

# WEEK 2 — BigQuery Bronze Ingestion

## 1. Weekly Goal
Stand up Airflow locally, and build the three extraction pipelines (production, downtime, QC) that read source data, validate it against its contract, and load it directly into native, time-partitioned BigQuery tables in `fplip_bronze` — using batch `WRITE_APPEND`/partition-decorator loads (the only load mechanism Sandbox mode permits), idempotent and retryable, orchestrated as Airflow DAGs.

## 2. Why This Week Comes Now
Airflow needs the `fplip_bronze` dataset from Week 1 to have somewhere to write to. This is also the week where BigQuery Sandbox's DML restriction first becomes directly relevant to code you write, not just to architecture you read about — getting the idempotent-load pattern right here, while it only affects three simple Bronze tables, is far cheaper than discovering it's wrong once Silver/Gold depend on it.

## 3. Prerequisites
- All Week 1 GCP infrastructure applied and verified, including confirmed least-privilege IAM
- Synthetic data generator scaffolded

## 4. Detailed Task Breakdown

**Airflow local environment**
- Add Airflow services to `docker-compose.yml` (`airflow-init`, `airflow-webserver`, `airflow-scheduler`, a Postgres instance for Airflow's own metadata — this metadata database is purely local/internal to Airflow and has nothing to do with the BigQuery-hosted pipeline data)
- Configure `LocalExecutor`
- Mount the `ingestion_sa` JSON key into the Airflow containers as a volume (never baked into an image layer), and set `GOOGLE_APPLICATION_CREDENTIALS` to its in-container path
- Bring up Airflow, confirm the webserver is reachable, and run a throwaway test DAG that lists tables in `fplip_bronze` to confirm the credential and permissions work end to end, then delete the test DAG

**Synthetic data generator — completed this week**
- Finish `generate_sample_data.py` for all three sources
- Add a CLI date parameter
- Generate several days of data, including one day with a deliberately malformed record for failure-path testing
- Output to a local `data/incoming/` folder simulating the factory drop location

**Contract validation**
- Create `ingestion/contract_validator.py`
- Write `tests/unit/test_contract_validator.py` covering valid/invalid/missing-column/wrong-type cases

**BigQuery Bronze table creation with time partitioning — a required one-time setup task**
- Before the first load, each Bronze table must be created with time partitioning defined on the `_ingested_at` column — this is what makes the partition-decorator load pattern below possible at all, and it must be set at table-creation time, not retrofitted
- Write a small one-time setup routine (or the loader's own "create if not exists" logic) that creates `fplip_bronze.production_runs`, `fplip_bronze.downtime_events`, `fplip_bronze.qc_inspections` with an explicit schema (matching each contract exactly — never rely on schema autodetection, which risks silent type drift if a day's data happens to look numeric) and `time_partitioning` configured on `_ingested_at`
- Run this setup once, verify all three tables exist (empty) in the BigQuery console with partitioning visible under each table's Details tab

**Bronze ingestion logic (per source, repeated three times)**
- Extraction step: read the source file (real or synthetic)
- Validation step: run `contract_validator` against it; fail loudly, don't log-and-continue, on any mismatch
- **Idempotent load step — the week's most important technical detail**: load into the specific date's partition using the partition-decorator syntax (`fplip_bronze.production_runs$20260414`) with `write_disposition=WRITE_TRUNCATE`. This is a load-job operation, not a DML statement, and is fully permitted under Sandbox mode — it replaces only that one partition's contents, giving you true idempotency (rerun-safe) without ever touching `INSERT`/`UPDATE`/`MERGE`. Using plain `WRITE_APPEND` without the partition decorator will duplicate rows on any rerun — this is the single most consequential mistake available this week, and it will not throw an error to warn you; it will simply produce quietly wrong row counts.
- Add `_ingested_at` and `_source_file` metadata columns to every row before load

**Airflow DAGs**
- Create `dags/extract_production.py`, `dags/extract_downtime.py`, `dags/extract_qc.py`, each chaining `extract → validate_contract → load_bronze_bigquery`, 3 retries with exponential backoff
- Trigger each manually against a valid synthetic day, verify success
- Trigger the same DAG a second time for the *same* date; verify (by querying `SELECT COUNT(*) FROM fplip_bronze.production_runs WHERE _ingested_at = '2026-04-14'`) that the row count is unchanged, not doubled
- Trigger against the malformed synthetic file; verify the task fails loudly

**Integration testing**
- Write `tests/integration/test_bronze_ingestion.py` running the real load logic against a real (or Sandbox-project) BigQuery table, asserting row count and schema after load, and asserting a second run at the same date doesn't change the row count

**Documentation**
- Update `docs/architecture.md` with the completed Bronze flow
- Write `docs/adr/ADR-002-idempotent-bronze-loading.md` documenting the partition-decorator `WRITE_TRUNCATE` pattern and explicitly stating why plain `WRITE_APPEND` alone was rejected

## 5. Deliverables
- Local Airflow environment authenticated as `ingestion_sa`
- Completed synthetic data generator with a malformed-record test case
- Contract validator with passing unit tests
- Three time-partitioned Bronze tables with explicit (non-autodetected) schemas
- Three Bronze ingestion DAGs using verified idempotent, partition-decorator loads
- Integration tests
- ADR-002

## 6. Acceptance Criteria
- All three DAGs succeed against valid synthetic data
- Bronze tables show correct partitioning and `_ingested_at`/`_source_file` columns
- Re-triggering a DAG for an already-processed date leaves the row count unchanged, confirmed by direct query, not assumption
- Triggering against the malformed file produces a visible task failure
- `pytest` passes locally

## 7. Common Mistakes
- Using `WRITE_APPEND` without a partition decorator, causing silent row duplication on any rerun — the defining risk of this week.
- Attempting a streaming insert (`insert_rows_json`/legacy `tabledata.insertAll`) instead of a batch load job — Sandbox mode does not support streaming inserts at all; only batch load jobs are permitted.
- Relying on schema autodetection for the load job instead of passing an explicit schema matching the contract, risking silent type drift.
- Forgetting that the partition-decorator syntax (`table$YYYYMMDD`) only works against a table that was created with time partitioning already configured — attempting it against a non-partitioned table fails outright.
- Putting business logic (defect-code remapping, unit conversions) into the Bronze load step instead of deferring it to dbt/Silver.

## 8. Recommended Commit Strategy
1. `infra: add Airflow services to docker-compose`
2. `feat: complete synthetic data generator for all three sources`
3. `feat: add contract validator with unit tests`
4. `feat: add Bronze table creation with time partitioning`
5. `feat: add idempotent Bronze load logic (partition-decorator WRITE_TRUNCATE)`
6. `feat: add extract_production, extract_downtime, extract_qc DAGs`
7. `test: add integration tests for Bronze ingestion`
8. `docs: update architecture; add ADR-002`

## 9. Estimated Difficulty
- **Technical difficulty:** Medium-High. The partition-decorator idempotency pattern is a genuinely non-obvious BigQuery-specific technique — this is the one piece of this week that most benefits from deliberately reading `google-cloud-bigquery`'s load-job documentation before writing code, rather than learning by pure trial and error.
- **Time required:** A full week.
- **Learning curve:** Moderate-high, concentrated specifically on the BigQuery load-job/partitioning mechanics rather than spread evenly across the week.

## 10. End-of-Week Checklist
- [ ] Local Airflow running, authenticated as `ingestion_sa`
- [ ] Synthetic data generator complete with malformed-record case
- [ ] Contract validator unit-tested
- [ ] Bronze tables created with explicit schema and time partitioning
- [ ] Idempotent loads verified by rerunning a DAG for the same date and checking row count directly
- [ ] Failure path verified
- [ ] Integration tests passing
- [ ] ADR-002 written
- [ ] All work committed in logical, separate commits

---

# WEEK 3 — Silver Layer Dimensions (Opens with the SCD2/DML Validation Spike)

## 1. Weekly Goal
Resolve the SCD2-vs-Sandbox-DML question flagged above, scaffold the `dbt-bigquery` project, build and test all six Silver dimension models, and — contingent on the spike's outcome — get SCD2 history working and verified for `dim_machine` and `dim_product`.

## 2. Why This Week Comes Now
dbt needs populated Bronze tables (Week 2) to build staging views over. Dimensions come before facts because facts reference dimension keys. The SCD2 spike specifically belongs at the very start of this week, not buried inside the dimension-building work, because its outcome could change how `dim_machine`/`dim_product` need to be built — running it first avoids building the "wrong" version and then redoing it.

## 3. Prerequisites
- Three Bronze tables from Week 2, populated and idempotency-verified
- `ingestion_sa` credentials working locally

## 4. Detailed Task Breakdown

**Task 3.1 — SCD2 / DML Validation Spike (do this first, before any other Week 3 work)**
- Install `dbt-core` and `dbt-bigquery`
- Scaffold a throwaway dbt project (or a throwaway model inside the real one) with a tiny dummy source table and a single trivial snapshot definition
- Run `dbt snapshot` against it once (initial creation — this always succeeds, since the first run is a plain `CREATE TABLE`, not a `MERGE`)
- **Manually alter the dummy source row**, then run `dbt snapshot` a second time — this second run is the one that actually depends on `MERGE`
- Record the exact outcome:
  - **If it succeeds**: BigQuery's Sandbox restrictions may not extend to dbt's internally-generated `MERGE` statements the way the blueprint assumed, or dbt-bigquery may have a Sandbox-compatible snapshot strategy available. Document this finding precisely (dbt version, adapter version, the exact statement dbt generated, visible via `dbt --debug`) in `docs/adr/ADR-003-scd2-scd-strategy-validated.md`, and proceed with the real `dim_machine`/`dim_product` snapshots as originally scoped.
  - **If it fails with a permissions/DML-not-supported error**: this confirms the contradiction. Do not attempt to fix the blueprint's architecture yourself here — write `docs/adr/ADR-003-scd2-blocked-by-sandbox-dml.md` stating the failure precisely (the exact error message), and flag this as a decision point requiring your own judgment call: options include (a) accepting `dim_machine`/`dim_product` as non-SCD2 (full-refresh, current-state-only dimensions) for the duration of the Sandbox-mode build, explicitly noting the SCD2 capability as deferred rather than removed, or (b) hand-rolling a DDL-only history table (a `CREATE OR REPLACE TABLE AS SELECT` that unions the previous version of the dimension with newly detected changes) as a Sandbox-compatible substitute. **Either choice is legitimate; making it silently is not.** This roadmap does not choose for you — it stops here, flags it, and moves the remaining Week 3 dimension work forward on the assumption that whichever path you choose, `dim_machine` and `dim_product` still get built as tables this week; only the history-tracking mechanism underneath them is in question.

**dbt project scaffold**
- Run `dbt init` inside `dbt/`
- Configure `profiles.yml` (gitignored) using the `service-account` auth method, keyfile pointed at the `ingestion_sa` key, default dataset/location matching Week 1's Terraform config
- Run `dbt debug`, confirm connection
- Create `models/staging/sources.yml` declaring the three Bronze tables as sources, with `loaded_at_field: _ingested_at` and freshness thresholds

**Staging views**
- Create `models/bronze/stg_production_runs.sql`, `stg_downtime_events.sql`, `stg_qc_inspections.sql` as lightweight views selecting directly from the Bronze sources — there is no physical staging-load task in this version (unlike the Azure build), since dbt queries BigQuery directly; this is one fewer moving part than the equivalent week in a non-BigQuery version of this project

**Silver dimension models**
- Create `models/silver/dims/dim_machine.sql`, `dim_product.sql` (including `standard_cycle_time_sec` and `cycle_time_confidence`), `dim_shift.sql`, `dim_date.sql` (date-spine macro), `dim_defect_type.sql`, `dim_downtime_reason.sql`
- Run `dbt run --select silver.dims`, verify all six build as native BigQuery tables in `fplip_silver`

**Testing on dimensions**
- Add `schema.yml` with `not_null`/`unique` on primary keys, `accepted_values` on categorical fields
- Run `dbt test --select silver.dims`, confirm 100% pass

**SCD2 implementation — proceeding per the Task 3.1 outcome**
- If the spike succeeded: build `dim_machine_snapshot.sql` and `dim_product_snapshot.sql` as originally scoped, run `dbt snapshot`, manually alter a synthetic source record, rerun, and directly verify a closed old row and an open new row appear
- If the spike failed: build whichever alternative you chose in ADR-003, and still perform the equivalent manual-change verification — the requirement to actually watch history-tracking fire on a real change, not assume it, applies regardless of which mechanism you land on

**Documentation**
- Run `dbt docs generate`/`serve`, confirm the lineage graph
- Update `docs/data_dictionary.md` with dimension definitions
- ADR-003 (from the spike) should already be written; add ADR-004 if a second ADR is needed to document the final chosen SCD2 implementation approach separately from the validation finding

## 5. Deliverables
- A definitive, documented answer to the SCD2/DML question (ADR-003)
- Scaffolded, connected dbt project
- Three staging views over Bronze
- Six tested Silver dimension models
- A working history-tracking mechanism for `dim_machine`/`dim_product` (SCD2 snapshots, or the documented alternative), verified against a real manual change
- Local `dbt docs` site; updated data dictionary

## 6. Acceptance Criteria
- The SCD2 spike's outcome is documented with the exact error or success evidence, not a guess
- `dbt run --select silver.dims` and `dbt test --select silver.dims` both succeed
- Whatever history-tracking mechanism was chosen, a manual source-record change produces a directly-verified new history row
- `dbt docs` lineage graph correctly shows staging → Silver dims

## 7. Common Mistakes
- Building the full `dim_machine`/`dim_product` snapshot pipeline before running the spike, discovering the DML failure only after investing real time in the "wrong" version.
- Assuming the spike's first `dbt snapshot` run (which always succeeds, since it's a plain `CREATE TABLE`) proves snapshots work — the real test is the *second* run, after a source change, which is the one that depends on `MERGE`.
- Putting business logic into the staging views instead of keeping them cast-and-rename only.
- Declaring history-tracking "done" without ever manually triggering and directly observing a change fire through it.

## 8. Recommended Commit Strategy
1. `spike: validate dbt snapshot MERGE behavior under BigQuery Sandbox`
2. `docs: add ADR-003 (SCD2/DML spike outcome)`
3. `chore: scaffold dbt-bigquery project`
4. `feat: add staging views over Bronze sources`
5. `feat: add Silver dimension models`
6. `test: add dbt tests for Silver dimensions`
7. `feat: add SCD2/history-tracking implementation for dim_machine and dim_product`
8. `docs: update data dictionary; add ADR-004 if applicable`

## 9. Estimated Difficulty
- **Technical difficulty:** Medium-High, driven almost entirely by the spike and its resolution rather than the dimension-building work itself, which is otherwise routine dbt.
- **Time required:** A full week; budget real time for the spike specifically — don't treat it as a quick five-minute check.
- **Learning curve:** Moderate for dbt fundamentals if you have prior exposure; the BigQuery-specific DML/snapshot interaction is the genuinely new piece.

## 10. End-of-Week Checklist
- [ ] SCD2/DML spike run and outcome documented in ADR-003
- [ ] dbt project connects successfully to BigQuery
- [ ] Three staging views built
- [ ] Six Silver dimension models built and passing all tests
- [ ] History-tracking mechanism verified against a real manual change
- [ ] `dbt docs` lineage graph renders correctly
- [ ] Data dictionary and ADRs updated
- [ ] All work committed in logical, separate commits

---

# WEEK 4 — Silver Facts, Grain Validation & GitHub Actions Slim CI

## 1. Weekly Goal
Build the three Silver fact models with the corrected grain, run the grain-validation checkpoint against a deliberately constructed multi-run-per-day case, complete the full Silver test suite, and stand up the GitHub Actions Slim CI pipeline — including a dedicated CI-only GCP Sandbox project, a per-PR temporary BigQuery dataset, and verified, unconditional teardown of that dataset even on failure.

## 2. Why This Week Comes Now
Facts depend on dimension keys from Week 3. The grain-validation checkpoint is the last safe point before any Gold model is built on top of it. CI belongs at the end of this foundation phase because it needs a stable Silver layer as its test target, and because the CI-project isolation pattern (Section 20) is specifically designed to protect the *production* Sandbox project's data and quota from bad PRs — protection that only matters once there's real Silver-layer work worth protecting.

## 3. Prerequisites
- Six Silver dimension models from Week 3, tested and passing
- History-tracking mechanism verified (whichever form it took)

## 4. Detailed Task Breakdown

**Grain validation preparation**
- Write `docs/adr/ADR-005-fact-grain-validation.md` stating the exact `run_sequence_number` derivation logic
- Inspect synthetic data for a naturally occurring multi-run case; if none exists, extend the generator to deliberately produce one
- Manually spot-check that the intended logic correctly separates two runs rather than collapsing them

**Silver fact models**
- Create `models/silver/facts/fct_production_run.sql` (corrected grain), `fct_downtime_event.sql`, `fct_qc_inspection.sql`
- Run `dbt run --select silver.facts`

**Testing on facts**
- `not_null`/`unique` on primary keys; `relationships` tests against dimensions and the `fct_qc_inspection` → `fct_production_run` reference
- A singular test asserting no duplicate `(machine_id, shift_id, product_id, date_id, run_sequence_number)` combination
- Run `dbt test --select silver.facts`, confirm 100% pass including the deliberate multi-run case, verified to produce two distinct rows

**Source freshness**
- Configure `dbt source freshness` on Bronze sources, confirm it reports correctly

**IAM audit (the GCP-appropriate equivalent of a least-privilege migration)**
- Confirm `profiles.yml` and Airflow's `GOOGLE_APPLICATION_CREDENTIALS` are actually pointed at the `ingestion_sa` key — not your personal `gcloud auth application-default login` credentials, which may have been used for convenience during Weeks 2–3 debugging and would otherwise silently carry broader personal-account permissions into what should be a scoped service-account-driven pipeline

**A dedicated CI-only GCP project**
- Create a second, separate GCP project (also Sandbox mode — confirm no billing linked, same as Week 1) used exclusively for ephemeral CI datasets, isolating any bad PR from ever touching real Bronze/Silver/Gold data or eating into the production project's query quota
- Create a `ci_sa` service account scoped to this CI project only, granted `roles/bigquery.admin` **on this project only** — broader than `ingestion_sa`'s role, but acceptable specifically because this project is disposable and never holds real data; the blast radius is bounded by the project's own purpose, not by the role's narrowness
- Generate a `ci_sa` JSON key
- Add it as a GitHub Actions encrypted secret (the first secret this project stores in GitHub, since local development so far has used local key files)

**GitHub Actions Slim CI workflow**
- Create `.github/workflows/ci.yml`
- `lint` job: `ruff check .`, `sqlfluff lint dbt/`
- `contract-check` job: validate `contracts/*.yaml` against current Bronze schemas
- `dbt-test` job: authenticate as `ci_sa`, create a temporary dataset named `fplip_ci_pr_<PR number>` in the CI-only project, run `dbt seed && dbt build` (covering run + all test tiers + model contracts) against it, then **unconditionally** drop that dataset in a step marked `if: always()` — so the dataset is removed whether the build passed or failed
- `terraform-plan` job: `terraform validate && terraform plan`, no `apply`
- `docker-build` job: `docker compose build`
- Open a real PR, verify all jobs pass

**Verify the teardown guarantee specifically — do not skip this**
- On a throwaway branch, deliberately break one dbt test
- Open a PR, confirm the `dbt-test` job fails as expected
- Immediately check the CI-only project's BigQuery console: confirm no `fplip_ci_pr_<number>` dataset remains — this is the specific check your own risk list called out, and it's the same principle as every other "watch it fail on purpose" verification this project has required at each prior checkpoint
- Close the throwaway branch without merging

**Documentation**
- Update `docs/architecture.md` with the completed Silver layer and CI architecture (including the two-project topology: production Sandbox project + CI-only Sandbox project)
- Update `docs/data_dictionary.md` with the three fact tables
- Review all ADRs (001 through the SCD2 ADRs and ADR-005) together for internal consistency before beginning Gold-layer work

## 5. Deliverables
- Three tested Silver fact models with validated grain
- Full Silver test suite passing, including the multi-run grain test
- IAM audit confirming pipeline credentials, not personal credentials, are in use
- A second, CI-only GCP Sandbox project with `ci_sa` scoped to it
- Working GitHub Actions Slim CI pipeline with verified, unconditional per-PR dataset teardown
- Updated documentation and ADRs

## 6. Acceptance Criteria
- `dbt test --select silver` passes 100%, including the multi-run grain test producing two distinct rows, confirmed by direct query
- A real PR shows all CI jobs passing
- A deliberately broken PR shows the `dbt-test` job failing *and* the temporary CI dataset confirmed absent afterward
- Pipeline credentials confirmed to be `ingestion_sa`, not a personal account

## 7. Common Mistakes
- Treating grain validation as satisfied without deliberately constructing a multi-run test case.
- Running CI against the *production* Sandbox project instead of the dedicated CI-only project, risking real data or quota exposure from an untrusted PR.
- Forgetting the `if: always()` condition on the dataset-teardown step, leaving orphaned `fplip_ci_pr_<number>` datasets behind after failed runs — harmless at zero cost, but sloppy, and exactly the kind of gap this week's dedicated verification step exists to catch.
- Granting `ci_sa` any role outside the CI-only project, accidentally widening its blast radius back to production.
- Never actually checking whether local dev was quietly using personal `gcloud` credentials instead of `ingestion_sa` — an easy thing to skip since everything "works" either way.

## 8. Recommended Commit Strategy
1. `feat: add Silver fact models with corrected grain`
2. `test: extend synthetic generator with multi-run edge case`
3. `test: add referential integrity and grain-uniqueness tests`
4. `chore: add dbt source freshness configuration`
5. `security: audit and confirm ingestion_sa usage over personal credentials`
6. `infra: add CI-only GCP project and ci_sa service account`
7. `ci: add GitHub Actions Slim CI workflow with per-PR dataset teardown`
8. `docs: add ADR-005 (grain validation); update architecture and data dictionary`

## 9. Estimated Difficulty
- **Technical difficulty:** Medium-High. Grain validation remains the most conceptually demanding modeling task; the Slim CI dataset-per-PR pattern with guaranteed teardown is a genuinely new CI pattern, more involved than a standard ephemeral-container CI job.
- **Time required:** A full week.
- **Learning curve:** Moderate — GitHub Actions itself is likely familiar; the specific combination of dynamic BigQuery dataset provisioning inside a CI job is the new piece.

## 10. End-of-Week Checklist
- [ ] Three Silver fact models built with corrected, validated grain
- [ ] Full Silver test suite passing
- [ ] IAM audit completed — pipeline uses `ingestion_sa`, confirmed
- [ ] CI-only GCP project and `ci_sa` created
- [ ] GitHub Actions CI pipeline green on a real PR
- [ ] Deliberate CI failure triggered, and dataset teardown confirmed even on failure
- [ ] ADRs reviewed together for consistency
- [ ] All work committed in logical, separate commits

---

## End of Foundation Phase

At the close of Week 4: a verified zero-cost GCP foundation across two Sandbox projects; three idempotent, contract-validated Bronze ingestion pipelines using a correct partition-decorator load pattern; a fully tested Silver layer (six dimensions with a resolved and documented history-tracking approach, three facts with a validated grain); and a Slim CI pipeline with a verified teardown guarantee — all before any Gold-layer work begins.

The next phase (Gold marts, formula unit tests, the API, the Power BI dashboard, the daily-scheduled GitHub Actions production run, and deployment/monitoring hardening — blueprint Weeks 5–8+) is intentionally not detailed here. Ask for it once this foundation phase's checklist is fully checked off — and specifically once Week 3's SCD2/DML question has a documented, not assumed, answer, since that finding may shape how Gold-layer work references `dim_machine`/`dim_product` history.
