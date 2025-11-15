# TAAIP - Run & Test Instructions

Run these commands from the project root: `/Users/ambermooney/Desktop/TAAIP`

1) Activate the virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2) Install dependencies (first time or when `requirements.txt` changes)

```bash
pip install -r requirements.txt
```

3) Start the TAAIP service (background)

```bash
source .venv/bin/activate
nohup python3 taaip_service.py > service.log 2>&1 &
tail -f service.log
```

4) Run the automated tests (uses FastAPI TestClient)

```bash
source .venv/bin/activate
pytest -q test_taaip_marketing.py
```

5) Open the dashboard prototype

Serve the `dashboard/` folder (simple option using Python):

```bash
cd dashboard
python3 -m http.server 8080
# Then open http://localhost:8080 in your browser
```

6) Run mock syncs for EMM/iKrome

```bash
source .venv/bin/activate
python3 mocks/mock_sources.py
```

Notes:
- The tests create a fresh `data/taaip.sqlite3` database for test runs by removing any
  existing DB before initializing; production data will remain unless explicitly removed.
- The dashboard prototype is intentionally simple (static HTML + JS) and calls the
  running TAAIP service at `http://localhost:8000`.
