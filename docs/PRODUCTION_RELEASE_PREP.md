# TAAIP Production Release Preparation

This guide is for real-world handoff and repeatable startup using the current, completed system.

Scope:
- commander workflow shell in `taaip-dashboard`
- backend in `services/api`
- deployment hardening scripts and runtime preflight
- admin-safe refresh workflow

## 1) Release Prerequisites

- Repository checked out at the approved release commit.
- Python virtual environment available at `.venv` in repo root.
- Node dependencies available for `taaip-dashboard`.
- Runtime user has read/write access to:
  - `TAAIP_DB_PATH`
  - `TAAIP_UPLOAD_DIR`
  - `TAAIP_REFRESH_UPLOAD_DIR`
  - `EXPORT_STORAGE_DIR`
  - `TAAIP_DOCUMENTS_PATH`

## 2) Required Environment Variables

Primary required variables (resolved by `scripts/taaip_preflight.sh`):

- `TAAIP_DB_PATH` default: `data/taaip.sqlite3`
- `DATABASE_URL` default: `sqlite:///$TAAIP_DB_PATH`
- `TAAIP_UPLOAD_DIR` default: `services/api/.data/imports`
- `TAAIP_REFRESH_UPLOAD_DIR` default: `data/refresh_uploads`
- `EXPORT_STORAGE_DIR` default: `data/exports`
- `TAAIP_DOCUMENTS_PATH` default: `data/documents`
- `HOST` default: `127.0.0.1`
- `PORT` default: `8000`

Production example values are in `deploy/.env.prod.example`.

## 3) DB Path and Migration Expectations

Migration policy:
- Alembic is the single supported schema migration path.
- Legacy migration scripts are blocked by default.

Run from repository root:

```bash
./.venv/bin/python -m alembic -c services/api/alembic.ini upgrade head
```

If using an explicit DB target:

```bash
DATABASE_URL=sqlite:////opt/TAAIP/data/taaip.sqlite3 ./.venv/bin/python -m alembic -c services/api/alembic.ini upgrade head
```

## 4) Backend Startup (Repeatable)

Preflight + local process startup:

```bash
zsh scripts/taaip_preflight.sh
./start-taaip-local.sh
```

PM2 startup:

```bash
./start-taaip.sh
```

Systemd example:
- `deploy/taaip.service.example` uses:
  - `ExecStartPre=/usr/bin/env zsh /opt/TAAIP/scripts/taaip_preflight.sh`
  - `ExecStart=/opt/TAAIP/.venv/bin/python -m uvicorn services.api.app.main:app ...`

## 5) Frontend Startup and Build

Development frontend startup:

```bash
cd taaip-dashboard
npm run dev -- --host 127.0.0.1 --port 5173
```

Production build verification:

```bash
cd taaip-dashboard
npm run build
```

## 6) Admin Refresh Path (Controlled)

Authoritative refresh routes:
- `GET /api/refresh/sources`
- `POST /api/refresh/sources`
- `POST /api/refresh/sources/{source_id}/upload`
- `POST /api/refresh/jobs/{job_id}/commit`

Safety contract:
- Admin-only via `admin.permissions.manage`.
- Invalid schema returns structured `invalid_schema` errors.
- Empty uploads return structured `no_data` errors.
- Failed validation does not rebind `dataset_active`.

## 7) Release Validation Commands

Run from repository root:

```bash
./.venv/bin/python -m pytest -q services/api/tests/test_refresh_admin_workflow.py services/api/tests/test_runtime_preflight_contract.py
./.venv/bin/python services/api/scripts/runtime_preflight.py --ensure-schema
zsh -n start-taaip.sh start-taaip-local.sh run-dev.sh scripts/taaip_preflight.sh
```

Run frontend checks:

```bash
cd taaip-dashboard
npm test
npm run build
```

## 8) Handoff Checklist

- Runtime preflight returns `status: ok`.
- Backend and frontend start on expected ports.
- Commander and 420T perspectives do not expose admin console.
- Admin refresh routes return 403 for non-admin users.
- Documentation set for sustainment and demo runbook is delivered.
