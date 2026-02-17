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
- The project uses SQLAlchemy and creates tables automatically on startup for local dev.
- For Postgres in production, set `DATABASE_URL` env var and run Alembic (alembic support is scaffolded in requirements).

## Phase 1 - Local Dev & Testing

### Environment Variables

```bash
export DATABASE_URL="sqlite:///./services/api/taaip_dev.db"
export JWT_SECRET="devsecret"
export PYTHONPATH="$(pwd)"
```

### Run Migrations

```bash
cd services/api
alembic upgrade head
```

### Run API

```bash
uvicorn app.main:app --reload
```

API Health Check:

```
GET http://localhost:8000/health
```

## Seeding and Imports (important — no demo data)

This service does NOT seed demo or synthetic operational data. Only system defaults and reference tables are safe to seed.

1) Seed system defaults (idempotent):

```bash
python services/api/scripts/seed_defaults.py
```

This will create only the `market_category_weights` defaults and `funnel_stages` baseline. It will not create events, metrics, funnel transitions, burden inputs, LOEs, or station/ZIP coverage.

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

