# TAAIP Targeting & AI Service

This repository contains a small FastAPI-based microservice that simulates a Lead Scoring engine for Talent Acquisition (TAAIP).

## Files
- `taaip_service.py` - FastAPI app exposing `/api/v1/scoreLead` and `/health` endpoints.
- `requirements.txt` - Python dependencies.

## Quick start (macOS / zsh)

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the service (reload enabled):

```bash
uvicorn taaip_service:app --reload --port 8000
```

4. Open docs at `http://127.0.0.1:8000/docs` to test the endpoints.

## Endpoints
- `POST /api/v1/scoreLead` - Accepts JSON matching `LeadData` and returns a `ScoringResult`.
- `GET /health` - Returns service and model status.

Additional notes:
- The service now persists demo data to a local SQLite database at `data/taaip.sqlite3`. If there are existing `data/leads.json` or `data/pilot_state.json` files, they will be automatically migrated into the SQLite database on service startup.
- To run the API Gateway (optional, for the provided static frontend) start `node api-gateway.js` and visit the frontend at `http://127.0.0.1:3001` (if you're serving `frontend/` via a static server) or use the React scaffold in `frontend/App.jsx`.

Example run commands (in separate terminals):

```bash
# Backend (FastAPI)
source .venv/bin/activate
uvicorn taaip_service:app --reload --port 8000

# API Gateway (Node)
node api-gateway.js

# Static frontend (optional)
cd frontend
python3 -m http.server 3001
```

Auth & Docker:
- To enable simple token auth set the env var `TAAIP_API_TOKEN` (same value for gateway and backend). When set, both the gateway and FastAPI will require `Authorization: Bearer <token>` on `/api/v1/*` calls.

- Docker (quick local demo):

```bash
# Build & run both services with docker-compose (uses token `dev-token` by default)
docker compose up --build

# Then visit gateway at http://127.0.0.1:3000 and backend at http://127.0.0.1:8000
```

If you'd like, I can install dependencies and run the server now (I will run the appropriate commands in the terminal).