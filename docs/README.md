# FPLIP Technical Documentation Hub

Welcome to the central documentation index for the **Factory Performance & Loss Intelligence Platform (FPLIP)**.

---

## Documentation Categories

### 🏛️ 1. Architecture & Design Specifications
- **[System Architecture](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/architecture/architecture.md)** — High-level architecture, pipeline design, data model topology, and component integration.
- **[GCP Topology](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/architecture/gcp-topology.md)** — Google Cloud BigQuery dataset structure, IAM roles, and storage configuration.
- **[API Endpoint Latency](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/architecture/Endpoint_latency.md)** — Benchmark metrics and performance analysis of FastAPI endpoints.
- **[Business Impact](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/architecture/business-impact.md)** — Value proposition, ROI calculation, and manufacturing operational impact.
- **[Scope Traceability Matrix](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/architecture/scope-traceability.md)** — Requirements mapping to implemented system features.

---

### 📜 2. Architectural Decision Records (ADRs)
Browse architectural decisions made throughout the engineering lifecycle:
- [ADR-001: Data Warehouse Selection](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/adr/ADR-001-warehouse-selection.md)
- [ADR-002: Idempotent Bronze Ingestion Design](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/adr/ADR-002-idempotent-bronze-loading.md)
- [ADR-003: SCD2 DML & Sandbox Handling](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/adr/ADR-003-scd2-blocked-by-sandbox-dml.md)
- [ADR-004: History Tracking Pattern](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/adr/ADR-004-history-tracking-implementation.md)
- [ADR-005: Consistency Review](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/adr/ADR-005-week3-consistency-review.md)
- [ADR-006: Fact Grain Validation](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/adr/ADR-006-fact-grain-validation.md)
- [ADR-007: Gold Dimension Join Pattern](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/adr/ADR-007-gold-dimension-join-pattern.md)
- [ADR-008: OEE Edge Case Handling](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/adr/ADR-008-oee-edge-case-handling.md)
- [ADR-009: Data Quality Findings & Verification](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/adr/ADR-009-data-quality-findings.md)
- [ADR-010: Loss Attribution Output Schema](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/adr/ADR-010-loss-attribution-output-shape.md)
- [ADR-011: Airflow DAG Architecture](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/adr/ADR-011-week6-dag-design.md)
- [ADR-012: Production Schedule Integration](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/adr/ADR-012-production-schedule.md)
- [ADR-013: Airflow LocalExecutor Choice](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/adr/ADR-013-airflow-executor-choice.md)
- [ADR-014: Alerting & Metric Splitting](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/adr/ADR-014-alerting-split.md)
- [ADR-015: API Key Management & Security](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/adr/ADR-015-api-key-storage.md)
- [ADR-016: Response Caching TTL Strategy](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/adr/ADR-016-caching-ttl.md)
- [ADR-017: Foundation Phase Sign-off](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/adr/ADR-017-foundation-phase-complete.md)
- [ADR-018: BI Tooling — Apache Superset Choice](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/adr/ADR-018-dashboard-tool-superset-over-powerbi.md)

---

### 📊 3. Data Warehouse Schema & Contracts
- **[Data Dictionary](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/data-dictionary/data_dictionary.md)** — Detailed schema definitions for Bronze, Silver, and Gold BigQuery tables.

---

### 🛠️ 4. Runbooks & Testing Protocols
- **[Operational Runbook](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/runbooks/runbook.md)** — Step-by-step instructions for operating and maintaining the system.
- **[Cold Restart Test Plan](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/runbooks/cold_restart_test_plan.md)** — Disaster recovery and cold-start verification procedure.
- **[Cold Restart Test Results](file:///c:/Users/kheza/Downloads/project%20zip/project%20zip/docs/runbooks/cold_restart_test_results.md)** — Empirical verification report of system initialization test.
