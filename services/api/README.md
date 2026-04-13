Services API - local run

From the repository root you can run the API using the package layout in this folder.

Recommended (from repo root):

```bash
cd services/api
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Or, from the repo root (equivalent):

```bash
source services/api/.venv/bin/activate
python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Notes:
- This README intentionally does not enable any demo seeding. The service will start with an empty database and empty-state UX.
- If you need XLSX parsing support, install `openpyxl` into the `services/api` virtualenv: `pip install openpyxl`.
- Alembic under `services/api/alembic` is the only supported schema migration system for this repository.
- Legacy `migrate*.py`, `backend/migrate.py`, and runtime schema bootstrap helpers are deprecated and blocked by default.
# TAAIP - API Service (FastAPI)

This service provides the backend API for TAAIP. It contains importers for RSIDs and ZIP coverage and implements basic endpoints for ZIP coverage lookups.

Quick start (local, sqlite):

1. Create a virtualenv and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the API locally:

```bash
uvicorn app.main:app --reload --port 8000
```

3. Import RSIDs then ZIP coverage (import RSIDs first):

```bash
python scripts/import_rsids.py /path/to/RSIDs\ USAREC.xlsx
python scripts/import_zips.py /path/to/Zip\ Codes\ in\ USAREC.xlsx
```

Notes:
- Schema changes must be applied through Alembic only.
- The application no longer treats startup-time table creation or script-based migrations as supported schema management paths.

## Phase 1 - Local Dev & Testing

### Environment Variables

```bash
export DATABASE_URL="sqlite:///./services/api/taaip_dev.db"
export JWT_SECRET="devsecret"
export PYTHONPATH="$(pwd)"
```

### Run Migrations

```bash
./.venv/bin/python -m alembic -c services/api/alembic.ini upgrade head
```

This is the single supported migration command path for this repository.
If needed, override the target DB per invocation: `DATABASE_URL=sqlite:///./data/taaip.sqlite3 ./.venv/bin/python -m alembic -c services/api/alembic.ini upgrade head`.

### Run API

```bash
uvicorn app.main:app --reload
```

API Health Check:

```
GET http://localhost:8000/health
```

## Router Ownership Map

The API entrypoint is `services/api/app/main.py`, and these functional areas have a single owning router module:

- command center: `services/api/app/routers/command_center.py` (`/api/command-center/*`)
- domain v2: `services/api/app/api_domain.py` (`/api/v2/*` SQLAlchemy domain endpoints)
- powerbi feed: `services/api/app/routers/powerbi_feed.py` (`/api/powerbi/*`)
- school recruiting: `services/api/app/routers/school_recruiting.py` (`/api/school/*`)
- refresh: `services/api/app/routers/refresh.py` (`/api/refresh/*`)

Known overlap to preserve compatibility:

- Legacy compatibility `v2` router and `api_domain` both serve under `/api/v2/*`. Keep include order in `main.py` so compatibility routes are evaluated before domain routes.

## Seeding and Imports (important — no demo data)

This service does NOT seed demo or synthetic operational data. Only system defaults and reference tables are safe to seed.

1) Seed system defaults (idempotent):

```bash
python services/api/scripts/seed_defaults.py
```

This will create only the `market_category_weights` defaults and `funnel_stages` baseline. It will not create events, metrics, funnel transitions, burden inputs, LOEs, or station/ZIP coverage.
Run the Alembic migration command above before seeding defaults.

2) Optional admin users (ONLY when explicitly requested):

```bash
SEED_SAMPLE_USERS=true python services/api/scripts/seed_defaults.py
```

This will create only `sysadmin` and `usarec_admin` users. Do NOT enable this in production unless you intend to create admin accounts.

3) Import org and ZIP coverage (authoritative source):

```bash
python services/api/scripts/import_rsids.py "/path/to/RSIDs USAREC.xlsx"
python services/api/scripts/import_zips.py "/path/to/Zip Codes in USAREC.xlsx"
```

Import scripts are the only supported mechanism to populate `stations` and `station_zip_coverage`. Do not seed those tables manually.


## Run Tests (Phase 1 Only)

```bash
pytest -q services/api/tests
```

Expected Output:

```
2 passed
```

## CI Command

CI should run:

```bash
pytest -q services/api/tests
```

## Decision Output - Mission Decrease Justification

The domain v2 router includes a decision-output endpoint for commander-ready mission decrease analysis.

Generate:

```bash
POST /api/v2/decision-output/mission-decrease-justification
```

Request payload:

```json
{
	"org_id": "1A1",
	"period_start": "2026-01-01",
	"period_end": "2026-01-31",
	"baseline_start": "2025-12-01",
	"baseline_end": "2025-12-31",
	"include_evidence": true,
	"force_refresh": false
}
```

Retrieve cached result by request id:

```bash
GET /api/v2/decision-output/mission-decrease-justification/{request_id}
```

Response highlights:
- `mission_delta_summary`: current vs baseline totals and percent delta.
- `causal_factors`: deterministic ranking by weighted score desc then factor code asc.
- `confidence`: score, band (`low|medium|high`), completeness, and agreement.
- `one_slide_payload`: compact briefing payload for command syncs.
- `evidence`: traceable source snapshots (when `include_evidence=true`).

## Market Intelligence Engine (420T)

The Market Intelligence Engine is implemented in:

- `services/api/app/services/market_engine_contract.py`
- `services/api/app/services/market_engine.py`

Authoritative real source input:

- `uploads/6L MARKET CORE.csv`

Behavior and constraints:

- No demo market rows are generated.
- If source is unavailable: `status=no_active_dataset`.
- If required columns are missing: `status=invalid_dataset_schema` with `schema_error`.
- Scoring is deterministic and stable-sorted.

Key derived metrics per ZIP:

- `recruiting_age_male`
- `recruiting_age_female`
- `total_recruiting_age_population`
- `education_quality_score`
- `income_access_score`
- `market_capability_score` (0-100)

Base weighting (centralized constants in code):

- `0.50 * normalized_recruiting_age_population`
- `0.30 * normalized_education_quality_score`
- `0.20 * normalized_income_access_score`

Classification:

- strong: `score >= 70`
- moderate: `40 <= score < 70`
- weak: `score < 40`

Integration points:

- targeting overlays and recommendations
- mission adjustment justification signal collection
- command center overview block (`market_engine`)
- Power BI operational dataset (`market_engine_summary`)

## Funnel Engine (Operational)

Source dataset:

- `data/dev_datasets/Recruiting Funnel Enriched.csv`

Behavior and constraints:

- Uses only uploaded operational funnel source data (no synthetic fallback).
- Supports malformed/non-canonical headers via value-pattern inference.
- If source is unavailable: `status=no_active_dataset`.
- If required canonical mapping cannot be inferred: `status=invalid_dataset_schema` with `schema_error` and `schema_mapping`.
- Scope-aware summaries are supported for `USAREC`, `BDE`, `BN`, `CO`, and `STN`.
- Output ranking is deterministic and stable-sorted.

Canonical operational summary includes:

- `total_leads`
- `total_appointments`
- `total_interviews`
- `total_contracts`
- `lead_to_appointment_rate`
- `appointment_to_interview_rate`
- `interview_to_contract_rate`
- `lead_to_contract_rate`
- `largest_dropoff_stage`
- `overall_funnel_status` (`healthy` | `watch` | `critical` | `unknown`)

Integration points:

- mission adjustment justification signal collection (`funnel_health` factor)
- command center overview block (`phase2.funnel_engine`)
- Power BI operational dataset (`funnel_engine_summary`)
- targeting expansion metadata (`funnel_signal` per recommendation)

## Targeting Engine (Operational 420T)

Authoritative module:

- `services/api/app/services/targeting_engine.py`

Authoritative inputs (no synthetic data):

- Market: `market_engine.prioritized_market_zip`, `market_capability_score`, `opportunity_band`
- Funnel: `funnel_engine` station status and dropoff signals
- School: `school_access` top gaps; fallback to `fact_school_contacts` when school access rows are absent

Deterministic priority formula:

- `targeting_priority_score = 0.50*market_score + 0.30*(1-funnel_efficiency) + 0.20*school_gap_score`

Targeting output shape:

- `status`: `ok | no_data | invalid`
- `targeting_engine.summary`: total/high/moderate/low priority ZIP counts
- `targeting_engine.prioritized_targets`: commander-ready ZIP rows with funnel and school signals, score, band, rationale, and `trace_id`
- `targeting_engine.top_targeting_shifts`: prioritized shift actions for board use
- `targeting_engine.data_sources`: source lineage for market/funnel/school

Integration points:

- mission adjustment signal collection (`targeting` block)
- command center overview block (`phase2.targeting_engine`)
- Power BI operational dataset (`targeting_engine_summary`)
- compatibility wrapper retained in `targeting_expansion.recommendations_for_scope`

## School Plan Engine (Operational 420T)

Authoritative module:

- `services/api/app/services/school_plan_engine.py`

Authoritative inputs (no synthetic data):

- School terrain: `schools` canonical rows; fallback to real `fact_school_contacts` when `schools` is absent or empty.
- Market alignment: `market_engine.prioritized_market_zip` capability/opportunity signals.
- Funnel intervention: `funnel_engine` station-level health and dropoff priority.
- Targeting reinforcement: `targeting_engine.prioritized_targets` score reinforcement.

Deterministic priority formula:

- `school_priority_score = 100*(0.40*market_alignment + 0.30*access_gap + 0.20*funnel_intervention + 0.10*targeting_reinforcement)`

School plan output shape:

- `status`: `ok | no_data | invalid_dataset_schema`
- `school_plan_engine.summary`: total schools, priority schools, engaged/underengaged counts, high-opportunity count, overall status
- `school_plan_engine.prioritized_schools`: deterministic school-level ranking with market/funnel/access signals, score, band, action, rationale, and trace
- `school_plan_engine.school_recruiting_plan`: commander-ready actions with owner level, expected effects, time horizon, rationale, and trace
- `school_plan_engine.top_school_gaps`: top school gaps for board and sync consumption
- `school_plan_engine.data_sources` and `source_school_dataset`: lineage to operational datasets

Integration points:

- mission adjustment signal collection (`school_plan` block and `school_plan_gap` factor)
- mission recommendations (`school_plan_action` recommendation derived from top school plan row)
- command center overview block (`phase2.school_plan_engine`)
- Power BI operational dataset (`school_plan_summary`, `school_plan_prioritized_schools`, `school_plan_actions`)

