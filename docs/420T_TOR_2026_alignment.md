420T TOR 2026 → TAAIP Alignment Spec
=====================================

Purpose
-------
- 420T is the transformational position within USARD formations and the SME + principal advisor to BDE/BN commanders for recruiting operations.
- Lead fusion + precision recruiting processes; provide data-driven reporting to BN/BDE commanders.

Operational truths to preserve
-----------------------------
- 420T is not subordinate to DCO/XO/S3 or any BDE/BN staff section.
- IPPS-A access is analysis-only; no S1 / AIMS Marketplace transactional functions.
- Outputs must follow Data → Insight → Action → Outcome.
- Support BN + BDE views and distinguish BI (historical) vs DS (predictive/recs).

Non‑negotiable product constraints
---------------------------------
1. Analytics-first: TAAIP remains a decision support and intelligence platform.
2. Commander-facing outputs: insights must translate to actions and outcomes.
3. BN + BDE views: support both levels natively.
4. IPPS-A analysis-only guardrail: ingest/analysis only; no talent-management actions.
5. Avoid redundancy: provide "tool health" outputs for quarterly THOR-style reviews.

Concrete implementation changes (summary)
---------------------------------------
- Add a TOR-aligned Metrics Catalog YAML: `backend/config/tor_metrics.yaml`.
- Expose a small router: `GET /api/v2/tor/metrics` and `GET /api/v2/tor/metrics/{metric_id}`.
- Make Indicators & Warnings first-class via `indicator_events` table (schema/design documented in repo).
- Require dataset-driven ingestion: `dataset_key` → column maps, required fields, normalization rules, target table.
- Minimal role model (420T, BN_CMD, BDE_CMD, Analyst, Viewer) and scope binding (BN/BDE/Station).
- Tool Health logging for dashboard usage + quarterly review export.

Acceptance criteria (definition of "aligned")
---------------------------------------------
- Real dataset imports map to TOR metric categories.
- Dashboards show metrics grouped by TOR categories (School, Lead Mgmt, MAP, Processing, FS Mgmt, Marketing/ROI).
- BI vs DS labels and recency shown; recommended actions mapped to red/yellow/green.
- Auditability: raw row storage + preview and per-target-table inserted row counts.
- Guardrails: no S1 transactional endpoints; IPPS-A flagged as analysis-only.

Where files live
----------------
- `docs/420T_TOR_2026_alignment.md` (this file)
- `backend/config/tor_metrics.yaml` (catalog)
- `backend/routers/tor.py` (API)

Next actions
------------
1. Install the TOR router (`app.include_router(...)` added to `taaip_service.py`).
2. Build dataset registry from uploaded Excel files (optional — triggers mapping generation).
3. Wire dataset_key → TOR metric mapping so uploads automatically tag which TOR metrics they feed.

For the quick win, create the dataset registry and I'll auto-populate it from your uploaded XLSX files.
