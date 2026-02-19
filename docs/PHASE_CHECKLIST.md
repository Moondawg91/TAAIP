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

Acceptance Criteria
- `/api/operations/targeting-data` ingest and query endpoints exist.

How to Verify
- Endpoint: POST `/api/operations/targeting-data` returns 200

Status: NOT DONE

Evidence placeholder

## Phase 7 — Reporting & Mission Assessment

Objective
- Mission Assessment snapshots, Command Priorities and LOEs, and mission assessment comparisons.

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
