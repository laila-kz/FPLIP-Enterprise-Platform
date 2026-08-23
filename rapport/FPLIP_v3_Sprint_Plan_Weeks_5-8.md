# FPLIP v3.0 — Implementation Roadmap
## Sprint Plan: Weeks 5–8 (Gold Layer, Orchestration, API Serving & Portfolio Phase)

**Scope note, stated explicitly rather than assumed silently:** these four weeks cover Blueprint v3.0's Gold Layer, Orchestration, Serving, and Portfolio phase — Gold marts and formula unit tests through the daily-scheduled GitHub Actions production run, the FastAPI serving layer, and final documentation/demo packaging (blueprint Sections 18–19, 21–29, 33–36, mapped directly onto Section 33's own Weeks 5–8). This roadmap assumes the Foundation & Silver Layer phase (Weeks 1–4) is fully complete, per that sprint plan's own closing checklist.

No code is written below. No architecture is altered. Every task traces to a section of the frozen v3.0 blueprint.

---

## ⚠️ Flagged Before You Begin: Two Items to Resolve Before Week 5 Starts

Per the same instruction that governed the Weeks 1–4 plan — flag, don't silently fix, any genuine contradiction, unresolved dependency, or naming inconsistency found while planning against the frozen architecture.

**1. The Week 3 SCD2/DML spike outcome is a hard prerequisite for Week 5, not just a nice-to-have.** The Weeks 1–4 plan closed by saying Gold-layer work should not begin until "Week 3's SCD2/DML question has a documented, not assumed, answer, since that finding may shape how Gold-layer work references `dim_machine`/`dim_product` history." `gold_oee_daily` joins directly to `dim_product` for `standard_cycle_time_sec` and `cycle_time_confidence`, and to `dim_machine` for the machine dimension row — if the SCD2 snapshot mechanism turned out not to execute in Sandbox mode and an alternative history-tracking approach was substituted (e.g., a type-1-only table with a documented ADR accepting the loss of history, or a manually-maintained effective-dating pattern), every Gold model's join logic to these two dimensions needs to target whatever that resolved mechanism actually produced — not the SCD2 pattern as originally drafted. **Week 5, Task 5.0 below is a mandatory checkpoint that reads that ADR before any Gold SQL is written.** Do not skip it even if you remember the answer; the point is to have it written down and referenced, the same discipline the blueprint itself demands of every other decision (Section 24).

**2. A naming and scope question in this prompt's own Week 5 framing needs to be resolved against the frozen blueprint, not silently followed.** This prompt's Week 5 instructions name the deliverables `gold_oee_daily` and `gold_loss_tree_summary`. The frozen blueprint (Sections 4, 18, 26) names exactly two Gold marts — `oee_daily` and `scrap_root_cause_summary` — and Section 26 states table naming convention as "plain business names for marts," with no `gold_` prefix (the dataset itself, `fplip_gold`, already carries that namespacing; a repeated prefix on the table name is redundant, not wrong, but it is a deviation worth naming rather than adopting silently). More substantively: a "Loss Tree" mart, as a named third deliverable distinct from `scrap_root_cause_summary`, is not defined anywhere in the frozen Section 18 Gold layer scope, which lists exactly two marts.

That said, this is not pure scope invention — the Source Data Contract's `oee_loss_category` field on the Downtime Reason Code Master exists specifically to let downtime be bucketed into Availability-loss versus Performance-loss categories for exactly this kind of reconciliation, so the underlying analytical need is real and already provisioned for in the data model. **The resolution this roadmap adopts, stated explicitly rather than silently decided:** treat "loss tree" as the downtime-loss-attribution logic that belongs inside `oee_daily`'s Availability/Performance component build (using `oee_loss_category`), *not* as a third standalone Gold mart beyond the frozen two-mart scope. Week 5 below builds `oee_daily` (dropping the `gold_` prefix to match Section 26 convention) with an internal loss-attribution breakdown as part of that model, and defers a dedicated `scrap_root_cause_summary` mart to where it already belongs — its own build step within Week 5, per Section 33's own Week 5 milestone ("First Gold table + formula unit tests") being immediately followed by Week 6's "Second Gold table." If, after reading this, you actually want a third, separate mart, that is a legitimate call to make — but it is a scope change to the frozen blueprint, and per Section 24's change-management rule, it needs its own ADR before Week 5's Task 5.1 begins, not an implicit adoption of this prompt's naming.

---

# WEEK 5 — Gold Layer Aggregations & OEE / Loss-Attribution Metrics

## 1. Weekly Goal
Build and fully test the first Gold-layer mart, `oee_daily` — the platform's highest-risk, most-scrutinized model, since it's the direct fix for the validity risk (`standard_cycle_time_sec`) the entire blueprint has been building toward closing since Section 8. By the end of the week: `oee_daily` exists as a dbt model with an enforced contract, its Availability/Performance/Quality formulas pass dbt unit tests against mocked edge cases, and a downtime loss-attribution breakdown (Availability-loss vs. Performance-loss, using `oee_loss_category`) reconciles against total logged downtime per machine/shift/day. `scrap_root_cause_summary` — the second Gold mart — is scaffolded and its grain finalized, but its full build is intentionally sequenced into early Week 6 rather than crammed into this week (see Section 2 below).

## 2. Why This Week Comes Now
Nothing in Weeks 6–8 is buildable before this week, and this week itself cannot be rushed. Airflow orchestration (Week 6) has nothing meaningful to schedule until Gold models exist to run. The API (Week 7) has nothing to serve until Gold tables exist to query. And the OEE formula is the specific place the blueprint's own risk register (Section 30) rates highest-probability, highest-impact: `standard_cycle_time_sec` is "structurally valid at any number" (Section 19), meaning no row-level test can catch a wrong-but-plausible value — only a correct *formula*, proven via unit tests against mocked inputs, closes that risk. Rushing this week to also finish `scrap_root_cause_summary` in the same five days would mean rushing the one model this entire project's credibility depends on. Splitting the two Gold marts across the Week 5/6 boundary (exactly as Section 33's own timeline already does — "Week 5: First Gold table," "Week 6: Second Gold table") is not schedule padding; it's the blueprint's own pacing, preserved.

## 3. Prerequisites
- Week 4 fully closed out per that sprint plan's checklist: tested Silver dims and facts, IAM audit confirming `ingestion_sa` (not personal credentials) is in use, Slim CI green with verified per-PR dataset teardown.
- **The Week 3 SCD2/DML spike ADR exists, is dated, and states a definitive outcome** (see the flagged item above). Its outcome is read and understood before Task 5.0 is marked complete.
- `fct_production_run` (corrected grain), `fct_downtime_event`, `fct_qc_inspection` all exist in `fplip_silver`, pass their full Silver test suite, and have been spot-checked against real or synthetic sample data for at least one multi-run day.
- `dim_machine`, `dim_product` (with `standard_cycle_time_sec` and `cycle_time_confidence` populated, including at least one `estimated`-tagged row and one `unconfirmed`-tagged row in dev/synthetic data, per the Source Data Contract's closing note), `dim_shift`, `dim_downtime_reason` (with `oee_loss_category` populated on every row), and `dim_defect_type` all exist and pass tests.
- `contracts/dim_product.yaml` (or equivalent) is the actual source of truth you can point to when writing `oee_daily`'s own model contract — re-read it before this week begins, don't work from memory of what it said in Week 1.

## 4. Detailed Task Breakdown

**Task 5.0 — Mandatory checkpoint: confirm the dimension history mechanism (do this before any other task)**
- Open the Week 3 SCD2/DML ADR
- Confirm in writing (a note in your own working log, not just mental confirmation) which of the two outcomes applies: (a) `dbt snapshot` executes successfully in Sandbox mode and `dim_machine`/`dim_product` are true SCD2 tables, or (b) it does not, and a documented alternative is in place
- If (b), identify exactly which columns/keys the alternative mechanism exposes for "the dimension row that was current as of a given production date" — this is the join condition every Gold model below needs, and it may not be a simple `machine_id` equi-join if history is involved
- Do not proceed to Task 5.1 until this is written down and unambiguous

**Task 5.1 — Finalize the Availability/Performance/Quality grain decisions before writing SQL**
- Re-read the Source Data Contract's "Validation Against Analytical Requirements" section on OEE grain: Availability is machine+shift+day; Performance and Quality are run-grain, rolled up
- On paper (or in a scratch markdown file, not yet a dbt model), write out the exact aggregation path for each component:
  - Availability: `(shift_duration_sec - SUM(downtime duration_sec for that machine/shift/day)) / shift_duration_sec`
  - Performance: roll-up of `(produced_units * standard_cycle_time_sec) / run_duration_sec` across all runs in the machine/shift/day, weighted appropriately (decide and document whether this is a simple average or a duration-weighted average across runs — this is a real modeling decision, not a mechanical one)
  - Quality: `SUM(good_units) / SUM(produced_units)` across all runs in the machine/shift/day
  - OEE: `Availability * Performance * Quality`
- Enumerate every edge case that must not silently produce garbage: `shift_duration_sec = 0` (should not occur if Shift Master is correct, but code defensively), `produced_units = 0` for a run (Quality and Performance both divide by a produced/duration quantity that could be zero), `run_duration_sec = 0` (a logged run with no elapsed time), `standard_cycle_time_sec` null or `cycle_time_confidence = 'unconfirmed'`, and a shift with zero logged downtime (Availability should correctly resolve to 1.0, not null or an error)
- Decide, and write into an ADR, how each edge case resolves: does the row get excluded, does the component get set to `NULL` with a flag column, or does it get clamped? (Section 6's Data Quality target says untested models never reach Gold — this decision is what the unit tests in Task 5.3 will assert against, so it must exist before those tests are written)

**Task 5.2 — Build `oee_daily` staging logic**
- Create `models/marts/gold/oee_daily.sql` (no `gold_` prefix — see the flagged naming note above)
- Build the Availability CTE: join `fct_downtime_event` to `dim_shift` at machine/shift/day grain, sum `duration_sec`, compute Availability per Task 5.1's formula
- Build the Performance/Quality CTE: join `fct_production_run` to `dim_product` for `standard_cycle_time_sec`/`cycle_time_confidence`, compute run-level Performance, roll up to machine/shift/day per the weighting decision made in Task 5.1
- Join the two CTEs on `(machine_id, shift_id, date_id)`, compute final `oee`, and carry `cycle_time_confidence` through to the output row exactly as Section 18 requires ("`performance` explicitly carries forward the `cycle_time_confidence` flag ... so any consumer can see when the number is built on a verified versus estimated input")
- Apply the edge-case handling decided in Task 5.1 explicitly in SQL (`CASE WHEN` guards, not implicit NULL propagation you haven't verified)

**Task 5.3 — Loss-attribution breakdown (the "loss tree" logic, scoped inside `oee_daily` per the flagged resolution above)**
- Add a CTE that joins `fct_downtime_event` to `dim_downtime_reason` and buckets `duration_sec` by `oee_loss_category` (Availability-loss vs. Performance-loss) per machine/shift/day
- Decide the output shape: either wide columns on `oee_daily` (`availability_loss_sec`, `performance_loss_sec`) or a separate lightweight model (`oee_loss_breakdown` or similar) that shares `oee_daily`'s grain and is joined at query time — document which you chose and why in the same ADR as Task 5.1's edge-case decisions
- Write the reconciliation logic: `SUM(availability_loss_sec) + SUM(performance_loss_sec)` per machine/shift/day should equal the total `duration_sec` from `fct_downtime_event` for that same grain, *minus* any rows where `reason_id` is null (unmapped free-text reasons can't be categorized yet — this is expected, not a bug, per the Source Data Contract's nullable-FK design principle) — the reconciliation test in Task 5.5 needs to account for this gap explicitly, not treat it as silent slippage

**Task 5.4 — dbt model contract on `oee_daily`**
- Write the `contracts:` block in the model's YAML: explicit column names, types, and `not_null` constraints on every column that must never be null (machine_id, shift_id, date_id, oee) versus columns that may legitimately be null (loss-attribution columns where downtime is unmapped)
- Confirm the contract fails CI loudly if a future schema change violates it — verify this the same way Week 1–4 verified other guarantees: deliberately break the contract on a throwaway branch and confirm the CI job fails, then revert without merging

**Task 5.5 — dbt unit tests: the week's highest-priority task**
- Create `tests/unit_tests/oee_daily/` (or the equivalent path your dbt project structure uses) and add a `unit_tests:` block covering, at minimum:
  - A "clean" case: known inputs produce a hand-calculated expected OEE
  - Zero planned/shift time
  - Zero `run_duration_sec` on one run within an otherwise normal shift
  - Zero `produced_units` on one run
  - `standard_cycle_time_sec` null
  - `cycle_time_confidence = 'unconfirmed'` (confirm the output still computes but the confidence flag correctly propagates)
  - A multi-run shift where Performance's roll-up weighting (decided in Task 5.1) is the thing actually being tested, not just the individual run formula
- Run `dbt test --select oee_daily` locally against the temporary/dev target and confirm every unit test passes before touching CI

**Task 5.6 — Singular tests and the loss-tree reconciliation test**
- Add a singular test asserting `0 <= oee <= 1` (and the same bound on each component individually) per Section 19's business-rule row
- Add a singular test asserting `good_units <= produced_units` is never violated at the Silver layer feeding this model (if not already covered in Week 3–4, add here since Gold depends on it)
- Add the loss-tree reconciliation singular test from Task 5.3, with the unmapped-reason gap treated explicitly (assert the *mapped* portion reconciles exactly, and separately assert the unmapped portion is within an expected small percentage — don't let an unbounded unmapped percentage pass silently)

**Task 5.7 — Manual spot-check against real or synthetic data**
- Run `dbt build --select oee_daily` against your dev target
- Pick three actual machine/shift/day rows and hand-verify the Availability/Performance/Quality/OEE numbers against the raw Silver rows they were built from — this is the "values sane on manual spot-check" success criterion from Section 33's Week 5 row, and it is a distinct check from the unit tests (unit tests prove the formula is internally consistent against mocked data; this proves the model actually wired real columns to the right formula inputs)

**Task 5.8 — Scaffold `scrap_root_cause_summary` (grain only, build deferred to Week 6)**
- Create the model file with its `SELECT` skeleton and a comment header stating its grain (machine/shift/product/defect-type, per Section 18) and its planned join path (`fct_qc_inspection` → `dim_defect_type`, `fct_production_run` for scrap-volume context)
- Do not build out the full aggregation logic or tests yet — this is intentionally left for Week 6's first task, so Week 5 stays focused on `oee_daily`

**Task 5.9 — Documentation**
- Update `docs/data_dictionary.md` with `oee_daily`'s full column list, each with its named metric owner (Section 24) and its formula in plain business language, not just SQL
- Write the ADR(s) from Tasks 5.1 and 5.3 (edge-case resolution, loss-attribution output shape) into `docs/adr/`
- If the naming/scope question flagged at the top of this document was resolved differently than this roadmap's default (i.e., you decided a genuine third "loss tree" mart was warranted), write that ADR explicitly before proceeding to Week 6

## 5. Deliverables
- `models/marts/gold/oee_daily.sql` with enforced dbt model contract
- Loss-attribution logic (wide columns or companion model, per your Task 5.3 decision) reconciling against total logged downtime
- Full dbt unit test suite for the OEE formula, covering every edge case in Task 5.3
- Singular tests: OEE bounds, quality bound, loss-tree reconciliation
- ADRs documenting the Task 5.1 edge-case resolutions and Task 5.3 output-shape decision
- `scrap_root_cause_summary` model file scaffolded (grain and join path only, not yet built)
- Updated `docs/data_dictionary.md`

## 6. Acceptance Criteria
- `dbt build --select oee_daily` succeeds with zero test failures, including every unit test in Task 5.5
- Model contract enforcement verified by a deliberate break-and-revert on a throwaway branch
- Three hand-picked rows manually verified correct against their Silver source data
- Loss-tree reconciliation test passes, with the unmapped-reason gap explicitly bounded rather than silently ignored
- Every edge case enumerated in Task 5.1 has a corresponding unit test and a documented resolution — no edge case is "handled" only implicitly by SQL behavior no one verified

## 7. Common Mistakes
- Writing the OEE formula once and treating it as done because it "looks right" on clean data — the entire point of this week is that clean-data correctness is not the risk; edge-case correctness is.
- Silently letting a `NULL` propagate through a division rather than explicitly deciding (and testing) what should happen — a `NULL` OEE that reaches Power BI or the API looks like a bug, not a documented decision, unless it was deliberately chosen and flagged.
- Choosing a Performance roll-up weighting (simple vs. duration-weighted average) without writing down why, then forgetting the choice was even made when a reviewer or a Week 8 ADR review asks about it.
- Building the full `scrap_root_cause_summary` mart this week "since I'm on a roll" — this quietly compresses two weeks of validation-heavy work into one and is exactly the kind of pace this project's own Section 33 timeline was built to avoid.
- Treating the loss-tree reconciliation test as a nice-to-have and skipping it because the unmapped-reason-code gap makes exact reconciliation slightly annoying to test — this is precisely the situation the Source Data Contract's Design Principle 5 anticipated, and the test should assert the *known-good* portion strictly while bounding the *known-gap* portion, not skip the whole check.
- Forgetting to actually open and read the Week 3 SCD2 ADR (Task 5.0) and instead assuming from memory which outcome applies — this is the same failure mode Week 4's "IAM audit" task existed to catch for credentials; here it's for dimension-join correctness.

## 8. Recommended Commit Strategy
1. `docs: confirm SCD2/DML resolution and its implication for Gold dimension joins`
2. `docs: add ADR for OEE edge-case handling and loss-attribution output shape`
3. `feat: add oee_daily Gold model (Availability/Performance/Quality)`
4. `feat: add loss-attribution breakdown to oee_daily`
5. `feat: add oee_daily model contract`
6. `test: add oee_daily dbt unit tests covering formula edge cases`
7. `test: add oee_daily singular tests including loss-tree reconciliation`
8. `chore: scaffold scrap_root_cause_summary grain (build deferred to Week 6)`
9. `docs: update data dictionary with oee_daily columns and metric ownership`

## 9. Estimated Difficulty
- **Technical difficulty:** High. This is the single most conceptually demanding week in the entire project — it's the model the blueprint's own risk register rates as the top platform-wide risk, and unit-testing a multi-grain roll-up formula correctly is a genuinely advanced dbt skill.
- **Time required:** A full week, and resist the temptation to compress it, per Section 2 above.
- **Learning curve:** High if this is your first time writing dbt `unit_tests:` blocks (as opposed to generic/singular tests) — budget real time to learn the syntax and mocked-input pattern before you're also trying to get the OEE math right at the same time.

## 10. End-of-Week Checklist
- [ ] Week 3 SCD2/DML ADR read and its implication for dimension joins confirmed in writing
- [ ] `oee_daily` built, contract-enforced, and passing all unit and singular tests
- [ ] Loss-attribution breakdown built and reconciling against total downtime (with the unmapped-reason gap explicitly bounded, not ignored)
- [ ] Three rows manually spot-checked against raw Silver data
- [ ] `scrap_root_cause_summary` scaffolded (not fully built)
- [ ] All edge-case and output-shape decisions written into ADRs
- [ ] Data dictionary updated with metric ownership per column
- [ ] All work committed in logical, separate commits

---

# WEEK 6 — Second Gold Mart, Production Airflow Orchestration & Automated Workflows

## 1. Weekly Goal
Finish the second Gold mart (`scrap_root_cause_summary`), then move the entire pipeline from manual, ad-hoc triggering to fully scheduled Airflow orchestration running inside GitHub Actions on a daily cron trigger, exactly as Section 10/25 specify. By the end of the week: both Gold marts are built and tested, the DAG dependency chain (`extract_* → validate_contracts → load_bronze_bigquery → dbt_run_silver → dbt_test_silver → {dbt_run_gold_oee, dbt_run_gold_scrap} → dbt_test_gold`) runs unattended on a schedule, failure alerting reaches you without you checking manually, and the production and CI environments remain fully isolated from each other.

## 2. Why This Week Comes Now
`scrap_root_cause_summary` belongs here rather than Week 5 for the pacing reason already stated. Orchestration belongs here — not earlier — because there is nothing meaningful to orchestrate until both Gold marts exist; scheduling a DAG that only produces Silver tables would mean rebuilding the DAG's downstream steps again once Gold existed anyway. Orchestration also has to come *before* Week 7's API work, because the API's whole reason for existing is to serve Gold tables that are refreshed on a real schedule, not tables you happened to build once by hand — an API demoed against manually-triggered data would misrepresent the platform's actual operating model (Section 6's Reliability target: ">95% of runs succeed without manual intervention").

## 3. Prerequisites
- Week 5 fully closed: `oee_daily` built, contract-enforced, tested, and spot-checked; loss-attribution reconciling.
- `ingestion_sa` and `api_sa` JSON keys exist and are already stored as GitHub Actions encrypted secrets (established in Week 1/4) — confirm they are still valid and haven't been rotated without updating the secret.
- The Slim CI workflow (`ci.yml`) from Week 4 is green and its dataset-per-PR teardown is verified working — this week adds a *second*, structurally different workflow file for the production schedule, and the two must not be confused or share state.
- A Slack workspace (or equivalent) where you can create an incoming webhook for failure alerts — set this up before Task 6.4, not during it.

## 4. Detailed Task Breakdown

**Task 6.1 — Build `scrap_root_cause_summary` (carried over from Week 5's scaffold)**
- Complete the model at machine/shift/product/defect-type grain: join `fct_qc_inspection` → `dim_defect_type`, and to `fct_production_run` for scrap-volume context (`produced_units - good_units`)
- Handle the nullable `defect_type_id` case explicitly (a QC pass record has no defect type — per the Source Data Contract, this is expected, not an error; decide whether these rows are excluded from the mart or included with a `defect_type = 'N/A - Pass'` style row, and document the choice)
- Handle the QC-vs-Production-Log "good units" tension named explicitly in the Source Data Contract's Design Principle 6: this mart is authoritative for defect-type root-cause detail, `oee_daily`'s Quality component is authoritative for the scrap-rate number itself — do not let this model silently recompute a competing scrap-rate figure that could someday disagree with `oee_daily`'s
- Apply the model contract, run `dbt build --select scrap_root_cause_summary`, verify against 2–3 hand-picked rows

**Task 6.2 — Tests for `scrap_root_cause_summary`**
- Generic tests: `not_null` on required FKs, `accepted_values` on `defect_category` (per Section 19's Silver-layer example, re-verify it's also enforced here where it matters for the dashboard filter)
- Singular test: aggregated defect counts per machine/product/day should not exceed `produced_units` for that same grain from `fct_production_run` — a sanity ceiling, not a hard business rule, so decide whether this is a warn-severity or error-severity test and document why

**Task 6.3 — Design the production DAG structure (on paper, before any YAML)**
- Re-draw Section 25's dependency graph in your own working notes, confirming task names map 1:1 to your actual dbt selectors and Python callables: `extract_production`, `extract_downtime`, `extract_qc` → `validate_contracts` → `load_bronze_bigquery` → `dbt_run_silver` → `dbt_test_silver` → (`dbt_run_gold_oee` → `dbt_test_gold`) and (`dbt_run_gold_scrap` → `dbt_test_gold`) running in parallel
- Confirm every task is genuinely idempotent (safe to rerun for the same date without duplicating rows) — this was already a design requirement from Bronze onward, but re-verify it holds all the way through Gold now that both marts exist, since a Gold rebuild depends on a `CREATE OR REPLACE TABLE AS SELECT`, which is idempotent by construction, but confirm nothing upstream of it isn't
- Decide retry policy per task: 3 retries with exponential backoff, per Section 25 — confirm this is configured at the Airflow task level, not left as Airflow's bare default

**Task 6.4 — Stand up Airflow inside a GitHub Actions runner (validation spike before full build-out)**
- This is a genuinely new pattern (Airflow standalone/`LocalExecutor` bootstrapped fresh inside a CI runner, running one DAG, then tearing down) — before wiring the real DAG, do a minimal spike: get *any* trivial two-task DAG to execute successfully end-to-end inside a scheduled GitHub Actions job, to de-risk the mechanics (Airflow DB init time, `LocalExecutor` behavior in an ephemeral container, log/artifact capture) separately from getting the *real* DAG's business logic correct
- Time this spike run start-to-finish and record the number — this is the input to the execution-time-limit risk check in Task 6.5, not a throwaway detail

**Task 6.5 — Validate the GitHub Actions execution-time constraint explicitly (flagged risk — do not skip)**
- GitHub Actions jobs have a maximum runtime per job (check the current documented limit for your plan, since these limits are the kind of platform detail that changes) — before assuming the daily DAG will comfortably fit, add up: Airflow bootstrap time (from Task 6.4's spike), three parallel extract tasks, Bronze load time, `dbt_run_silver` + `dbt_test_silver`, and the parallel Gold build+test branches
- At this project's data volume (low hundreds of rows/day, per Section 6), the total should be comfortably inside any GitHub Actions limit — but "should be" is not "confirmed to be": run the actual full DAG once manually-triggered (via `workflow_dispatch`, not yet the cron schedule) and record wall-clock time before trusting the schedule
- If the run is unexpectedly slow, profile which task dominates before optimizing blindly — a slow `dbt_test_silver` step and a slow Airflow bootstrap step have completely different fixes

**Task 6.6 — Write the production GitHub Actions cron workflow**
- Create a new workflow file (e.g., `.github/workflows/production-schedule.yml`), deliberately separate from `ci.yml` — do not extend the CI workflow with a schedule trigger, since the two have different secret scopes, different target projects, and different failure semantics
- `on: schedule: cron:` set to run before the next shift starts, per the Performance NFR (Section 6) — pick and justify the actual cron time against the factory's real shift schedule from `dim_shift`, not an arbitrary time
- Also add `on: workflow_dispatch:` so you retain the ability to manually trigger a production run for demo purposes without waiting for the schedule
- Authenticate this workflow using `ingestion_sa`'s GitHub Actions secret — explicitly *not* `ci_sa`, and explicitly targeting the production Sandbox project, not the CI-only project from Week 4 (this is the "environment isolation" requirement from this week's brief, and it's worth a dedicated verification step, not just careful naming)

**Task 6.7 — Verify environment isolation concretely, not just by inspection**
- After the first successful scheduled/dispatched production run, check the *production* project's BigQuery console and confirm the datasets updated
- Separately, check the *CI-only* project's BigQuery console and confirm nothing changed there — no orphaned `fplip_ci_pr_*`-style dataset was accidentally created by the production workflow
- Confirm the production workflow's secrets (`ingestion_sa` key) and the CI workflow's secrets (`ci_sa` key) are stored as clearly and distinctly named GitHub repository secrets, so a future edit to one workflow can't accidentally reference the other's credential by a copy-paste mistake

**Task 6.8 — Failure alerting**
- Create a Slack incoming webhook, store its URL as a GitHub Actions encrypted secret
- Configure Airflow's `on_failure_callback` (or, if that proves awkward inside the standalone/ephemeral runner pattern, a workflow-level `if: failure()` step posting to the same webhook — decide which is more reliable in your actual setup and document why) to post a message on any task failure, including which task failed and a link back to the run's logs
- **Deliberately break the pipeline on purpose** — e.g., temporarily point `load_bronze_bigquery` at a nonexistent dataset on a throwaway branch/manual dispatch — and confirm a Slack alert actually arrives before reverting. This is the same "watch it fail on purpose" discipline every prior checkpoint in this project has required, and it's the single most important test in this task, more important than the alert's message formatting.

**Task 6.9 — Logging**
- Confirm structured (JSON) logs exist at every DAG stage per Section 22: row counts in/out, `_ingested_at` timestamps, contract-validation results — verify a failure is actually diagnosable from the GitHub Actions run's logs/artifacts alone, without needing to reproduce locally, by picking one real (or deliberately induced) failure and trying to diagnose it purely from the CI-run artifact

**Task 6.10 — Documentation**
- Update `docs/architecture.md` with the finalized production DAG diagram and the two-workflow (CI vs. production-schedule) GitHub Actions topology
- Write an ADR for the cron schedule time decision (Task 6.6) and for the alerting mechanism decision (Task 6.8)
- Update the data dictionary with `scrap_root_cause_summary`'s columns and metric ownership

## 5. Deliverables
- `scrap_root_cause_summary` Gold model, tested and contract-enforced
- A validated, timed Airflow spike proving the standalone-in-GitHub-Actions pattern works
- Full production DAG matching Section 25's dependency graph, with documented idempotency and retry configuration
- `.github/workflows/production-schedule.yml`, separate from CI, using `ingestion_sa` against the production project only
- Confirmed, tested environment isolation between production and CI projects
- Working Slack failure alerting, verified via a deliberate break
- Updated `docs/architecture.md` and ADRs for schedule timing and alerting mechanism

## 6. Acceptance Criteria
- `scrap_root_cause_summary` passes all tests, contract enforcement verified
- A manually-dispatched full production DAG run completes successfully end-to-end within a documented, measured wall-clock time
- The scheduled cron trigger fires and completes successfully at least once, unattended
- A deliberately broken run produces a Slack alert that actually arrives
- Production and CI datasets independently confirmed isolated from each other after a real run
- Every task in the DAG confirmed idempotent (a rerun for the same date does not duplicate rows — verify this concretely by triggering the DAG twice for the same date and checking row counts, not just asserting it by design)

## 7. Common Mistakes
- Reusing the CI workflow's schedule/secrets for production instead of building a genuinely separate workflow — this is the single most likely way to accidentally cross-contaminate the CI-only and production projects.
- Assuming the GitHub Actions time limit "obviously" isn't a problem at this data volume and never actually timing a real run — the risk section of this brief calls this out explicitly for a reason; a bootstrap-heavy pattern like Airflow-inside-an-ephemeral-runner can surprise you even at low data volume.
- Configuring `on_failure_callback` and never actually testing it — an alerting mechanism that has never fired is unverified, not working.
- Skipping the idempotency re-verification at the DAG level because each individual task was already idempotent in isolation back in Weeks 2–4 — composition isn't automatically idempotent just because each part is; verify the whole chain.
- Leaving the manually-dispatched Week 6 testing runs as the only evidence the schedule works, without ever confirming the actual `cron:` trigger fires on its own.

## 8. Recommended Commit Strategy
1. `feat: complete scrap_root_cause_summary Gold model`
2. `test: add scrap_root_cause_summary generic and singular tests`
3. `chore: add Airflow-in-GitHub-Actions validation spike`
4. `feat: add production DAG matching Section 25 dependency graph`
5. `ci: add production-schedule.yml workflow with ingestion_sa auth`
6. `feat: add Slack failure alerting via on_failure_callback`
7. `test: verify environment isolation and idempotency via deliberate reruns`
8. `docs: update architecture.md with production DAG and two-workflow topology; add ADRs`

## 9. Estimated Difficulty
- **Technical difficulty:** High. Bootstrapping Airflow fresh inside an ephemeral CI runner on a schedule is a genuinely uncommon pattern outside this project's specific zero-cost constraint, and the timing/isolation verification work is easy to underestimate.
- **Time required:** A full week, with real risk of the Airflow-in-GitHub-Actions spike alone eating 1–2 days if it doesn't work smoothly on the first attempt — budget for that possibility rather than assuming it goes cleanly.
- **Learning curve:** Moderate-High if this is your first time running Airflow outside a persistent host.

## 10. End-of-Week Checklist
- [ ] `scrap_root_cause_summary` built, tested, contract-enforced
- [ ] Airflow-in-GitHub-Actions spike validated and timed
- [ ] Full production DAG built matching Section 25's graph
- [ ] Production schedule workflow live, separate from CI workflow, using correct service account and project
- [ ] Environment isolation concretely verified (not just assumed)
- [ ] Idempotency verified via an actual same-date rerun test
- [ ] Slack alert tested via a deliberate failure
- [ ] Architecture docs and ADRs updated
- [ ] All work committed in logical, separate commits

---

# WEEK 7 — FastAPI Serving Layer & Secure BigQuery Access

## 1. Weekly Goal
Build the read-only FastAPI service (`/health`, `/oee/daily`, `/oee/summary`, `/scrap/root-cause`) against `fplip_gold`, authenticated via `api_sa` and a single API key header, with query optimization, caching, and error handling in place — and deploy/test it locally via Docker. By the end of the week, the API is a working "last mile" demonstration layer, explicitly scoped and defended as exactly that (Section 27), not oversold as a production integration surface.

## 2. Why This Week Comes Now
The API cannot be meaningfully built or tested before Gold marts exist and are refreshed on a real schedule (Weeks 5–6) — an API demoed against stale, manually-populated tables would misrepresent what it actually does. It comes before Week 8 because Week 8's cold-restart integration test and final demo need every layer of the stack, including the API, already working and stable; Week 8 has no room in it to also be debugging API code for the first time.

## 3. Prerequisites
- Both Gold marts (`oee_daily`, `scrap_root_cause_summary`) built, tested, and refreshing on the Week 6 production schedule.
- `api_sa`'s JSON key exists (provisioned in Week 1), scoped to `BigQuery Data Viewer` + `BigQuery Job User` on `fplip_gold` only (Section 23) — confirm this scoping is still exactly what's applied, not broadened at some point for convenience during earlier debugging.
- Docker and Docker Compose available locally (already a Week 1 prerequisite).
- A stable API key value generated and ready to use (not yet decided how it's stored — that's part of this week's task).

## 4. Detailed Task Breakdown

**Task 7.1 — Confirm `api_sa` scoping before writing any application code**
- In the GCP console (or via `gcloud`), directly inspect `api_sa`'s IAM bindings and confirm: `BigQuery Data Viewer` on `fplip_gold` specifically (not project-wide, not on `fplip_bronze`/`fplip_silver`), plus the project-level `BigQuery Job User` binding required for query execution (per the Week 1 note that this is a genuine BigQuery IAM nuance, easy to forget exists at all)
- If scoping has drifted from this at any point, correct it via Terraform (not a manual console click) and re-`apply` before proceeding

**Task 7.2 — Application structure**
- Scaffold `api/` with a conventional FastAPI layout: `main.py`, `routers/`, `schemas/`, `dependencies/`, `core/config.py`
- Configure the BigQuery Python client inside a dependency (not instantiated per-request) so the client and its credentials are set up once at app startup, not repeatedly

**Task 7.3 — Credential handling (flagged risk — service-account key leakage)**
- Load `api_sa`'s key from an environment variable pointing to a file path (`GOOGLE_APPLICATION_CREDENTIALS`) or from the key's JSON content directly via an env var — never hardcode the key path or contents into any file that gets committed
- Confirm `.dockerignore` excludes any local key file the same way `.gitignore` already does, so a `docker build` run from a directory containing the key doesn't accidentally bake it into an image layer
- For local development, mount the key file into the container via Docker Compose volume mount, not `COPY` in the Dockerfile — a `COPY`'d secret persists in every image layer even if a later step deletes it
- Decide and document how the API key (the app-level auth header, distinct from `api_sa`'s GCP credentials) is generated, stored, and rotated — a single static value is acceptable at this project's scale per Section 27, but the decision should be explicit, not accidental

**Task 7.4 — `/health` endpoint**
- Build a minimal endpoint that confirms the app is running and, separately, that it can successfully reach BigQuery with `api_sa`'s credentials (a lightweight query like a dry-run or a trivial `SELECT 1`) — distinguish "app is up" from "app can reach its dependency," since these fail for different reasons and a good health check should say which one broke

**Task 7.5 — `/oee/daily`, `/oee/summary`, `/scrap/root-cause` endpoints**
- Define request schemas (query params: date range, machine filter, at minimum) and response schemas (Pydantic models matching `oee_daily`'s and `scrap_root_cause_summary`'s actual contracted columns — derive these schemas directly from the dbt model contracts written in Weeks 5–6, don't redefine the shape from scratch and risk drift)
- Write parameterized BigQuery queries (never string-concatenated user input directly into SQL — use the BigQuery client's query-parameter mechanism) selecting only the columns each endpoint actually needs, filtered by the request's date range/machine params
- `/oee/summary` should be a genuinely different query shape from `/oee/daily` (an aggregate over a range, not a row-per-day list) — confirm this distinction is real in your implementation, not two endpoints doing the same query with different names

**Task 7.6 — Query optimization**
- Ensure every query filters on `oee_daily`/`scrap_root_cause_summary`'s clustering keys (per Section 12, Gold tables are clustered on filter/join keys) — confirm via `EXPLAIN`/query-plan inspection that filters are actually pruning partitions/clusters, not doing a full scan every request
- Avoid `SELECT *` anywhere in the API layer — select only contracted columns the response schema actually exposes

**Task 7.7 — Caching**
- Add a lightweight in-memory response cache (a simple TTL cache is sufficient at this data volume and single-instance deployment — do not reach for Redis, which the blueprint's Section 4/38 already explicitly rejected as unjustified at this scale) keyed on the endpoint + query params, with a TTL shorter than the daily refresh cadence (e.g., a few hours) so cached responses can never be staler than "since the last scheduled Gold refresh" by more than a bounded, documented amount
- Document the TTL choice and why it's safe given the pipeline only refreshes once daily

**Task 7.8 — Error handling and async correctness (flagged risk — synchronous long-running queries blocking the API)**
- Wrap BigQuery calls with explicit timeouts and translate BigQuery client exceptions into proper HTTP error responses (4xx for bad params, 5xx for genuine backend failures) — never let a raw BigQuery exception or stack trace leak into an API response
- Confirm BigQuery calls are made in a way that doesn't block the FastAPI event loop for the whole request lifecycle under load — either via FastAPI's `run_in_threadpool` pattern for the synchronous BigQuery client, or by using it correctly within an `async def` endpoint; verify which your actual client usage requires, since getting this wrong is a common, subtle source of the "long query blocks other requests" failure mode named in this week's brief

**Task 7.9 — Validate real-world query latency before considering this week done (flagged risk)**
- Run each endpoint against the live `fplip_gold` dataset and record actual response times, both cache-cold and cache-warm
- If cache-cold latency is uncomfortably high for a demo (e.g., multiple seconds), diagnose whether it's query-plan inefficiency (revisit Task 7.6) or simply BigQuery's inherent per-query startup overhead at this tiny data volume (likely, and not really fixable, only maskable via caching) — document which it is rather than guessing
- This validation must happen before declaring the week done — a functioning-but-unmeasured API is not the same as a validated one, per this week's own instruction to schedule validation for exactly this kind of risk

**Task 7.10 — Docker deployment and local testing**
- Write/confirm `api/Dockerfile` and the relevant `docker-compose.yml` service definition
- `docker compose up` the API service locally, confirm all four endpoints work end-to-end against the real (or a test) `fplip_gold` dataset, using the mounted credential file from Task 7.3, not a locally-installed personal `gcloud` session
- Write a minimal `tests/integration/test_api.py` (or equivalent) exercising each endpoint against a live or test dataset, run as part of local validation (full CI wiring for this is optional at this project's scope but is worth at least a manual pass here)

**Task 7.11 — Documentation**
- Confirm FastAPI's auto-generated docs (`/docs`) render correctly and accurately reflect the real request/response schemas
- Update `docs/architecture.md` with the API's position in the overall data flow (Section 9's diagram already shows this at a high level — add the API-specific detail: auth model, caching, `api_sa` scoping)
- Write an ADR for the caching TTL decision and for how the app-level API key is stored/rotated

## 5. Deliverables
- Working FastAPI app (`main.py`, routers, schemas, dependencies) with all four endpoints
- Verified `api_sa` IAM scoping (Data Viewer + Job User on `fplip_gold` only)
- Credential handling that never bakes a key into a Docker image or a git commit
- In-memory response caching with a documented, safe TTL
- Documented, measured query latency for every endpoint
- `docker-compose` service definition, tested working locally
- Integration tests exercising all endpoints
- Updated architecture docs and new ADRs (caching TTL, API key storage)

## 6. Acceptance Criteria
- All four endpoints return correct, contract-matching data when tested against the live `fplip_gold` dataset via `docker compose up`
- `api_sa`'s IAM scope independently verified in the GCP console, not just assumed from Terraform code
- No service-account key or API key appears in any committed file or Docker image layer — verified by actually inspecting a built image's layers, not just trusting the Dockerfile's intent
- Cache-cold and cache-warm latency both measured and documented for every endpoint
- A deliberately malformed request (bad date range, missing API key) returns a proper 4xx response, not a raw exception or a 500

## 7. Common Mistakes
- Embedding the service-account key directly in API source code or a committed config file — explicitly called out as a common mistake in this week's brief, and worth treating as a hard blocker to catch via the layer-inspection check in the acceptance criteria, not just code review by eye.
- Running long BigQuery queries synchronously inside an `async def` endpoint without offloading to a thread pool, silently serializing all API requests under any real concurrent load.
- Skipping the cache TTL decision and either caching forever (serving stale data past the next Gold refresh) or not caching at all (paying full BigQuery latency on every request for no benefit, given the data only changes once daily).
- Forgetting to clean up any BigQuery Sandbox test datasets created while iterating on integration tests during this week — a small but real hygiene item explicitly named in this week's brief; don't let scratch datasets accumulate silently in the CI or dev project.
- Testing only the happy path and never actually sending a malformed request to confirm error handling behaves as documented.

## 8. Recommended Commit Strategy
1. `chore: verify and document api_sa IAM scoping`
2. `feat: scaffold FastAPI app structure and BigQuery client dependency`
3. `security: add credential handling via env-mounted key, exclude from Docker image`
4. `feat: add /health endpoint with BigQuery connectivity check`
5. `feat: add /oee/daily and /oee/summary endpoints`
6. `feat: add /scrap/root-cause endpoint`
7. `perf: add query optimization (clustering-key filters, column pruning)`
8. `perf: add in-memory TTL response caching`
9. `fix: add async-safe BigQuery calls and structured error handling`
10. `test: add API integration tests and record measured latency`
11. `docs: add Docker Compose service, update architecture.md, add ADRs`

## 9. Estimated Difficulty
- **Technical difficulty:** Medium. FastAPI itself is likely familiar territory; the specific risks here (async/sync BigQuery client interaction, credential hygiene inside Docker) are narrow but easy to get subtly wrong.
- **Time required:** A full week, with the latency validation and credential-hygiene verification (Tasks 7.3, 7.9) deserving real time, not a rushed final-day check.
- **Learning curve:** Low-Moderate if FastAPI and Docker are already familiar; Moderate if the BigQuery Python client's sync/async behavior is new.

## 10. End-of-Week Checklist
- [ ] All four endpoints implemented and returning correct, contract-matching data
- [ ] `api_sa` IAM scoping independently verified
- [ ] No credential or key present in any committed file or built Docker image layer (actually checked, not assumed)
- [ ] Caching implemented with a documented TTL
- [ ] Latency measured (cache-cold and cache-warm) and documented for every endpoint
- [ ] Error handling verified against a deliberately malformed request
- [ ] `docker compose up` runs the full API locally against live Gold data
- [ ] Integration tests passing
- [ ] Architecture docs and ADRs updated
- [ ] All work committed in logical, separate commits

---

# WEEK 8 — End-to-End Validation, Portfolio Packaging & Documentation

## 1. Weekly Goal
Prove the entire platform works from nothing — a genuine cold-restart integration test — and package the repository, documentation, and demo so a stranger (a recruiter, an interviewer, a senior engineer doing a code review) can understand and verify the platform's claims without needing you in the room. By the end of the week: a full cold-restart system test has passed, README/ADRs/data lineage are complete and internally consistent, and at least one verified, quantified business-impact number exists, per Section 3's Objective 3.

## 2. Why This Week Comes Now
Every other week's work is a prerequisite for this one — there is nothing to validate end-to-end, document accurately, or demo convincingly until Gold marts, orchestration, and the API all exist and work (Weeks 5–7). This week is deliberately last because portfolio packaging done *before* the platform is fully stable produces documentation that immediately drifts out of sync with the real system — exactly the kind of internal-inconsistency failure mode Section 24's governance principle exists to prevent, applied here to the project's own README rather than to a data contract.

## 3. Prerequisites
- Weeks 5–7 fully closed: both Gold marts built and tested, production DAG running on schedule with verified alerting, API deployed and its endpoints validated for correctness and latency.
- Access to a way to either (a) provision a genuinely fresh third GCP Sandbox project for the cold-restart test, isolated from both the production and CI-only projects, or (b) fully tear down and rebuild the existing production project's BigQuery datasets from scratch — decide which before starting Task 8.1, since it changes what "cold" actually means for this test.
- A stable, current business-impact hypothesis in mind (e.g., current unmeasured scrap cost, or current manual time-to-insight) from Section 3's Objective 3 — if this hasn't been discussed with anyone at the factory yet, that conversation needs to happen early this week, not on the last day.

## 4. Detailed Task Breakdown

**Task 8.1 — Design the cold-restart test precisely before running it**
- Write down exactly what "cold" means for this test: empty Bronze/Silver/Gold datasets (or a genuinely new project), no locally-cached dbt state, no manually-run setup steps outside what's actually documented in the README
- Decide the success definition in advance, in writing: what specific commands, in what order, starting from a fresh `git clone`, must succeed for the test to pass — this becomes the literal script a stranger would follow, and writing it before running it is what makes the test honest rather than something you retroactively narrate as having gone well

**Task 8.2 — Execute the cold-restart test**
- From the fresh state defined in Task 8.1: `terraform apply` (against the fresh/reset project), run the synthetic data generator or point at real source files, manually trigger the production DAG via `workflow_dispatch`, confirm Bronze → Silver → Gold populate correctly and all tests pass at every layer, then start the API via `docker compose up` and hit all four endpoints against the freshly-populated Gold tables
- Time the entire process start to finish
- Record every deviation from what the README currently says, however small — this task's output is as much "a list of documentation bugs" as it is "confirmation the system works"

**Task 8.3 — Fix documentation gaps found in Task 8.2**
- Go through the deviation list from Task 8.2 and correct the README/setup docs for each one — do not defer this, since an undocumented manual step is exactly the kind of thing that silently breaks the "stranger can run this in 15 minutes" success criterion from Section 33's Week 8 row

**Task 8.4 — Data lineage diagrams**
- Generate `dbt docs generate` and confirm the lineage graph renders correctly and completely across Bronze → Silver → Gold, including the loss-attribution logic from Week 5 and both Gold marts
- Decide how this is hosted/shared for a reviewer who can't run `dbt docs serve` themselves — a static export, screenshots embedded in `docs/architecture.md`, or a hosted docs site, per the Section 32/Future Improvements note about `dbt docs` being the chosen governance mechanism at this project's scale
- Build the third architecture diagram named explicitly in Section 36 — GCP resource topology (one project, three BigQuery datasets, two service accounts, IAM-role arrows not credential arrows, explicit annotation that no billing account is linked) — and place it as the first visual in the README, ahead of any code block, exactly as Section 36 specifies

**Task 8.5 — README and Architecture Decision Records**
- Write/finalize the top-level `README.md`: problem statement (Section 2), architecture diagram (Task 8.4's third diagram, first), quickstart matching the corrected Task 8.3 steps, link to `docs/architecture.md`, `docs/data_dictionary.md`, `docs/runbook.md`, and the ADR log
- Review every ADR written across all eight weeks (grain definition, warehouse choice, storage choice, auth model, the Section 13/23 constraint-driven trade-offs, the Week 3 SCD2/DML resolution, the Week 5 edge-case and loss-attribution decisions, the Week 6 schedule/alerting decisions, the Week 7 caching/key-storage decisions) together, in one sitting, for internal consistency — check specifically for any ADR that contradicts a later one without an explicit superseding note, the same review discipline the Weeks 1–4 plan already applied once at its own Week 4 close

**Task 8.6 — `docs/runbook.md`**
- Write the operational runbook: what to do when the daily pipeline fails (how to read the Slack alert, where to find logs, how to manually re-trigger), how to rotate `ingestion_sa`/`api_sa` keys, how to recover if the 60-day table auto-expiration window is ever actually hit (Section 12's documented one-command recovery), and how to add a new downtime reason code or defect type without breaking the loss-attribution mapping

**Task 8.7 — Verified, quantified business-impact number (Objective 3)**
- Using either real factory data (if access has materialized by now) or a clearly-labeled synthetic-but-realistic estimate, produce one specific, defensible number: e.g., "current manual reconciliation to produce a comparable OEE figure takes approximately N hours/week; this platform produces it daily, unattended" or a scrap-cost figure derived from `scrap_root_cause_summary`'s actual output
- State explicitly, in the documentation, whether this number is verified against real factory data or is a synthetic-data-based estimate — per the same honesty principle Section 8 applies to `cycle_time_confidence`, an unlabeled number presented as fact is the exact failure mode this project has avoided everywhere else; don't let the one number meant to prove the platform's value be the place that principle slips

**Task 8.8 — Recorded demo (fallback path)**
- Record a walkthrough demo covering: the problem (Section 2), the architecture diagram, a live (or recently-run) pipeline execution, the Power BI dashboard, and the API's `/docs` page — this is the documented fallback for a reviewer who wants zero GCP account involvement at all, per Section 33's Week 8 success criteria ("watch the recorded demo with zero account at all")
- Keep it tight and specific to what a hiring manager or interviewer actually needs to see, not a full feature tour

**Task 8.9 — Final repository polish**
- Confirm every directory has a purpose a stranger could infer from its name plus one line of README explanation (Section 6's Maintainability NFR: "a new contributor can locate and modify any layer within 10 minutes")
- Remove any leftover scratch files, temporary branches, or dead code paths accumulated across eight weeks
- Final check: no committed secrets anywhere in git history, not just the current working tree — run a secret-scanning check across the full history, not just `HEAD`, since a key committed and later removed in a subsequent commit is still present in history unless it was actively purged

**Task 8.10 — Final review against the frozen blueprint**
- Walk Section 4's in-scope/out-of-scope list one more time and confirm the finished repository matches it exactly — no scope crept in silently across eight weeks that was never given its own ADR (the Week 5 naming/scope flag at the top of this document is the kind of thing this final check exists to catch if it happened again anywhere else)
- Confirm every functional requirement in Section 5 (FR-01 through FR-11) has a traceable implementation and, ideally, a one-line pointer to where in the repo it's satisfied — useful both for your own final defense and for a technical interviewer probing requirement-by-requirement

## 5. Deliverables
- A completed, timed, documented cold-restart integration test
- Corrected README/setup documentation reflecting the real, verified steps
- Full `dbt docs` lineage graph, hosted or exported for reviewer access
- The third architecture diagram (GCP resource topology) as the README's first visual
- Complete `docs/architecture.md`, `docs/data_dictionary.md`, `docs/runbook.md`, and a reviewed, internally-consistent ADR log
- One verified-or-clearly-labeled quantified business-impact statement
- A recorded demo video
- A final, polished, secret-free repository, traced against Section 4/5 for scope and requirement completeness

## 6. Acceptance Criteria
- A stranger (or you, simulating one, following only the README with no prior context) can clone the repo and run the live demo against their own free BigQuery Sandbox project in under 15 minutes, per Section 33's Week 8 success criterion — or, failing that, the recorded demo stands as a complete, honest fallback
- Cold-restart test passed and its actual timing documented
- Every ADR reviewed together with no unresolved contradiction
- The business-impact number is explicitly labeled verified or estimated — never presented ambiguously
- A full-history secret scan comes back clean
- Every Section 5 functional requirement has a traceable pointer in the finished repo

## 7. Common Mistakes
- Treating "the pipeline has worked before" as equivalent to a cold-restart test — prior successful runs prove nothing about whether an undocumented manual step is hiding in your own muscle memory.
- Writing documentation from memory of how the system is supposed to work rather than from actually re-running the steps and recording what really happened.
- Presenting a synthetic-data-derived business-impact number without labeling it as such — the exact failure mode `cycle_time_confidence` exists elsewhere in this platform to prevent, recreated here if skipped.
- Scanning only the current working tree for committed secrets and missing a key that was committed and later deleted but still lives in git history.
- Letting scope quietly expand in Week 8 itself — e.g., adding "just one more" dashboard chart or endpoint during final polish — without the same ADR discipline applied to every other change across the project.

## 8. Recommended Commit Strategy
1. `chore: define and execute cold-restart integration test`
2. `docs: correct README and setup steps found inaccurate during cold-restart test`
3. `docs: add hosted dbt docs lineage export and GCP resource topology diagram`
4. `docs: finalize architecture.md, data_dictionary.md, runbook.md`
5. `docs: review all ADRs for internal consistency`
6. `docs: add verified/estimated business-impact statement`
7. `chore: full-history secret scan and final repository cleanup`
8. `docs: add Section 4/5 scope and requirement traceability check`
9. `docs: add recorded demo link to README`

## 9. Estimated Difficulty
- **Technical difficulty:** Low-Medium technically, but High in rigor — nothing here is conceptually new, but doing the cold-restart test honestly (rather than as a formality) and reviewing eight weeks of ADRs for real consistency both take real discipline.
- **Time required:** A full week — the cold-restart test and documentation-fixing loop (Tasks 8.1–8.3) alone can easily consume 2–3 days if the gap list from Task 8.2 turns out to be long, which is common and not a sign anything went wrong earlier.
- **Learning curve:** Low. This week is mostly execution and writing, not new technical territory.

## 10. End-of-Week Checklist
- [ ] Cold-restart test executed, timed, and documented
- [ ] README and setup docs corrected to match the actual verified steps
- [ ] `dbt docs` lineage accessible to a reviewer
- [ ] GCP resource topology diagram is the README's first visual
- [ ] `docs/architecture.md`, `docs/data_dictionary.md`, `docs/runbook.md` complete
- [ ] All ADRs reviewed together, no unresolved contradictions
- [ ] Business-impact number produced and explicitly labeled verified/estimated
- [ ] Recorded demo complete
- [ ] Full-history secret scan clean
- [ ] Section 4/5 scope and requirement traceability confirmed
- [ ] All work committed in logical, separate commits

---

## End of Gold Layer, Orchestration, Serving & Portfolio Phase

At the close of Week 8: a fully governed two-mart Gold layer (`oee_daily` with tested, edge-case-hardened OEE formulas and downtime loss attribution; `scrap_root_cause_summary`) refreshing daily via unattended, alerted Airflow orchestration inside GitHub Actions; a working, latency-validated, credential-safe FastAPI serving layer; and a repository whose documentation has been proven accurate by an actual cold restart rather than assumed accurate from memory — with one verified, honestly-labeled business-impact number as the platform's evidence of real value, per Section 3's Objective 3.

This closes the full 8-week roadmap against Blueprint v3.0's own Section 33 timeline. Anything beyond this point — the Phase 2 energy mart, or the Section 32 future-improvements items (multi-factory `factory_id`, real-time triggers, a data catalog, ML-driven predictive maintenance) — is explicitly out of scope for this roadmap and, per Section 32's own framing, should only be pursued once a stated scale threshold is actually crossed, not pursued as unscoped extra polish before a defense or interview.
