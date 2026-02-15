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
