# Factory Performance & Loss Intelligence Platform (FPLIP)
## Architecture Blueprint v3.0
### A Governed OEE and Scrap Root-Cause Analytics Platform for a Single-Site Manufacturer

Prepared for: 8–12 week end-of-studies internship / portfolio project
Scope: OEE Analytics + Scrap Root-Cause Analytics (MVP), Energy Analytics (Phase 2, conditional)
Cloud posture: single-platform, zero-cost (Google BigQuery Sandbox), storage- and warehouse-justified, not storage- and warehouse-inflated

---

## 1. Executive Summary

FPLIP is a governed, cloud-backed analytics platform that converts three low-trust operational data streams — production output, machine downtime, and quality-control inspection records — into two metrics a plant manager can act on without qualification: **OEE (Overall Equipment Effectiveness)** and **scrap root-cause attribution**. Version 3.0 keeps the architectural philosophy of v1.0 and v2.0 fully intact — medallion architecture, dbt-governed transformations, Airflow orchestration, tests as promotion gates — and makes one category of change on top of everything v2.0 already fixed: it replaces the entire Azure-based storage and warehouse footprint (ADLS Gen2 + Azure SQL Database) with **Google BigQuery in Sandbox mode** — a single platform, requiring no credit card and no linked billing account, that serves as both Bronze storage and the Silver/Gold warehouse.

This is not a downgrade dressed up as a pivot. The financial constraint behind this change is real and non-negotiable, but the resulting design is, in several respects, *more* defensible than v2.0's — not despite the constraint, but because meeting it honestly forced the removal of steps (a separate landing zone, a separate staging-load hop, a separate compute host) that v2.0 carried out of convention rather than necessity. Every removal below is traceable either to a real Sandbox constraint or to a genuine simplification the Sandbox constraint exposed — never to a silent loss of capability papered over. The v2.0 fixes remain untouched: the corrected `fct_production_run` grain, the formal data contracts, and the unit-tested OEE formula that closes the `standard_cycle_time_sec` validity risk are all carried forward exactly as they were.

---

## 2. Business Problem

A concrete-block, paver, and zellige-tile manufacturer currently has no single, trusted definition of two numbers every plant manager instinctively wants: how efficiently its machines are running, and why product gets rejected. The data to answer both questions already exists — production logs, downtime reason codes, QC inspection sheets — but it is scattered across paper, spreadsheets, and an ERP (Nizzar) built for transactional record-keeping, not trend analysis. Different departments compute "downtime" differently. No one can currently produce a number like "Line 2 lost 34% of available time to changeovers on Tuesday's night shift" without a multi-hour manual reconciliation exercise, which means the number is never produced, and decisions get made on impression instead of evidence.

This is not a data-availability problem. It is a data-trust problem, and it is the specific problem a data platform — not a dashboard — is built to solve.

---

## 3. Objectives

1. Establish one governed, tested definition each for OEE and scrap rate, computed identically every day.
2. Make both metrics available through a BI layer (Power BI) and a lightweight read API within a pipeline that runs unattended on a daily schedule.
3. Capture at least one verified, quantified business baseline (e.g., current unmeasured scrap cost or current time-to-insight) before the internship ends, so the platform's value is provable, not asserted.
4. Build a portfolio artifact that demonstrates real cloud data engineering judgment — knowing when a cloud service adds value and when it would only add cost and ceremony, including the judgment to redesign around a hard financial constraint without quietly losing rigor.
5. Produce a repository and documentation set that a Senior Data Engineer would recognize as internally consistent: every technology choice has a stated reason, and every rejected alternative has a stated reason for rejection.

---

## 4. Project Scope

**In scope (MVP):**
- Ingestion of production, downtime, and QC data directly into native BigQuery tables (`fplip_bronze` dataset)
- Medallion transformation (Bronze/Silver/Gold) via dbt against BigQuery (`fplip_bronze` / `fplip_silver` / `fplip_gold` datasets)
- `oee_daily` and `scrap_root_cause_summary` Gold marts
- Airflow orchestration with idempotent, retryable tasks, run on a daily schedule via GitHub Actions
- Data contracts for every Bronze source
- dbt tests (generic + singular + unit tests) as promotion gates between layers
- Power BI dashboard and a read-only FastAPI service against Gold
- CI/CD via GitHub Actions
- Infrastructure as Code (Terraform, `google` provider) for the BigQuery datasets and IAM bindings
- Documentation: README, architecture doc, data dictionary, runbook, ADR log

**Conditional (Phase 2, only if energy meter data exists and MVP finished with time remaining):**
- `energy_cost_per_unit` Gold mart
- Threshold-based alerting extended to energy metrics

**Explicitly out of scope, stated and defended, not just omitted:**
- Kafka / event streaming — no business requirement is time-sensitive below a daily cadence; introducing streaming here would be solving a problem the factory doesn't have.
- Spark / Databricks / Hadoop — data volumes (low hundreds of rows/day across all sources) do not approach the threshold where distributed compute earns its operational cost.
- Kubernetes — one engineer, no persistent compute host at all in this version; Kubernetes' value (multi-service scaling, complex rollout strategies) has no counterpart problem here.
- Redis / Cassandra / Flink — no caching-at-scale, no wide-column access pattern, no stream processing requirement exists in this platform.
- Microservices decomposition of the API — a four-endpoint read layer with one real consumer does not benefit from service boundaries; it only adds deployment surface area.
- A dedicated data catalog (Purview/DataHub/OpenMetadata) — governance at eight Gold-adjacent models is handled adequately by dbt docs and the data dictionary; a catalog tool solves a discovery problem that exists at dozens-of-models scale, not this scale.
- A semantic layer (dbt Semantic Layer/MetricFlow) — with two governed metrics, there is no metric-consistency problem across multiple BI tools for a semantic layer to solve.

---

## 5. Functional Requirements

| ID | Requirement |
|---|---|
| FR-01 | System shall ingest daily production run data (machine, shift, product, quantities, timestamps) directly into native BigQuery tables in the `fplip_bronze` dataset. |
| FR-02 | System shall ingest daily downtime/stop-reason event data. |
| FR-03 | System shall ingest daily QC inspection records with defect classification. |
| FR-04 | System shall validate schema conformance for every source file before promoting it beyond Bronze. |
| FR-05 | System shall transform Bronze data into conformed Silver dimensional and fact models via dbt. |
| FR-06 | System shall compute `oee_daily` (availability, performance, quality, OEE) per machine per day in Gold. |
| FR-07 | System shall compute `scrap_root_cause_summary` per machine/shift/defect-type in Gold. |
| FR-08 | System shall reject promotion of any model whose dbt tests fail. |
| FR-09 | System shall expose Gold metrics via Power BI and a versioned, authenticated read-only API. |
| FR-10 | System shall alert a human on pipeline failure without requiring anyone to check manually. |
| FR-11 | System shall maintain an auditable log of schema and metric-definition changes (ADRs + dbt model versioning). |

---

## 6. Non-Functional Requirements

| Requirement | Target | Mechanism |
|---|---|---|
| Reliability | Daily pipeline succeeds without manual intervention in >95% of runs | Airflow retries with exponential backoff, idempotent loads |
| Maintainability | A new contributor can locate and modify any layer within 10 minutes | Consistent naming, dbt docs, ADR log, one-concern-per-folder repo structure |
| Scalability | Architecture tolerates 10x data volume without a rearchitecture | Native BigQuery columnar storage in Bronze, clustered Gold tables on filter/join keys, SQL-native transforms |
| Security | Credentials and data access follow least privilege at every layer | Dataset-scoped IAM roles, two narrowly-scoped service accounts, no static keys committed to git |
| Performance | Daily pipeline completes inside its scheduling window (before next shift starts) | Full-refresh `table` materializations sized correctly to this data volume (no incremental/MERGE dependency — see Section 26), clustering on join keys |
| Availability | Dashboard/API reachable during business hours with graceful degradation | Health-check endpoints, container/service restart policies |
| Data Quality | No untested model reaches Gold | dbt tests (generic, singular, and unit) as hard promotion gates |
| Governance | Every metric has one documented owner and one documented definition | Data contracts, data dictionary, ADR log |
| Cost | Zero cloud spend for the full internship duration — no credit card, no linked billing account, at any point | Google BigQuery Sandbox mode (indefinite free tier: 10GB storage / 1TB query processing per month), GitHub Actions free tier for orchestration and CI, no paid compute host anywhere in the design |
| Auditability | Any Gold-layer number is traceable to its Bronze source | Immutable, append-only Bronze loads, full dbt lineage graph, no in-place mutation of raw data |

---

## 7. Data Sources

| Source | Format (current state) | Format (ingested) | Owner | Update frequency | Reliability |
|---|---|---|---|---|---|
| Production logs | Excel / paper, digitized manually or via Nizzar export | CSV, loaded directly into a native BigQuery table | Production dept. | Daily, end-of-shift | Medium — manual entry, expect gaps |
| Downtime/stop logs | Paper reason-code sheets | CSV, loaded directly into a native BigQuery table | Production/Maintenance | Daily | Low-medium — free-text reason codes likely, requires mapping |
| QC inspection records | Excel | CSV, loaded directly into a native BigQuery table | Quality dept. | Daily | Medium |
| Nizzar (ERP) | Transactional exports, if accessible | CSV | IT/ERP admin | On request | Unconfirmed — treated as optional enrichment, never a hard dependency |

**Fallback provision (carried forward unchanged):** a Faker-based synthetic data generator, schema-matched to the contracts in Section 8, ships from week one. If real access to any source is delayed beyond Week 2, the pipeline runs against synthetic data without any code change, and the switch to real data is a configuration change, not a rebuild.

---

## 8. Data Contracts

Each Bronze source is governed by an explicit contract, versioned in the repository (`contracts/*.yaml`), not left as an implicit assumption inside ingestion code.

**Contract fields per source:** schema (column name, type, nullability), primary/natural key, expected update frequency, freshness SLA, owning department, a `confidence` tag (`verified` | `estimated` | `unconfirmed`), and a named contact for schema questions.

**The contract that matters most in this project** is `dim_product.standard_cycle_time_sec` — the single input identified as the platform's largest silent-failure risk, because it feeds directly into the OEE performance component and has no natural data-quality test that can catch a plausible-but-wrong value. Its contract explicitly requires: (a) a named manufacturing-engineering source for the value, (b) a `confidence` tag defaulting to `estimated` until manually verified against floor observation, and (c) surfacing that confidence tag directly in the data dictionary and dashboard tooltip — so a manager reading `oee_daily` can see when performance is built on a verified input versus a placeholder. A wrong number that's labeled "estimated" is honest engineering; a wrong number presented as fact is the failure mode this contract exists to prevent.

Schema-breaking changes to any contract trigger a CI failure (Section 21), not a silent pipeline success against a shape the models no longer expect. The contract's `schema` field also doubles as the explicit column schema passed to each BigQuery load job (Section 16) — contracts are enforced at load time, not just documented.

---

## 9. Data Architecture

```
FACTORY SYSTEMS (production logs, downtime logs, QC sheets, Nizzar export)
        │
        ▼  (Airflow: extract, validate against contract, load)
BIGQUERY — fplip_bronze dataset  (native tables, as-received, schema-validated, one table per source, partitioned by ingestion date)
        │
        ▼  (dbt: stg_* views select directly from fplip_bronze — no physical staging hop)
        ▼  (dbt: clean, conform, join, dedupe)
BIGQUERY — fplip_silver dataset  (dims + facts, tested, full-refresh tables)
        │
        ▼  (dbt: aggregate, apply business logic — tests gate promotion)
BIGQUERY — fplip_gold dataset  (oee_daily, scrap_root_cause_summary)
        │
        ├──▶ Power BI  (native BigQuery connector, import mode, scheduled refresh)
        └──▶ FastAPI  (read-only, API-key auth, BigQuery Data Viewer IAM role scoped to fplip_gold)
```

The v2.0 rationale for keeping Bronze in object storage rather than a database — immutability matters more than query convenience at that stage — is resolved differently here, not abandoned: BigQuery's native tables give Bronze *both* properties at once. Loads are append-only (`WRITE_APPEND` batch load jobs, not DML — see Section 16), so nothing is ever mutated in place, and the data is immediately queryable without a second storage system or a staging hop. The two-hop object-storage-then-database pattern v2.0 needed to reconcile immutability with queryability simply isn't necessary once storage and warehouse are the same platform.

---

## 10. Cloud Architecture

**Storage & warehouse: Google BigQuery, Sandbox mode — a single platform for both roles.**
This removes the storage-vs-warehouse consistency decision v2.0 had to make (Section 10 of v2.0) entirely — there is no second service to keep consistent with, because Bronze, Silver, and Gold all live as BigQuery datasets inside one GCP project. The project is created with no billing account linked, which is what activates Sandbox mode: the same indefinite free tier (10GB storage, 1TB query processing/month) as the paid tier's on-demand pricing, minus DML/streaming/scheduled-query support and a 60-day table auto-expiration window (addressed in Section 12).

**Compute/orchestration:** Airflow runs inside a scheduled GitHub Actions workflow (`on: schedule: cron`) rather than on a persistent host. v2.0 hosted Airflow on a small Azure Container Instance or VM — an option that no longer exists under the current constraint, since any always-on compute host from a major cloud provider requires a linked billing account. Because every task in this pipeline is idempotent and no state needs to persist in the orchestrator itself between runs (only in BigQuery), Airflow can be started fresh in standalone/`LocalExecutor` mode inside a GitHub Actions runner, execute the day's DAG once, and tear down — with no loss of the retry/dependency semantics Section 25 relies on. GitHub Actions' free tier (unlimited minutes for public repos; 2,000 minutes/month for private ones) comfortably covers one short daily DAG run.

**Identity and secrets:** there is no Sandbox-mode equivalent to Azure Key Vault — Google Secret Manager, like Cloud Storage, sits behind an active billing account and isn't available here. This is a stated, accepted trade-off (Section 23), not an oversight: a single GCP service account per role, scoped to dataset-level IAM permissions only, with its JSON key stored as a GitHub Actions encrypted secret for scheduled/CI runs and a git-ignored local file for development.

---

## 11. Medallion Architecture

Unchanged in philosophy, relocated in implementation, with Bronze's definition tightened per the Phase 1 decision:

- **Bronze** — raw, as-received, schema-validated-but-unmodified, loaded directly into native BigQuery tables in the `fplip_bronze` dataset. There is no separate landing zone: Bronze *is* the first cloud-native layer. Exists so a Silver defect never requires re-extraction from a source system.
- **Silver** — cleaned, conformed, deduplicated, joined; still tables, not yet business metrics. Lives in the `fplip_silver` BigQuery dataset, queried and tested relationally from this point forward.
- **Gold** — the two business marts, computed once, tested, and trusted by every downstream consumer (dashboard, API), in the `fplip_gold` dataset. No consumer is permitted to recompute OEE or scrap rate independently — that duplication is exactly the trust problem this platform exists to eliminate (Section 2).

---

## 12. Storage Strategy

| Layer | Location | Format | Retention | Access pattern |
|---|---|---|---|---|
| Bronze | BigQuery `fplip_bronze` dataset | Native BigQuery tables, one per source, partitioned by an `_ingested_at` DATE column | See auto-expiration note below | Loaded by Airflow only (`WRITE_APPEND`); queried by dbt `stg_*` views |
| Silver | BigQuery `fplip_silver` dataset | Native BigQuery tables (dims + facts) | Rebuilt daily (full-refresh); dbt snapshots for SCD2 dims | Read by dbt (Gold build) |
| Gold | BigQuery `fplip_gold` dataset | Native BigQuery tables, clustered on filter/join keys | Rebuilt daily (full-refresh) | Read by Power BI + API |

**On Sandbox's 60-day table auto-expiration:** since every table in every dataset is rebuilt daily via full-refresh `table` materializations (`CREATE OR REPLACE TABLE AS SELECT` — a DDL statement, unaffected by the Sandbox's DML restriction), each rebuild resets that table's expiration clock. In practice, no table in an actively-run daily pipeline ever reaches 60 days without activity, so the limit does not bind. The one documented recovery path, should the daily schedule ever be paused for more than 60 days: a single `dbt run --full-refresh` recreates every table from Bronze — a one-command recovery, not a redesign. This is stated explicitly as a verified assumption, not left implicit the way v1.0 left its fact-grain assumption.

The v2.0 Hot→Cool lifecycle-tiering setting has no BigQuery Sandbox equivalent and isn't needed — there is no separate "raw" tier to age out of, since Bronze is the raw layer.

---

## 13. Warehouse Design

**Decision: Google BigQuery, Sandbox mode.**

**Options considered:**

| Option | Verdict | Reasoning |
|---|---|---|
| **A — Google BigQuery (Sandbox mode)** | **Selected** | The only option that requires no credit card and no linked billing account at any point, has no time-boxed trial clock to fight the 8–12 week timeline, and collapses storage and warehouse into a single platform. `dbt-bigquery` is a Tier-1, dbt Labs–maintained adapter with full support for contracts and unit tests. Its real constraints (no DML/streaming, 60-day table auto-expiration) are addressed explicitly in Sections 12 and 26 and do not bind at this project's data volume. |
| **B — Snowflake (Free Trial)** | Rejected for this scope | The 30-day trial clock is shorter than a third of the 8–12 week project timeline; the account would suspend mid-project (around the Week 4–5 milestone), forcing a full re-signup and re-deployment right as the demo and continuous-operation deliverables are due. It also duplicates a dbt+Snowflake portfolio project already built elsewhere, so adopting it here adds no resume differentiation. Remains the correct choice for the multi-factory evolution stage (Section 32), where a paid account would be justified regardless. |
| **C — Azure SQL Database (Serverless)** | Retired, not merely deprioritized | v2.0's selected option. Every path to it now requires an active Azure billing account, which is the exact constraint this revision exists to remove — this is a hard disqualification, not a preference ranking. |
| **D — Microsoft Fabric Warehouse** | Rejected | Same billing-account dependency as Option C, on top of the multi-workload capacity/governance overhead v2.0 already identified as premature at this scale. |
| **E — MotherDuck** | Considered, not selected | Genuinely free with no card required, but its 2026 free-tier restructuring caps the no-cost plan at 10 compute-hours/month and 3 users — tight against a daily-scheduled pipeline running for 8–12 weeks. Its dbt adapter (`dbt-duckdb`) is community-maintained rather than dbt Labs–maintained, and it carries materially lower name-recognition with the recruiters and hiring managers this candidate is targeting than BigQuery does. |

The rejected options are not weaker technologies in the abstract — Snowflake and Fabric remain the correct choice at a different scale or under a different financial constraint, and Section 32 states explicitly where each becomes justified again.

---

## 14. Data Modeling

Star schema, unchanged in shape from v2.0 — the model is vendor-agnostic. Every Silver/Gold model still carries an explicit dbt model contract (enforced column names and types, fully supported by `dbt-bigquery`) so that a schema change anywhere upstream fails loudly in CI rather than silently reaching a Power BI report.

**Dimensions**

| Table | Grain | Key Columns |
|---|---|---|
| `dim_machine` | one row per machine | `machine_id` (PK), `machine_name`, `line`, `product_type_default` |
| `dim_product` | one row per SKU | `product_id` (PK), `product_name`, `product_family`, `standard_cycle_time_sec`, `cycle_time_confidence` |
| `dim_shift` | one row per shift definition | `shift_id` (PK), `shift_name`, `start_time`, `end_time` |
| `dim_date` | one row per calendar day | `date_id` (PK), `date`, `day_of_week`, `is_holiday` |
| `dim_defect_type` | one row per defect category | `defect_type_id` (PK), `defect_name`, `defect_category` |
| `dim_downtime_reason` | one row per stop-reason code | `reason_id` (PK), `reason_name`, `reason_category` |

**Facts**

| Table | Grain | Key Columns | Measures |
|---|---|---|---|
| `fct_production_run` | one row per **run** — see Section 15 for the corrected grain definition | `run_id` (PK, surrogate), `machine_id`, `product_id`, `shift_id`, `date_id` (FKs), `run_sequence_number` | `planned_units`, `produced_units`, `good_units`, `run_duration_sec` |
| `fct_downtime_event` | one row per stop event | `event_id` (PK), `machine_id`, `shift_id`, `date_id`, `reason_id` (FKs) | `duration_sec` |
| `fct_qc_inspection` | one row per inspected batch | `inspection_id` (PK), `run_id` (FK), `defect_type_id` (FK, nullable) | `units_inspected`, `units_rejected` |

`dim_machine` and `dim_product` are tracked via dbt snapshots (SCD Type 2), unchanged from v2.0 — the data dictionary continues to note explicitly whether an SCD2 change was actually exercised during the build.

---

## 15. Fact Table Grain (Corrected)

Unchanged from v2.0 — this fix is about modeling logic, not cloud platform. The grain of `fct_production_run` is one row per **run**, uniquely identified by `(machine_id, shift_id, product_id, date_id, run_sequence_number)`. `run_sequence_number` increments for each distinct start/stop cycle of the same machine/shift/product/day, sourced directly from the production log's own run-boundary markers if present, or derived during Silver transformation from contiguous non-zero-output time windows otherwise. This is validated against real sample data in Week 1 (Section 33) before any Gold model is built on top of it.

---

## 16. Bronze Layer

Raw-as-received data, schema-validated against the Section 8 contract at load time, loaded directly into native BigQuery tables in the `fplip_bronze` dataset — one table per source (`fplip_bronze.production_runs`, `fplip_bronze.downtime_events`, `fplip_bronze.qc_inspections`, `fplip_bronze.nizzar_export`). There is no separate landing zone and no intermediate file-format conversion step: v2.0 converted raw CSV to partitioned Parquet specifically to get query-friendly columnar storage in object storage; BigQuery's native tables are already columnar, so that conversion step is dropped as unnecessary complexity, not a lost capability.

No business logic, no joins, no aggregation — Bronze exists purely to make ingestion replayable and auditable. Each Bronze table is partitioned by an `_ingested_at` DATE column and carries `_ingested_at` and `_source_file` metadata columns on every row, preserving the same lineage-traceability guarantee v2.0 established.

Loads use `WRITE_APPEND` batch load jobs via the `google-cloud-bigquery` Python client, executed as an Airflow task. This is a genuine, not incidental, fit with the Sandbox's restrictions: batch load jobs are explicitly supported in Sandbox mode (up to 10GB/month), while `INSERT`/`UPDATE`/`MERGE` DML and streaming inserts are not. Because loads only ever append, nothing is ever mutated in place — if anything, this makes Bronze's immutability guarantee stricter than v2.0's, where an `UPDATE` was at least theoretically possible against Azure SQL staging tables.

---

## 17. Silver Layer

dbt's own staging models (`stg_production_runs`, `stg_downtime_events`, `stg_qc_inspections`) are lightweight views selecting directly from `fplip_bronze` tables — there is no separate physical staging load step, because BigQuery can be queried directly by dbt without an intermediate database hop the way Azure SQL Database required one in v2.0. This removes an entire task from the pipeline (v2.0's `load_staging_azuresql`) with no loss of function, since dbt's staging-view pattern is the standard, recommended dbt approach regardless of warehouse.

dbt then builds Silver models on top of those staging views inside the `fplip_silver` dataset: type casting, timestamp normalization, reason-code and defect-code mapping to dimension tables, deduplication, and referential-integrity conformance. Silver is "one clean, joined version of the truth" — not yet a business metric, and tested to the same standard as Gold (Section 19), because a silent Silver defect corrupts every Gold model built on top of it.

---

## 18. Gold Layer

Two MVP marts, computed once, contract-enforced, and tested as promotion gates, in the `fplip_gold` dataset:

- **`oee_daily`** — availability, performance, quality, and OEE per machine per day. `performance` explicitly carries forward the `cycle_time_confidence` flag from `dim_product` (Section 8/14) so any consumer can see when the number is built on a verified versus estimated input.
- **`scrap_root_cause_summary`** — scrap rate and defect-type breakdown by machine/shift/product.

Both marts are covered by dbt model contracts (Section 20) — an explicit, enforced schema (column names, types, not-null constraints), fully supported by `dbt-bigquery`, that fails CI if violated rather than allowing a silent shape change to reach Power BI.

---

## 19. Data Quality

| Rule Type | Example | Layer enforced |
|---|---|---|
| Duplicate detection | `unique` on `run_id` | Silver |
| Null detection | `not_null` on all foreign keys | Silver + Gold |
| Accepted values | `defect_category` restricted to a fixed list | Silver |
| Referential integrity | every `fct_qc_inspection.run_id` exists in `fct_production_run` | Silver |
| Freshness | Bronze table for "yesterday" must show a matching `_ingested_at` partition before Gold build runs | Bronze→Silver gate |
| Row-count anomaly | today's row count compared to a 7-day rolling average; volume caveat noted below | Bronze→Silver gate |
| Business rule (singular test) | `0 <= oee <= 1`; `good_units <= produced_units` | Gold |
| **Formula unit test** | dbt unit test asserting `oee_daily.performance` computes correctly against mocked `standard_cycle_time_sec`, `produced_units`, `run_duration_sec` inputs, including edge cases (zero planned time, cycle time flagged `estimated`) | Gold |

The row-count anomaly check carries an explicit caveat in the data dictionary: at this factory's expected daily volume (likely dozens of rows per source), a 7-day rolling average is a directionally useful but statistically weak signal, and the check is documented as "flag for human review," not "auto-fail the pipeline."

The formula unit test remains the direct fix for the top-ranked hidden risk carried forward from v1.0: no row-level dbt test can catch a plausible-but-wrong `standard_cycle_time_sec`, because the value is structurally valid at any number. A unit test with mocked inputs at least guarantees the *formula itself* is correct; the Section 8 contract and confidence tag handle the input-trust problem the unit test cannot.

---

## 20. Testing Strategy

| Tier | Covers | Runs |
|---|---|---|
| Unit tests (Python) | Ingestion/loader logic (schema casting, contract validation) | Every PR (CI) |
| dbt unit tests | Business-logic formulas (OEE components) against mocked inputs | Every PR (CI) |
| dbt generic/singular tests | Silver/Gold row-level constraints | Every PR (CI) + every production run |
| Integration tests | Loader against a real (test) BigQuery dataset | Every PR (CI) |
| End-to-end tests | Full DAG run against sample/synthetic data, Gold tables assert-checked | Nightly / pre-release |
| Model contracts | Enforced Gold schema (Section 14/18) | Every `dbt run`, fails loudly on violation |

CI provisions a temporary, PR-scoped BigQuery dataset (`fplip_ci_pr_<number>`) inside a second, dedicated CI-only Sandbox project — kept separate from the "production" demo project so a bad PR can never touch real Bronze/Silver/Gold data or eat into its query/storage quota. The job runs `dbt seed && dbt build` (which covers run + generic/singular/unit tests + model contracts) against that temporary dataset, then drops it unconditionally at the end of the job, pass or fail. This is the same dataset-per-PR pattern the dbt ecosystem already treats as best practice for warehouse-native adapters (the "Slim CI" pattern), and it is a closer real-world signal of correctness than the v2.0 approach of testing against an ephemeral SQL Server container, since it exercises BigQuery's actual SQL dialect and job semantics rather than a substitute engine — while remaining fully free.

---

## 21. CI/CD

```
GitHub Actions (on every PR to dev/main):

  lint:
    - ruff check .
    - sqlfluff lint dbt/

  contract-check:
    - validate contracts/*.yaml against current Bronze schemas
    - fail if a source schema has drifted without a contract update

  dbt-test:
    - create temporary dataset in the CI Sandbox project (fplip_ci_pr_<PR#>)
    - dbt seed && dbt build   (run + generic/singular/unit tests + model contracts)
    - drop temporary dataset (always, even on failure)

  terraform-plan:
    - terraform validate && terraform plan   (no auto-apply — see Section 29)

  docker-build:
    - docker compose build   (local dev stack)

GitHub Actions (on schedule, daily):

  run-pipeline:
    - spin up Airflow (standalone/LocalExecutor) inside the runner
    - execute the FPLIP DAG once against the production Sandbox project
    - tear down — no state persisted in the orchestrator between runs
```

Deployment to the production Sandbox project remains a deliberate manual `terraform apply`, not an automated CD pipeline — the reasoning is unchanged from v2.0: automating infrastructure deployment for a single-environment, single-maintainer project solves a problem this project doesn't have, and the manual step keeps a human decision point in front of any change, however small. The `contract-check` job remains the direct enforcement mechanism for Section 8.

---

## 22. Monitoring

- **Pipeline monitoring:** Airflow UI (accessed via the run's logs/artifacts, since the scheduler is no longer a persistent host) — task status, duration trend, retry count.
- **Cloud resource monitoring:** BigQuery's own built-in job history via `INFORMATION_SCHEMA.JOBS` (bytes processed, slot time, load-job status) — free, built into BigQuery by default, and specifically useful here for keeping an eye on the Sandbox's 1TB/month query cap and 10GB storage cap, the direct equivalent of the DTU/storage visibility Azure Monitor provided in v2.0.
- **Freshness/row-count checks:** as defined in Section 19, surfaced as Airflow task failures, not a separate observability platform.
- **Alerting:** Airflow `on_failure_callback` to a Slack webhook.
- **Logging:** structured (JSON) logs at every pipeline stage, including row counts in/out, `_ingested_at` timestamps, and contract-validation results, so a failure is diagnosable from logs/CI-run artifacts alone.

---

## 23. Security

- **Secrets:** Google Secret Manager, like Cloud Storage, sits behind an active billing account and is not available in Sandbox mode — a stated, accepted trade-off, not an oversight. In its place: a single GCP service account per role (below), whose JSON key is stored as a GitHub Actions encrypted secret for scheduled/CI runs and as a git-ignored local file for development. This is a real reduction in security posture relative to Key Vault + managed identity (a static key file has to exist somewhere, however carefully scoped), and it is documented here as exactly that, not described as an equivalent replacement.
- **IAM roles (replacing v2.0's SQL logins):** `ingestion_sa` — `BigQuery Data Editor` scoped to the `fplip_bronze`/`fplip_silver`/`fplip_gold` datasets specifically (never project-wide `Editor`/`Owner`), used only by Airflow/dbt; `api_sa` — `BigQuery Data Viewer` + `BigQuery Job User` scoped to `fplip_gold` only, used only by FastAPI. No standing "break-glass admin" key is stored anywhere; break-glass access is the developer's own interactive Google account login, never automated.
- **Network:** BigQuery is a managed API endpoint, not a VM with a firewall surface, so access control is entirely IAM-based. This removes an entire category of v2.0 concern (firewall rules, VNet service endpoints) rather than replacing it with an equivalent.
- **Backups:** BigQuery's built-in time travel (7 days in Sandbox/standard mode — the 90-day window mentioned in some Snowflake trial marketing is a different product and doesn't apply here) gives point-in-time recovery for an accidental table drop or bad overwrite within that window. Beyond 7 days, recovery relies on dbt's ability to fully rebuild any Silver/Gold table from Bronze — real recovery capability, since Bronze is retained and re-loadable from source files, but slower than the Azure SQL Database PITR v2.0 had. Documented here as a real, accepted trade-off, not glossed over.
- **Least privilege extended to Terraform:** the Terraform service account is scoped to `roles/bigquery.admin` + `roles/iam.serviceAccountAdmin` on this one GCP project only, never organization-wide.

---

## 24. Governance

- **Metric ownership:** every Gold column has one named owner (a role, e.g., "Production Manager owns `oee_daily.availability` definition") recorded in the data dictionary.
- **ADR log (`docs/adr/`):** one markdown file per material decision (grain definition, warehouse choice, storage choice, auth model, and the Section 13/23 constraint-driven trade-offs specific to v3.0), each stating the decision, the date, the alternatives considered, and the reasoning.
- **Data dictionary:** generated in part by `dbt docs`, hand-curated for business-facing definitions and the `cycle_time_confidence` flag.
- **Change management:** any change to a data contract (Section 8) or a Gold model's contracted schema requires a corresponding ADR entry — enforced socially in a one-person project, but the practice itself is what a larger team would formalize as a review gate.

---

## 25. Airflow Pipelines

```
extract_production ─┐
extract_downtime   ─┼──▶ validate_contracts ──▶ load_bronze_bigquery
extract_qc         ─┘                                    │
                                                          ▼
                                               dbt_run_silver ──▶ dbt_test_silver
                                                          │
                                          ┌───────────────┴───────────────┐
                                          ▼                                ▼
                               dbt_run_gold_oee ──▶ dbt_test_gold   dbt_run_gold_scrap ──▶ dbt_test_gold
```

Idempotent tasks throughout (safe to rerun for a given date without duplication), 3 retries with exponential backoff per task, no business logic inside Airflow operators — orchestration only, unchanged from v2.0. The `validate_contracts` task remains the runtime enforcement companion to the CI-time `contract-check` job (Section 21). The one structural change is `load_bronze_bigquery` replacing v2.0's `load_bronze_adls` + `load_staging_azuresql` pair — one task doing the work two used to, since there's no separate object-storage hop and no separate staging-database hop anymore (Sections 16–17). The `@daily` schedule is now expressed as a GitHub Actions cron trigger rather than a persistent scheduler process (Section 10); because every task here is idempotent, that's a hosting change, not a semantics change.

---

## 26. dbt Models

Project structure unchanged in spirit (`models/bronze/` staging views, `models/silver/dims|facts/`, `models/gold/`), with `dbt-bigquery` as the adapter. Silver and Gold models use the `table` materialization throughout (full-refresh, `CREATE OR REPLACE TABLE AS SELECT`) rather than `incremental`, because BigQuery Sandbox blocks the `MERGE` statement dbt's incremental strategy depends on. This is a real, stated constraint rather than a silent scope narrowing — and one this project's own data volume (low hundreds of rows/day) never justified working around in the first place; v2.0 didn't use incremental models either. `contracts:` blocks remain enforced on every Gold model, and the `unit_tests/` directory (dbt's native unit-testing feature) sits alongside the existing `tests/` singular tests. Naming conventions (`stg_`, `dim_`, `fct_`, plain business names for marts) and the one-model-one-`SELECT` rule carry forward unchanged.

---

## 27. API Layer

Unchanged in scope and philosophy — a read-only FastAPI service (`/health`, `/oee/daily`, `/oee/summary`, `/scrap/root-cause`) backed by the `api_sa` service account (`BigQuery Data Viewer` scoped to `fplip_gold` only), authenticated via a single API key header. This API exists to demonstrate the "last mile" skill, and its necessity should be defended in an interview as exactly that, not oversold as solving a real integration requirement that doesn't yet exist.

---

## 28. Dashboard Layer

Power BI, unchanged from v2.0 — Power BI's native BigQuery connector (import mode; BigQuery Sandbox doesn't support the always-on capacity that DirectQuery-style live connections would want, so scheduled import refresh is the right fit for a daily-batch workload regardless) gives a clean, low-friction connection, and Power BI remains the more recognized enterprise BI skill for the international roles this candidate is targeting. The KPI set is unchanged (OEE trended by machine, OEE component breakdown, downtime Pareto, scrap rate by machine/defect-type/shift) — every chart maps to a tested, governed Gold column, no exceptions.

---

## 29. Deployment

Infrastructure is provisioned via Terraform (`infra/`, `google` provider) covering: the GCP project itself, with an explicit, commented Terraform line confirming no billing account is linked (so a reviewer sees the zero-cost posture as a deliberate design decision, not an accident); the three BigQuery datasets (`fplip_bronze`/`fplip_silver`/`fplip_gold`); and the IAM bindings for `ingestion_sa` and `api_sa`. There is no compute-hosting resource in this Terraform config at all, since Airflow now runs inside GitHub Actions rather than a provisioned host (Section 10) — a genuine reduction in infrastructure footprint relative to v2.0's four resources, not just a cheaper version of the same footprint. `terraform apply` is still run manually by the developer, not by CI — the same reasoning as v2.0: a human decision point in front of any infrastructure change is good practice regardless of whether that change costs money.

**One honest change from v2.0 worth stating plainly rather than glossing over:** v2.0's Docker Compose + Azurite setup let a stranger clone the repo and demo the entire pipeline completely offline, with zero Azure account of any kind. There is no equivalently faithful local emulator for BigQuery, and building one purely to preserve that guarantee would be solving a problem the real constraint (no card, not no signup) doesn't actually require solving. The v3.0 equivalent is: `docker compose up` still stands up Airflow and dbt locally, and any reviewer can create their own zero-cost BigQuery Sandbox project — a free Google account and roughly five minutes, no card at any point — and run the full live pipeline against it. For a reviewer who wants zero account of any kind, the Week 8 recorded demo (Section 33) remains the fallback. This is a small, stated increase in demo friction relative to v2.0, traded for the removal of an Azure billing account requirement — the trade this whole revision exists to make.

---

## 30. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Data access delayed/incomplete | High | High | Synthetic data generator ships Week 1 (Section 7) |
| `standard_cycle_time_sec` unreliable | High | High | Data contract confidence tag + dbt unit test on the formula (Sections 8, 19) |
| Fact grain assumption wrong | Now resolved pre-build | — | Explicit grain definition validated against real sample data before Gold build (Section 15) |
| No domain expert available to validate OEE against floor reality | Medium-High | Medium | Named metric owner requirement in governance (Section 24); escalate to Week 1 if unresolved |
| BigQuery Sandbox's 10GB storage / 1TB query-per-month caps approached | Low | Low-Medium | Expected data volume (low hundreds of rows/day) is roughly three orders of magnitude below the monthly query cap; `INFORMATION_SCHEMA.JOBS` monitoring (Section 22) gives early warning if usage trends up unexpectedly |
| Sandbox's DML restriction blocks a future incremental-model need | Low | Low | Full-refresh materializations are correctly sized to this project's actual data volume (Section 32 already excludes incremental models as unjustified here); if volume ever grows enough to need them, that's also the point a paid BigQuery edition or Snowflake becomes justified anyway |
| Service-account key (JSON) leaked, since Secret Manager isn't available in Sandbox mode | Low-Medium | Medium | Keys scoped to dataset-level IAM roles only (never project Owner/Editor), stored solely as a GitHub encrypted secret and a git-ignored local file; rotation documented as a runbook step |
| Low daily data volume makes anomaly-detection statistically weak | Medium | Low-Medium | Documented as "flag for review," not auto-fail (Section 19) |
| Solo dev scope creep into Phase 2 or into unjustified cloud services | Medium | Medium | Explicit out-of-scope list (Section 4) reviewed at each weekly milestone |
| Terraform/cloud IaC unfamiliarity adds unplanned learning curve | Medium | Medium | Scoped to three datasets + IAM bindings only; no compute resource, no networking complexity at all |

---

## 31. Assumptions

- The factory can provide at least sample-quality production, downtime, and QC records within the first two weeks; if not, the project proceeds on synthetic data with real data substituted later without a redesign.
- No source system requires sub-daily latency; all business questions this platform answers are inherently daily-or-slower in nature.
- The developer has a free Google account and can create a GCP project with no billing account linked (BigQuery Sandbox mode); no resource in this design requires a linked billing account, a credit card, or paid capacity to build and demo.
- `standard_cycle_time_sec` may not be authoritatively knowable within the project timeline; the platform is designed to be honest about that uncertainty (Section 8) rather than to assume it away.
- One engineer, working solo, without an internal Data Engineering mentor, for 8–12 weeks.

---

## 32. Future Improvements

Explicitly sequenced, not a wishlist — each item states the scale threshold that would justify it:

- **Multi-factory expansion** → justifies a `factory_id` dimension (decorative at n=1, real at n>1), a managed orchestration service once coordinating multiple daily DAGs across sites exceeds one engineer's manual oversight, and a genuine case for Snowflake, Microsoft Fabric Warehouse, or a paid BigQuery edition once cross-factory analytical volume outgrows a single Sandbox project's free-tier caps.
- **Real-time requirement emerging** (e.g., a future line-stoppage alerting requirement with sub-minute latency) → the first and only point at which event streaming (Pub/Sub if staying on GCP, Kafka or Event Hubs otherwise) becomes justified in this architecture.
- **Cross-team governance need** (multiple domains, multiple data owners beyond one factory's departments) → the point at which a data catalog (e.g., Purview, DataHub) stops being over-engineering and starts being necessary.
- **ML-driven predictive maintenance**, once a governed, trusted Gold layer exists to train on — deliberately sequenced *after* this platform, not alongside it, because a predictive model built on ungoverned data inherits every trust problem this project exists to remove.

---

## 33. Project Timeline

| Week | Objectives | Deliverables | Success Criteria |
|---|---|---|---|
| 1 | Factory discovery + GCP foundation | Data contracts drafted, grain validated against real samples, Terraform for BigQuery datasets/IAM applied, synthetic data generator working | Can name the exact source/format for each stream; `terraform apply` succeeds against a Sandbox project; synthetic pipeline runs end to end |
| 2 | BigQuery Bronze ingestion | `extract_*` + `load_bronze_bigquery` DAGs, contract validation live | Bronze tables populate daily without manual intervention |
| 3 | Silver dims | `stg_*` views over `fplip_bronze`, `dim_*` models, tests passing | Silver dims pass all dbt tests |
| 4 | Silver facts + grain validation checkpoint | `fct_production_run` (corrected grain), `fct_downtime_event` | Grain confirmed against real multi-run-per-day cases if present |
| 5 | First Gold table + formula unit tests | `oee_daily`, dbt unit tests on the OEE formula | Unit tests pass against mocked edge cases; values sane on manual spot-check |
| 6 | Second Gold table + Power BI | `scrap_root_cause_summary`, dashboard live | A manager finds "top defect type by machine" in under 30 seconds |
| 7 | API, CI/CD, monitoring, security hardening | FastAPI live, GitHub Actions green including contract-check, service-account IAM scoping verified, alerting live | Deliberately broken pipeline run triggers a visible alert |
| 8 | ADRs, documentation, testing polish, demo, verified business number | README, architecture.md, data dictionary, runbook, ADR log complete, recorded demo, one verified business-impact number | Stranger clones the repo and can run the live demo against their own free BigQuery Sandbox project (no card, ~5 minute signup) in under 15 minutes, or watch the recorded demo with zero account at all |
| 9–12 (if available) | Section 2 hardening items from the optimization review: backup-restore drill, pre-commit hooks, dbt docs hosted, case-study one-pager | — | — |

---

## 34. Deliverables

- Working, orchestrated pipeline (Airflow via scheduled GitHub Actions, cloud-deployed and locally demoable)
- Two governed Gold marts with enforced contracts and unit-tested formulas
- Power BI dashboard and FastAPI service
- Terraform-provisioned BigQuery infrastructure (datasets + IAM bindings only — no compute host)
- Full documentation set: README, architecture.md, data_dictionary.md, runbook.md, ADR log
- CI/CD pipeline with contract enforcement
- Synthetic data generator (fallback + demo enabler)
- One verified, quantified business-impact statement

---

## 35. Technology Stack

| Technology | Role | Why chosen |
|---|---|---|
| Google BigQuery (Sandbox mode) | Bronze/Silver/Gold storage + warehouse (single platform) | Zero-cost, no-credit-card, indefinite free tier (10GB storage / 1TB query per month); collapses the separate storage-and-warehouse decision into one service; Tier-1 dbt adapter |
| dbt-core (`dbt-bigquery`) | Transformation, testing, contracts, lineage | Tier-1 adapter maturity, equal to the `dbt-sqlserver`/`dbt-fabric` family v2.0 used; testing/contracts/unit-tests directly close the original review's top risk |
| Apache Airflow (via scheduled GitHub Actions) | Orchestration | DAG dependency modeling, retries, alerting, industry-recognized; hosting moved to a free scheduled CI runner since no paid always-on compute host is available |
| GCP IAM + service accounts | Secrets/identity | Replaces Key Vault/managed identity; dataset-scoped roles, keys held as GitHub encrypted secrets — a stated, accepted reduction in posture (Section 23), not a claimed equivalent |
| Terraform (`google` provider) | Infrastructure as Code | Reproducible, reviewable infra; scoped to three datasets + two IAM bindings, no compute resource |
| Power BI | Dashboard | Native BigQuery connector; stronger enterprise BI signal than a self-hosted tool for this candidate's target roles |
| FastAPI | Read API | Lightweight "last mile" layer; async-ready, auto-documented |
| GitHub Actions | CI/CD **and** orchestration host | Free, native to GitHub; now doing double duty as both the CI runner and the daily DAG-execution host |
| Docker Compose | Local dev/demo | Runs Airflow + dbt locally against the developer's (or a reviewer's own) free Sandbox project |

---

## 36. Architecture Diagrams

See Section 9 (data architecture / medallion flow) and Section 25 (Airflow DAG dependency graph). A third diagram — GCP resource topology (one project containing the three BigQuery datasets and two service accounts, with IAM-role arrows rather than credential arrows, and an explicit annotation that no billing account is linked) — belongs in `docs/architecture.md` and should be the first visual in the README, ahead of any code block.

---

## 37. Why Each Technology Was Selected

Every technology in Section 35 is selected against a stated, falsifiable criterion, not a popularity signal:

- **BigQuery Sandbox** — because it is the only option that meets the zero-card, zero-billing-account constraint without a time-boxed trial clock, and because collapsing storage and warehouse into one platform removes a whole category of cross-service consistency decisions v2.0 had to make.
- **dbt-core** — because testing, documentation, and lineage are not separable from transformation in this project's risk profile; the OEE formula's validity risk specifically requires dbt's unit-testing and contract features, not just SQL scripting.
- **Airflow** — because task-level retry semantics and explicit DAG dependencies are required the moment three independent sources must land before a downstream build can start; a cron job alone cannot express that dependency safely. Hosting it inside scheduled GitHub Actions runs, rather than a persistent host, is the direct consequence of having no paid compute option left.
- **GCP IAM + service accounts** — because credential leakage is the most common real-world security failure in small projects, and dataset-scoped roles are the closest available approximation to least-privilege once Secret Manager and Key Vault are both off the table.
- **Terraform** — because infrastructure that exists only as manual console clicks is neither reviewable nor reproducible, and this project's infrastructure footprint (three datasets, two IAM bindings) is small enough that Terraform adds real signal without real complexity.

---

## 38. Why Other Technologies Were Rejected

- **Azure SQL Database / ADLS Gen2** — v2.0's selected pair; retired outright because every path to either now requires an active Azure billing account, which is the exact constraint this revision exists to remove.
- **Microsoft Fabric Warehouse** — same billing-account dependency as above, plus the multi-workload capacity/governance overhead already identified as premature at this scale.
- **Snowflake** — genuinely portfolio-relevant, but its 30-day trial clock is shorter than a third of this project's timeline, and a second dbt+Snowflake project would duplicate a portfolio piece that already exists elsewhere. Correctly deferred to the multi-factory evolution stage (Section 32).
- **MotherDuck** — free tier is real but capped at 10 compute-hours/month after a 2026 pricing restructure, tight against a daily pipeline running 8–12 weeks; community-maintained dbt adapter rather than dbt Labs–maintained; weaker recruiter name-recognition than BigQuery.
- **Databricks / Spark / Delta Lake** — solves a distributed-compute problem this data volume does not have; using it anyway would be the exact "resume-driven architecture" failure mode the v1.0 devil's-advocate review identified.
- **Kafka / Event Hubs / Pub/Sub (now)** — no source in this system produces data faster than daily; a streaming layer would have nothing to stream. Revisit only under the Section 32 real-time trigger condition.
- **Hadoop** — superseded architecturally by BigQuery for this workload; no distinct capability it would add here.
- **Kubernetes / AKS** — one engineer, no persistent compute host at all in this version; Docker Compose (local) and scheduled GitHub Actions (cloud) fully cover this project's actual deployment topology.
- **Redis** — no caching-at-scale requirement; BigQuery's own query performance is more than sufficient at this row count.
- **Cassandra** — no wide-column, high-write-throughput access pattern exists anywhere in this platform.
- **Flink** — a stream-processing engine with no stream to process here; rejected for the same reason as Kafka.
- **Microservices decomposition** — the API has one real consumer and four endpoints; service boundaries would add deployment surface area without a corresponding scaling or team-ownership need.
- **A dedicated data catalog (Purview/DataHub)** — eight Gold-adjacent models are fully navigable via `dbt docs`; a catalog tool solves a discovery problem this project's model count doesn't yet create.
- **A semantic layer (MetricFlow)** — two governed metrics, one BI tool, one API — no metric-consistency-across-consumers problem exists yet for a semantic layer to solve.

---

## Closing Note

Version 3.0 is not a cheaper version of the platform — it is the version that took a hard financial constraint seriously enough to let it change the design, rather than working around it superficially. Every removal relative to v2.0 (the separate landing zone, the separate staging-load hop, the dedicated compute host, Key Vault) is traced here to either a real Sandbox limitation or a genuine simplification that limitation exposed, and every one of them is named as a trade-off where a trade-off was actually made — the security posture of a static service-account key, the slower recovery path without full PITR, the slightly higher demo friction of needing a free Google account. Nothing here exists because it was free; everything here exists because it was free *and* the honest engineering case for it, at this data volume and this budget, still holds up. If a reviewer asks "why is this in BigQuery Sandbox and not still Azure," the honest answer is now a specific one: the constraint was real, the redesign was traceable line by line, and the platform's actual job — one trusted number for OEE, one trusted number for scrap rate — never depended on which warehouse computed it.
