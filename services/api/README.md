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

## Targeting Execution Tracker (420T Core Execution)

Authoritative execution/status engine:

- service: `services/api/app/services/targeting_execution_tracker.py`
- function: `summarize_targeting_execution_tracker(...)`

Purpose:

- consume board-directed execution items and shifts
- track execution status (`not_started | in_progress | completed | blocked`)
- classify off-track work (overdue, blocked, or effect miss)
- escalate stalled items to `TWG` or `BOARD`
- publish command-ready execution scorecards

Authoritative inputs only (no recomputation of upstream analytics):

- `targeting_board_engine`: `board_decisions`, `directed_shifts`, `downstream_twg_tasks`
- `twg_engine`: `prioritized_items`, `due_outs`
- `asset_engine`: `asset_distribution`, `recommended_shifts`, `execution_constraints`
- `mission_decrease_justification` (when provided or fetched by tracker)
- `funnel_engine`, `school_plan_engine`, `roi_engine`

Canonical output block:

- `summary`
- `execution_items`
- `blocked_items`
- `off_track_items`
- `escalations`
- `execution_scorecard`
- `data_sources`

Integration points:

- mission adjustment signal collection (`mission_decrease_justification.py`)
- command center phase2 (`command_center.py`)
- Power BI operational dataset export (`powerbi_feed.py`)

## Flash-to-Bang / Processing Engine (420T Core Execution)

Authoritative execution/status engine:

- service: `services/api/app/services/flash_to_bang_processing_engine.py`
- function: `summarize_flash_to_bang_processing_engine(...)`

Purpose:

- consume authoritative flash-to-bang and stage-aging outputs already produced by execution and funnel services
- track stage-aging watch items, stalled processing items, and overdue processing items
- classify bottleneck categories without recomputing upstream analytics
- escalate processing risk to `TWG` or `BOARD`
- publish command-ready processing scorecards

Authoritative inputs only (no recomputation of upstream analytics):

- `execution_quality`: `summary`, `by_scope`, `root_cause_breakdown`
- `funnel_engine`: `summary`, `prioritized_funnel_gaps`
- `accountability_engine`: `classification`, `reason_codes`, `recommended_next_action`

Canonical output block:

- `summary`
- `processing_items`
- `stalled_items`
- `overdue_items`
- `escalations`
- `processing_scorecard`
- `data_sources`
- `processing_constraints`

Integration points:

- mission adjustment signal collection (`mission_decrease_justification.py`)
- command center phase2 (`command_center.py`)
- Power BI operational dataset export (`powerbi_feed.py`)

## Current Operational Validation Snapshot

Latest full-system validation against the current workspace data showed:

- `market_engine`: `ok` on real uploaded market data (`6L MARKET CORE.csv`)
- `funnel_engine`: `invalid_dataset_schema` on the current funnel source; this is surfaced honestly as a schema/data issue rather than hidden fallback math
- `school_plan_engine`: `no_data` correctly handled
- `roi_engine`: `no_data` correctly handled
- LOE-dependent downstream engines now degrade safely when LOE tables are absent instead of crashing (`twg_engine`, targeting board, asset, execution tracker, and flash-to-bang processing flows)
- focused regression evidence for the execution tracker and flash-to-bang integrations remains green

Known limitation during this validation pass:

- command-wide aggregated views can still respond slowly when the current funnel source requires expensive date parsing or schema fallback handling

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

---

## ROI / Event Effectiveness Engine (Operational 420T)

Authoritative module:

- `services/api/app/services/roi_engine.py`

Authoritative inputs (no synthetic data):

- Events: `emm_event` table (primary — has unit_rsid, zip, cost_total); fallback to `event_fact`.
- Costs: `spend_fact` grouped by `event_id` (overrides `emm_event.cost_total` when present).
- Leads/contracts: `lead_journey_fact` grouped by `event_id` (contract_flag=1 for contracts).
- Benchmarks: `roi_thresholds` table (seeded keys: `cpl_target=100`, `cpc_target=2500`).
- Market alignment: `market_engine.prioritized_market_zip` capability score for event zip.
- Targeting alignment: `targeting_engine.prioritized_targets` priority score (0–1 → 0–100) for event zip.

Deterministic scoring formula (all sub-scores 0–100):

```
roi_score = 0.35 * contract_outcome
          + 0.25 * lead_outcome
          + 0.20 * cost_efficiency
          + 0.10 * market_alignment
          + 0.10 * targeting_alignment
```

Sub-score definitions:

| Sub-score | Inputs | Logic |
|-----------|--------|-------|
| `contract_outcome` | contracts, cost, cpc_target | CPC vs cpc_target bands (100/70/40/10); 0 if no contracts |
| `lead_outcome` | leads, cost, cpl_target | CPL vs cpl_target bands (100/70/40/10); 0 if no leads |
| `cost_efficiency` | leads, contracts | lead→contract rate bands (100/80/60/30/10); 50 neutral if no leads |
| `market_alignment` | event zip → market_engine score | market_capability_score (0–100); 50 neutral if zip absent |
| `targeting_alignment` | event zip → targeting score | priority_score × 100; 50 neutral if zip absent |

Effectiveness bands: `high` ≥ 70, `moderate` 40–69, `low` < 40.

ROI engine output shape:

- `status`: `ok | no_data`
- `roi_engine.summary`: total_events_scored, high/moderate/low counts, avg_roi_score, avg_cost_per_lead, avg_cost_per_contract, total_spend, total_leads, total_contracts, scoring_formula
- `roi_engine.prioritized_events`: deterministic event ranking (roi_score DESC, event_id ASC) with all sub-scores, cost/lead/contract totals, recommendations list, trace_id
- `roi_engine.event_type_performance`: per-event-type aggregates (avg_roi_score, event_count, effectiveness_band, avg_cost_per_contract)
- `roi_engine.roi_recommendations`: command-level actions (owner_level, action, expected_effect, time_horizon, rationale, trace_id)
- `roi_engine.data_as_of`: latest event start_dt across scored events
- `roi_engine.source_tables`: lineage list

Legacy duplicate paths unified under roi_engine:

- `automation/engine.py:simple_event_recommendation()` — previously used LOE heuristic from `event_cost`. Now delegates to `roi_engine.compute_*` functions using `spend_fact` + `lead_journey_fact` for deterministic scoring.
- `routers/roi.py` `/financial` and `/score` endpoints accept manual payload inputs (separate API surface for ad-hoc calculation; not replaced).

Integration points:

- mission adjustment signal collection (`roi` block and `roi_effectiveness` causal factor)
- mission recommendations (`roi_action` recommendation derived from top roi_engine recommendation)
- command center overview block (`phase2.roi_engine`)
- Power BI operational dataset (`roi_summary`, `roi_prioritized_events`, `roi_recommendations`, `roi_event_type_performance`)

---

## TWG Engine (Operational 420T Workflow)

Authoritative module:

- `services/api/app/services/twg_engine.py`

Authoritative inputs (no synthetic data; no parallel analytics paths):

- `market_engine` output: market posture and top market gaps
- `funnel_engine` output: prioritized funnel dropoff gaps
- `targeting_engine` output: prioritized ZIP targeting issues
- `school_plan_engine` output: underengaged priority schools
- `roi_engine` output: low-effectiveness event concentration
- Existing authoritative risk signals: `accountability_engine` and `loe_engine`

TWG purpose:

- Identify operational issues for TWG review
- Prioritize those issues deterministically
- Produce command-usable actions and due-outs
- Identify candidates for future Targeting Board elevation

Deterministic priority formula (0–100):

```
twg_priority_score =
  0.25 * market_issue_weight +
  0.20 * funnel_issue_weight +
  0.20 * targeting_issue_weight +
  0.15 * school_issue_weight +
  0.10 * roi_issue_weight +
  0.10 * mission_risk_weight
```

Priority bands:

- `high`: `>= 70`
- `medium`: `40` to `< 70`
- `low`: `< 40`

Board elevation rule:

- `board_elevation_recommended = true` when item is high priority and reflects multi-signal concentration requiring resource/tradeoff decisions (for example: reallocation, stopping low-value formats, mission risk posture).

TWG engine output shape:

- `status`: `ok | no_data | invalid`
- `twg_engine.summary`: total item counts by band, board elevation count, overall TWG status
- `twg_engine.prioritized_items`: deterministic ranked items with owner, action, due_out, rationale, source, trace_id
- `twg_engine.twg_agenda`: sequence-ordered agenda rows (`highest priority first`)
- `twg_engine.due_outs`: command-usable action assignments
- `twg_engine.board_candidates`: filtered high-priority board-elevation-ready rows
- `twg_engine.data_sources`: upstream lineage map

Workflow integrations:

- mission adjustment: TWG issue concentration is exposed as `twg_issue_concentration` causal factor and `signal_summaries.twg`
- command center overview: `phase2.twg_engine`
- Power BI operational dataset exports:
  - `twg_summary`
  - `twg_prioritized_items`
  - `twg_due_outs`
  - `twg_board_candidates`


## Targeting Board Engine (Command Decision Layer — 420T Workflow)

Authoritative module:

- `services/api/app/services/targeting_board_engine.py`

Authoritative inputs (consume-only; no recomputation):

- `twg_engine` output: board_candidates (high-priority TWG items for board review)
- `roi_engine` output: ROI effectiveness metrics and guidance
- `mission_decrease_justification` output: mission feasibility signals and causal factors
- `targeting_engine` output: ZIP targeting alignment data
- Supporting engines: `market_engine`, `funnel_engine`, `school_plan_engine`

Targeting Board purpose:

- Consume TWG board_candidates and evaluate multi-engine impact
- Make board-level binary decisions: approve | modify | reject
- Direct resource shifts across markets, ZIPs, schools, and events
- Create executable downstream tasks for TWG to execute
- Serve as authoritative command decision layer for 420T operations

Decision-making formula (0–100 board priority):

```
board_priority_score =
  0.40 * twg_priority_score +
  0.20 * mission_impact +
  0.15 * roi_impact +
  0.15 * targeting_alignment +
  0.10 * resource_pressure
```

Decision rules:

- **approve**: board_priority >= 65 (proceed as recommended; generates resource shift if high priority)
- **modify**: board_priority 35–64 (adjust scope, timeline, or owner; resource-constrained)
- **reject**: board_priority < 35 (insufficient multi-engine impact justification)

Resource shift generation rules:

- Generate only for approved items with high priority (>= 75)
- Shift types:
  - **funnel**: Reallocate recruiter effort from retention optimization to funnel acceleration
  - **targeting**: Shift effort from low-opportunity ZIPs to high-opportunity ZIPs
  - **roi**: Redirect event effort from low-ROI events to high-ROI activities
  - **school**: Intensify effort at high-opportunity schools
  - **effort**: Concentration moves across competency areas

Downstream task generation:

- **mandatory rule**: Every approve/modify decision generates exactly one executable TWG task with:
  - `task_id`, `source_board_decision_id`, `owner_level`, `action`, `due_out`, `expected_effect`
  - Task action is concrete and actionable by TWG
  - Task ownership remains with TWG (not board)
  - Closes the loop: Board decision → TWG execution → operational outcome

Targeting Board output shape:

- `status`: `ok | no_data | invalid`
- `targeting_board_engine.summary`:
  - `total_items`: Number of board candidates evaluated
  - `approved_count`: Items approved for execution
  - `modified_count`: Items approved with scope/timeline modification
  - `rejected_count`: Items rejected as insufficient justification
  - `resource_shift_count`: Resource shifts directed
  - `overall_board_posture`: `aggressive | balanced | constrained | unknown` (based on approval rate)
- `targeting_board_engine.prioritized_board_items`: Evaluated board items with decision type, rationale, impact level, resource implication
- `targeting_board_engine.board_decisions`: Binary decisions with owner, time horizon, expected effects
- `targeting_board_engine.directed_shifts`: Resource reallocation directives with justification
- `targeting_board_engine.downstream_twg_tasks`: Executable tasks with owner, due-out, expected effect
- `targeting_board_engine.data_sources`: Upstream lineage (all authoritative sources consumed)

Workflow integrations:

- mission adjustment: Board decision approval rate exposed as `board_decision_approval` causal factor and `signal_summaries.board`
- command center overview: `phase2.targeting_board_engine` (summary, top decisions, shifts)
- Power BI operational dataset exports:
  - `board_summary`
  - `board_prioritized_items`
  - `board_decisions`
  - `board_directed_shifts`
  - `board_downstream_tasks`

Critical rule (determinism & scope):

- **NO** parallel scoring paths; board evaluates TWG output only
- **NO** recomputation of analytics; all metrics inherited from upstream engines
- **DETERMINISTIC**: Same TWG candidates + same upstream signals = same board decisions every time
- **SCOPED**: Enforce BN/CO/STN-level scope enforcement consistent with TWG engine
- **EXECUTABLE**: All decisions must be able to be handed to TWG with actionable due-outs


