# TAAIP Phase 1–9 DONE Checklist

This document lists Phase 1 through Phase 9 objectives, acceptance criteria, verification steps, status, and evidence placeholders.

> Note: No phase may be marked DONE until its verification commands and UI checks succeed when executed against a running local instance.

## Phase 1 — Core Platform

Objective
- Foundation: backend API, DB schema, auth, and minimal frontend shell.

Acceptance Criteria
- API responds on `/health` (HTTP 200).
- DB schema can be initialized with `services/api/app/db.init_db()`.
- Basic auth (dev bypass) controllable via `LOCAL_DEV_AUTH_BYPASS`.

How to Verify
- Command: `python -c "from services.api.app.db import init_db; print(init_db())"` (should print DB path)
- Endpoint: `curl -sS http://127.0.0.1:8000/health`
- UI: App loads shell and sidebar visible

Status: DONE

Evidence placeholder: paste command output and screenshot/JSON

## Phase 2 — Ingest & Provenance

Objective
- File imports, import_job tracking, preview, and commit with provenance.

Acceptance Criteria
- Upload endpoint returns preview JSON without committing.
- `import_job` and `import_file` rows can be created and show `status`.

How to Verify
- Endpoint: POST `/api/imports/preview` (describe payload)
- DB: `SELECT COUNT(1) FROM import_job WHERE status='uploaded'` returns integer

Status: NOT DONE

Evidence placeholder: command and JSON

## Phase 3 — Data Warehouse & Facts

Objective
- Shared dims/fact tables (`dim_org_unit`, `dim_time`, `fact_production`, `fact_marketing`, `fact_funnel`).

Acceptance Criteria
- Tables exist and are writable.
- Simple ETL can write `fact_marketing` rows.

How to Verify
- SQL: `SELECT name FROM sqlite_master WHERE type='table' AND name='fact_marketing'`
- Endpoint: POST `/api/ingest/marketing` (returns 200)

Status: NOT DONE

Evidence placeholder: SQL output / endpoint response

## Phase 4 — Planning & Projects

Objective
- Projects/events CRUD, calendar, tasks, and project-event-budget relations.

Acceptance Criteria
- `/api/planning/projects-events` CRUD endpoints exist and persist to `projects` and `event` tables.

How to Verify
- Endpoint: GET `/api/planning/projects-events` returns JSON list
- DB: `SELECT COUNT(1) FROM projects` runs

Status: NOT DONE

Evidence placeholder

## Phase 5 — Resources & Training

Objective
- Document library, LMS courses/enrollments, searchable docs storage.

Acceptance Criteria
- Doc upload endpoint works and creates `doc_library_item` and `doc_blob` rows.
- LMS course creation and enrollments persist.

How to Verify
- Endpoint: POST `/api/resources/docs` with multipart/form-data
- Endpoint: GET `/api/training/courses`

Status: NOT DONE

Evidence placeholder

## Phase 6 — Targeting & Operations

Objective
- Targeting methodology, targeting data ingestion, mission planning pages, boards.

Feature Status
- Targeting Execution Tracker (420T core execution): DONE
- Scope completed: authoritative execution/status engine, mission adjustment integration, command center integration, Power BI operational export, focused tests, API docs
- Flash-to-Bang / Processing (420T core execution): DONE
- Scope completed: authoritative processing-status engine, mission adjustment integration, command center integration, Power BI operational export, focused tests, API docs
- Funnel operationalization repair (real uploaded data): DONE
  - current resolved source: `data/dev_datasets/Recruiting Funnel Enriched.csv`
  - repaired headerless and shifted-header normalization path now returns `status=ok`
  - `prioritized_funnel_gaps` now populate from the real dataset
  - mission adjustment, command center phase 2, and Power BI funnel consumers validated against the repaired path
- School Plan operationalization repair (real uploaded data): DONE
  - current resolved source: `data/dev_datasets/school contacts.xlsx`
  - `school_plan_engine` now returns `status=ok` with non-empty prioritized school rows using the uploaded workbook fallback
  - school ZIP reinforcement remains neutral when the uploaded workbook does not carry ZIP-level school fields
- ROI operationalization repair (real uploaded data): DONE
  - current resolved source: `data/dev_datasets/EMM PORTAL.xlsx`
  - `roi_engine` now returns `status=ok` with non-empty prioritized event rows using the uploaded EMM workbook fallback
  - focused school/ROI regression evidence: `26 passed`
- Connected-system operational validation pass: DONE
  - broad regression evidence: `133 passed` across funnel, school plan, ROI, TWG, targeting board, asset, execution tracker, flash-to-bang, mission adjustment, and phase2 command tests
  - `market_engine`: complete on current workspace data at aggregate scope using `6L MARKET CORE.csv`
  - `funnel_engine`: complete on current workspace data after normalization repair using `Recruiting Funnel Enriched.csv`
  - `school_plan_engine`: complete on current workspace data after uploaded-school fallback repair using `school contacts.xlsx`
  - `roi_engine`: complete on current workspace data after uploaded-EMM fallback repair using `EMM PORTAL.xlsx`
  - downstream mission / command center / Power BI surfaces now consume the upstream engines correctly and expose the expected connected blocks
  - real integration defects fixed in this pass: signal propagation reuse, school authoritative-source precedence, scoped market fallback, and stable downstream field/metric shapes
  - honest partial behavior remains by design for unit scopes with no active authoritative rows; those surfaces return `no_data` / `no_active_dataset` instead of inventing defaults
- Commander-ready workflow and frontend consolidation pass: DONE
  - active commander shell in `taaip-dashboard` has been consolidated into one workflow sequence: Command Center → Mission Adjustment → Diagnostics → TWG and Board → Asset/Execution/Processing → Power BI
  - Mission Adjustment is now embedded in the main workflow instead of remaining an isolated legacy surface
  - workflow pages consume authoritative backend outputs only and surface honest loading, error, and empty states
  - frontend build verification evidence: `npm run build` completed successfully
  - workflow regression evidence: `npm test` returned `3 passed, 0 failed`

Acceptance Criteria
- `/api/operations/targeting-data` ingest and query endpoints exist.

How to Verify
- Endpoint: POST `/api/operations/targeting-data` returns 200

Status: NOT DONE

Evidence placeholder

## Phase 7 — Reporting & Mission Assessment

Objective
- Mission Assessment snapshots, Command Priorities and LOEs, and mission assessment comparisons.

Feature Status
- Controlled Learning Layer (Outcome Learning + Live Context + Adaptive Update): DONE
  - completed services:
    - `services/api/app/services/outcome_learning_engine.py`
    - `services/api/app/services/live_context_engine.py`
    - `services/api/app/services/adaptive_update_engine.py`
  - mission, command center, and Power BI operational surfaces now expose additive controlled-learning blocks
  - adaptive updates are proposal-based only with explicit approval states and rollback/version metadata
  - admin-only proposal visibility and state transitions exposed under `/api/v2/admin/controlled-learning/*`
  - production scoring logic remains unchanged unless an approved proposal is explicitly applied
  - verification evidence: `7 passed` in focused controlled-learning tests

Acceptance Criteria
- Command Priorities CRUD exists; LOEs editable and stored.
- `/api/performance/mission-assessment` computes baseline vs actual metrics.

How to Verify
- Endpoint: GET `/api/performance/mission-assessment`
- UI: Command Priorities page shows 3 priorities and 5 LOEs editable fields

Status: NOT DONE

Evidence placeholder

## Phase 8 — Budgeting & ROI

Objective
- Budget rollups: planned / committed / actual / remaining computed across projects/events/activities.

Acceptance Criteria
- `/api/budget/summary` returns numeric `planned`, `actual`, `remaining` and uses `budget_line_item` and `marketing_activities`.

How to Verify
- Endpoint: GET `/api/budget/summary`
- SQL: `SELECT SUM(amount) FROM budget_line_item` and `SELECT SUM(cost) FROM marketing_activities`

Status: NOT DONE

Evidence placeholder

## Phase 9 — Hardening & CI

Objective
- CI jobs, verify script, route crawl, and deterministic builds. No white UI surfaces.

Feature Status
- Deployment hardening and operational admin workflow: DONE
  - canonical startup now runs through `scripts/taaip_preflight.sh` and the repo-root launchers instead of user-specific absolute desktop paths
  - backend DB, upload, refresh, export, and documents paths are normalized and validated before startup
  - `docker-compose.yml`, `ecosystem.config.cjs`, and the systemd service example now use the same backend entrypoint and environment contract
  - admin refresh endpoints require admin-manage access and keep source replacement out of the commander-facing workflow
  - invalid-schema and no-data uploads fail honestly with structured errors and do not replace the active authoritative dataset version
  - verified evidence: `5 passed` in focused deployment/admin regressions, runtime preflight `status: ok`, commander workflow frontend `3 passed`, frontend production build succeeded
- Role-based operational walkthrough and command demo readiness: DONE
  - commander, 420T operator, and admin perspectives are mapped to role-safe workflow visibility in the active commander shell
  - commander and 420T perspectives do not expose admin console controls
  - admin refresh controls remain isolated to admin workflows and non-admin refresh source access returns `403`
  - operational command demo sequence is documented in `docs/COMMAND_DEMO_SEQUENCE.md`
  - verified evidence: commander + role visibility frontend regressions `6 passed`, refresh admin role-safety regressions `5 passed`, frontend production build succeeded
- Final production release preparation and sustainment documentation: DONE
  - release packaging instructions are finalized for backend/frontend startup, preflight, env variables, DB path, and Alembic migration expectations
  - sustainment guides are published for commander quick use, 420T operator workflow, and admin refresh troubleshooting
  - concise command-demo runbook is published with pre-demo checks, startup sequence, fallback paths, and no-data explanation points
  - documentation maps to current runtime scripts and admin-safe refresh behavior without introducing demo data or placeholder outputs
  - verification evidence: release safety startup checks and focused regressions passing (`test_refresh_admin_workflow`, `test_runtime_preflight_contract`, frontend tests/build)

Acceptance Criteria
- `scripts/verify_app.sh` runs without error and reports PASS for required checks.

How to Verify
- Run: `bash scripts/verify_app.sh` (local dev)
- CI: GitHub Actions runs smoke curl checks

Status: PARTIAL

Evidence placeholder

---

Notes
- This checklist is the authoritative plan for implementing and verifying Phase 1–9. Each line under "How to Verify" must be implemented as an automated check (endpoint, SQL, or CLI) before marking the phase DONE.
