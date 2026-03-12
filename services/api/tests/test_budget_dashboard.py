import os
import tempfile
import sqlite3
import json
import pathlib
import sys
from fastapi.testclient import TestClient

# ensure repo root on path
ROOT = str(pathlib.Path(__file__).resolve().parents[3])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.api.app.main import app
from services.api.app import db as tdb
import services.api.app.database as database
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool


def setup_db():
    fd, path = tempfile.mkstemp(prefix='taaip_test_', suffix='.sqlite3')
    os.close(fd)
    os.environ['TAAIP_DB_PATH'] = path
    os.environ['LOCAL_DEV_AUTH_BYPASS'] = '1'
    tdb.init_db()
    return path


def test_budget_dashboard_kpis_and_csv():
    path = setup_db()
    # ensure SQLAlchemy engine used by app points to our temp DB
    database.engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False}, poolclass=NullPool)
    database.SessionLocal.configure(bind=database.engine)
    client = TestClient(app)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # Ensure minimal tables exist in case init_db didn't run against this path
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS org_unit (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, type TEXT, created_at TEXT);
    CREATE TABLE IF NOT EXISTS fy_budget (id INTEGER PRIMARY KEY AUTOINCREMENT, org_unit_id INTEGER, fy INTEGER, total_allocated REAL, created_at TEXT);
    CREATE TABLE IF NOT EXISTS budget_line_item (id INTEGER PRIMARY KEY AUTOINCREMENT, fy_budget_id INTEGER, qtr INTEGER, event_id INTEGER, category TEXT, amount REAL, status TEXT, created_at TEXT);
    CREATE TABLE IF NOT EXISTS projects (project_id TEXT PRIMARY KEY, title TEXT, org_unit_id INTEGER, fy INTEGER, planned_cost REAL, created_at TEXT);
    CREATE TABLE IF NOT EXISTS event (id INTEGER PRIMARY KEY AUTOINCREMENT, org_unit_id INTEGER, name TEXT, fy INTEGER, planned_cost REAL, created_at TEXT);
    CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, event_id INTEGER, fy INTEGER, qtr INTEGER, org_unit_id INTEGER, amount REAL, created_at TEXT);
    ''')
    now = '2026-02-01T00:00:00Z'
    # create org_unit and use lastrowid to avoid name-based lookups
    cur.execute("INSERT INTO org_unit(name,type,created_at) VALUES (?,?,?)", ('Test Unit', 'Station', now))
    org_id = cur.lastrowid
    # create fy_budget and line
    cur.execute("INSERT INTO fy_budget(org_unit_id,fy,total_allocated,created_at) VALUES (?,?,?,?)", (org_id, 2026, 10000.0, now))
    fy_id = cur.lastrowid
    cur.execute("INSERT INTO budget_line_item(fy_budget_id,qtr,event_id,category,amount,status,created_at) VALUES (?,?,?,?,?,?,?)", (fy_id, 1, None, 'venue', 1500.0, 'committed', now))
    # create project and event with planned_cost
    cur.execute("INSERT INTO projects(project_id,title,org_unit_id,fy,planned_cost,created_at) VALUES (?,?,?,?,?,?)", ('p1', 'Proj 1', org_id, 2026, 2000.0, now))
    cur.execute("INSERT INTO event(org_unit_id,name,fy,planned_cost,created_at) VALUES (?,?,?,?,?)", (org_id, 'Evt 1', 2026, 500.0, now))
    # create expense
    cur.execute("INSERT INTO expenses(project_id,event_id,fy,qtr,org_unit_id,amount,created_at) VALUES (?,?,?,?,?,?,?)", ('p1', None, 2026, 1, org_id, 300.0, now))
    conn.commit()

    # call dashboard JSON
    resp = client.get('/api/budget/dashboard?fy=2026')
    assert resp.status_code == 200
    data = resp.json()
    # new shape uses total_planned/total_spent/total_remaining
    assert 'total_planned' in data
    assert 'total_spent' in data
    # allocated equals sum of budget_line_item (1500) and unlinked (none)
    # planned = projects + events = 2000 + 500 = 2500
    assert abs(float(data.get('total_planned') or 0) - 2500.0) < 0.01
    assert abs(float(data.get('total_spent') or 0) - 300.0) < 0.01

    # CSV export
    resp2 = client.get('/api/budget/dashboard/export.csv?fy=2026')
    assert resp2.status_code == 200
    assert resp2.headers.get('content-type', '').startswith('text/csv')
    text = resp2.text
    # CSV contains metric rows like total_planned or total_spent
    assert 'total_planned' in text or 'planned' in text

    conn.close()
    os.remove(path)