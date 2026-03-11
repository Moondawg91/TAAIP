# TAAIP Architecture Reference

This document is the canonical architecture reference for TAAIP. It defines page responsibilities, key data sources, authoritative tables, API endpoints, and organizational mapping rules so the codebase remains aligned as features are added.

---

## Core Data Model

### Fact Tables
- `fact_mission_production`
- `fact_funnel_daily`
- `fact_tne_pne`
- `fact_dep_loss`
- `fact_school_contacts`
- `fact_school_population`
- `fact_school_zone_targeting`

### Dimension Tables
- `dim_unit`
- `dim_school`
- `dim_recruiter`
- `dim_time`

---

## API Scope Parameters (Standard)

All analytics endpoints MUST accept these standard scope parameters. Endpoints should treat these as optional but honor them when provided.

- `unit_rsid`
- `fy`
- `qtr_num`
- `rsm_month`

Example:

GET /api/v2/mission-feasibility/summary?unit_rsid=6L&fy=2026&rsm_month=2026-03

---

## Organizational Mapping Rule

Unit codes MUST resolve to canonical org nodes. Battalion-level codes must be treated as battalion nodes, not brigade scope.

Example:

`6L` → Seattle Recruiting Battalion (battalion node under 6th Brigade). The system must never treat `6L` as equivalent to the 6th Brigade.

Importers, filters, and assignment writes must use the canonical `unit_rsid` produced by the org resolver.

---

# Page-by-Page Architecture (Detailed)

Below is the definitive mapping for each major page in TAAIP. Use this as the design contract when adding features or endpoints.

## Command Center — Recruiting Operations

- Purpose: Real-time operational picture for battalion leadership; monitor execution versus mission and surface immediate risks.
- Components: Mission Status card; Funnel Health card; DEP Loss card; School Compliance card; Risk Alerts panel; High-Risk Schools list; Top Funnel Leakage list.
- Data sources: `fact_mission_production`, `fact_mission_progress`, `fact_funnel_daily` / `fact_tne_pne`, `fact_dep_loss`, `fact_school_contacts`.
- Key endpoints: `/api/v2/mission-feasibility/summary`, `/api/funnel/analytics/leakage`, `/api/v2/fs-loss/dashboard`, `/api/ops/schools/contact-compliance`.
- Outputs: mission risk score, production progress, funnel bottlenecks, DEP loss counts, schools missing milestones.
- Command Center integrations: surface TWG-driven alerts and priority-school watchlists; feed to operations tasking.

## Recruiting Operations (Battalion Drill)

- Purpose: Actionable control for a single battalion (e.g., `6L`) — triage & remediation items.
- Components: Battalion selector; Mission KPIs; Funnel stage drop-off; DEP top-loss list; Compliance table with drilldowns; Assignment summary.
- Data sources: `fact_mission_production`, `fact_funnel_daily`, `fact_dep_loss`, `fact_school_contacts`, `fact_school_assignment`.
- Key endpoints: `/api/ops/recruiting-operations/summary`, `/api/ops/schools/high-risk`, plus Command Center endpoints.
- Outputs: ranked action list (schools/stations), remediation counts, drilldown links to School Intelligence.

## Planning — TWG Engine

- Purpose: Analytical workspace for planning: priority-setting, market analysis, scenario building (MDMP-like).
- Components: Scenario builder; Priority schools workspace; Market overlays (density/heatmap); What-if mission planner; Recommendation generator.
- Data sources: `fact_school_population`, `fact_school_zone_targeting`, market/prospect datasets, `dim_school`, historical `fact_mission_production`.
- Key endpoints: `/api/planning/twg/priority-schools`, `/api/planning/market/heatmap`, `/api/planning/scenario/run`.
- Outputs: prioritized school lists, recommended target markets, recruiter allocations, engagement plans.
- Command Center integrations: TWG outputs are exported as alerts/watchlists that appear in the Command Center Risk Alerts panel.

## School Intelligence

- Purpose: Canonical school profiles: assignment, population, targeting, contact history, and coverage metrics.
- Components: School profile; Assignment map (unit → school); Population & demographics; Zone targeting summary; Contact history & milestones.
- Data sources: `dim_school`, `fact_school_assignment`, `fact_school_population`, `fact_school_zone_targeting`, `fact_school_contacts`.
- Key endpoints: `/api/ops/schools/summary`, `/api/ops/schools/detail`, `/api/ops/schools/contact-compliance`.
- Outputs: authoritative school profile, coverage gaps, compliance status per school.
- Command Center integrations: School Compliance card rows and High-Risk Schools list.

## Production & Mission

- Purpose: Track mission contracts, monthly/quarterly progress, forecast gaps, and required corrective actions.
- Components: Contract vs production charts; Recruiter capacity dashboard; Forecast vs required WRs; Variance tables.
- Data sources: `fact_mission_production`, `fact_recruiter_standing`, `dim_unit`.
- Key endpoints: `/api/v2/mission-feasibility/summary`, `/api/v2/mission/production-timeseries`.
- Outputs: projected shortfalls, reallocation recommendations, mission attainment probability.
- Command Center integrations: Mission Status card and mission risk alerts.

## Funnel Analytics

- Purpose: Diagnose lead → contract flow and surface leakage stages and conversion rates.
- Components: Funnel Sankey/flow; Leakage table by stage; Station/school-level conversion; Cohort comparators.
- Data sources: `fact_funnel_daily`, `fact_tne_pne`, `fact_recruiter_activity`.
- Key endpoints: `/api/funnel/analytics/leakage`, `/api/funnel/analytics/stage-metrics`.
- Outputs: leakage hotspots, conversion-rate deltas, stage-level interventions.
- Command Center integrations: Funnel Health card and recruiter action items.

## DEP & Attrition

- Purpose: Monitor DEP losses and contract attrition risks; identify top loss codes and affected stations.
- Components: DEP Loss KPIs; Loss bucket histograms; Top stations by losses; Loss-driver analysis.
- Data sources: `fact_dep_loss`, `fact_mission_production`, `dim_unit`.
- Key endpoints: `/api/v2/fs-loss/dashboard`, `/api/v2/fs-loss/by-station`.
- Outputs: loss counts, trend alerts, priority stations for retention action.

## DataHub (Ingestion & Governance)

- Purpose: Central ingestion, dataset registry, run tracking, importer routing, and ingestion governance.
- Components: Upload UI; Run monitor; Dataset registry editor; Importer preview & error logs.
- Data sources: `dataset_registry`, `import_run_v2`, `import_run_error_v2`, uploaded file storage.
- Key endpoints: `/v2/datahub/upload`, `/v2/datahub/runs/{run_id}/commit`, `/v2/datahub/registry`.
- Outputs: committed rows into canonical fact tables, ingestion audits, dataset metadata.

---

## Cross-cutting Implementation Rules

- Importers write to canonical fact tables only. Avoid ad-hoc tables for derived metrics.
- TWG belongs in Planning. TWG outputs are persisted in planning artifact tables and surfaced in Command Center as alerts—do not implement TWG logic inside operational dashboards.
- All endpoints must support the standard API scope parameters and be optimized for read performance.
- Maintain a small number of authoritative sources per domain (see Authoritative Data Sources below).

## Authoritative Data Sources

- Mission: Vantage / THOR (primary)
- Funnel: AIE / CRM exports (primary)
- Production augment: BI Zone RA/USAR group (secondary)
- School population / targeting: NCES + BI Zone (primary)
- Contacts / compliance: School engagement exports (primary)
- DEP: USAREC reporting / BI Zone DEP (primary)

---

This file is the single source of truth for page responsibilities, canonical tables, standard endpoints, and org mapping rules. Update it whenever adding pages, fact tables, or changing endpoint contracts.

***
Generated and committed by the development workflow.
