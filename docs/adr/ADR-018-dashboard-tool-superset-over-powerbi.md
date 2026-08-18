# ADR-017: Dashboard Tool — Superset over Power BI

## Status
Accepted (2026-08-12)

## Context
The frozen blueprint (Section 28) specified Power BI as the dashboard/visualization layer for FPLIP. During execution, this decision was re-evaluated.

## Decision
Use **Apache Superset** (self-hosted, open-source BI) instead of Power BI.

## Reasoning

1. **Reproducibility:** Superset runs entirely via Docker Compose with zero external dependencies. Power BI requires a Microsoft account, licensing, and a Windows-only desktop application — which a professor or recruiter cloning this repo may not have.

2. **Zero Cost:** Superset is free and open-source. Power BI Pro is a paid service.

3. **Containerized Portfolio Artifact:** The dashboard export, screenshots, and configuration are all versioned in the repository alongside the rest of the project. A Power BI `.pbix` file would require a separate Microsoft ecosystem to even open.

4. **Skill Demonstration:** Building a self-hosted BI layer demonstrates additional engineering capability (Docker, BI tool administration, data source configuration) beyond just connecting to a managed service.

## Tradeoffs

| Aspect | Superset | Power BI |
|--------|----------|----------|
| Cost | Free | Paid (Pro license required for sharing) |
| Portability | Docker container | Windows-only desktop app |
| Repository Integration | Exportable JSON | `.pbix` file |
| Learning Curve | Moderate | Steep (DAX, M, etc.) |
| Authentication | Basic (admin) | Azure AD integration |

## Implementation Notes

- Superset installed via Docker Compose using the official pre-built images
- Connected to `fplip_gold` using `api_sa`'s existing read-only credentials
- Dashboard structured in 4 rows: KPIs → OEE → Loss Attribution → Scrap
- 3 global filters: date range, machine, product
- Dashboard exported and committed to the repository

## Verification
- All 9 charts built and verified against real data
- Dashboard filters confirmed working
- Export tested and re-importable

## Date
2026-08-12

## Supersedes
- Section 28 of the frozen blueprint (Power BI requirement)