# Phase‑4 Checklist — Make App Fully Functional

This checklist documents the steps to complete Phase‑4 (ingest/persist real data, provenance, retention, and Power BI exports).

## Quick verification (smoke tests)
- Start API server (local dev):
  - `source .venv/bin/activate`
  - `export LOCAL_DEV_AUTH_BYPASS=1`
  - `export TAAIP_DB_PATH=./data/taaip.sqlite3`
  - `python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8000 --reload`
- Seed minimal org data: `PYTHONPATH=. python scripts/seed_phase4.py`
- Health: `curl http://127.0.0.1:8000/health`
- Org units: `curl http://127.0.0.1:8000/api/v2/org/units-summary`
- Zip coverage (compat): `curl http://127.0.0.1:8000/api/org/stations/1A1D/zip-coverage`
- Coverage summary (v2): `curl 'http://127.0.0.1:8000/api/v2/coverage/summary?scope=STN&value=1A1D'`

## Database
- Ensure runtime idempotent DDL is applied on startup (`services/api/app/db.py:init_schema`).
- Reconciliation migrations for legacy tables added (events, marketing_activities).
- For production, create Alembic migration scripts from the current models and review.

## Backend
- Endpoints verified by tests and smoke checks:
  - `/api/org/stations/{rsid}/zip-coverage` (compat and v2)
  - `/api/v2/coverage/summary`
  - Power BI endpoints: `/api/powerbi/*` (fact exports)
- RBAC: runtime scoped access enforced (see `services/api/app/routers/compat_org.py` and `api_org.py`).

## Frontend
- Production build: `npm --prefix apps/web run build`
- Tests: `npm --prefix apps/web test -- --watchAll=false`

## CI / PR
- PR created: review CI runs and address failures.
- Recommended: configure CI to run the same SQLite PR environment variables and use WAL for reliable DDL.

## Next work (optional enhancements)
- Add more realistic seed data for LOEs, command priorities, and marketing activities.
- Add e2e tests (Cypress or Playwright) for import flow and RBAC flows.
- Harden migrations into Alembic revisions.

---
Generated: Feb 18, 2026
