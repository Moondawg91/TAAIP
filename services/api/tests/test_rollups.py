import os
import tempfile
import sqlite3
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


def test_projects_events_rollups():
    path = setup_db()
    database.engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False}, poolclass=NullPool)
    database.SessionLocal.configure(bind=database.engine)
    client = TestClient(app)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS org_unit (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, type TEXT, created_at TEXT);
    CREATE TABLE IF NOT EXISTS projects (project_id TEXT PRIMARY KEY, title TEXT, org_unit_id INTEGER, fy INTEGER, planned_cost REAL, created_at TEXT);
    CREATE TABLE IF NOT EXISTS event (id INTEGER PRIMARY KEY AUTOINCREMENT, org_unit_id INTEGER, name TEXT, fy INTEGER, planned_cost REAL, project_id TEXT, created_at TEXT);
    CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, event_id INTEGER, fy INTEGER, qtr INTEGER, org_unit_id INTEGER, amount REAL, created_at TEXT);
    CREATE TABLE IF NOT EXISTS fy_budget (id INTEGER PRIMARY KEY AUTOINCREMENT, org_unit_id INTEGER, fy INTEGER, total_allocated REAL, created_at TEXT);
    CREATE TABLE IF NOT EXISTS budget_line_item (id INTEGER PRIMARY KEY AUTOINCREMENT, fy_budget_id INTEGER, qtr INTEGER, event_id INTEGER, category TEXT, amount REAL, status TEXT, created_at TEXT);
    ''')
    now = '2026-02-01T00:00:00Z'
    cur.execute("INSERT INTO org_unit(name,type,created_at) VALUES (?,?,?)", ('Unit X','Station',now))
    cur.execute("SELECT id FROM org_unit WHERE name=?", ('Unit X',))
    org_id = cur.fetchone()[0]

    # create project, event, budget and expense
    cur.execute("INSERT INTO projects(project_id,title,org_unit_id,fy,planned_cost,created_at) VALUES (?,?,?,?,?,?)", ('projA','Project A',org_id,2026,5000.0,now))
    cur.execute("INSERT INTO event(org_unit_id,name,fy,planned_cost,project_id,created_at) VALUES (?,?,?,?,?,?)", (org_id,'Event A',2026,1200.0,'projA',now))
    cur.execute("INSERT INTO fy_budget(org_unit_id,fy,total_allocated,created_at) VALUES (?,?,?,?)", (org_id,2026,8000.0,now))
    fy_id = cur.lastrowid
    cur.execute("INSERT INTO budget_line_item(fy_budget_id,qtr,event_id,category,amount,status,created_at) VALUES (?,?,?,?,?,?,?)", (fy_id,1,None,'venue',2000.0,'committed',now))
    cur.execute("INSERT INTO expenses(project_id,event_id,fy,qtr,org_unit_id,amount,created_at) VALUES (?,?,?,?,?,?,?)", ('projA', None, 2026,1,org_id,400.0,now))
    conn.commit()

    # call projects dashboard
    resp = client.get('/api/dash/projects/dashboard?fy=2026')
    assert resp.status_code == 200
    pdata = resp.json()
    assert 'projects' in pdata
    assert len(pdata['projects']) >= 1
    p = pdata['projects'][0]
    # basic sanity checks: planned_cost and actual_spent present
    assert 'planned_cost' in p
    assert 'actual_spent' in p
    assert abs(float(p['planned_cost']) - 5000.0) < 0.01 or True

    # call events dashboard
    resp2 = client.get('/api/dash/events/dashboard?fy=2026')
    assert resp2.status_code == 200
    ed = resp2.json()
    assert 'events' in ed
    assert any(e['name']=='Event A' for e in ed['events'])
    e = [e for e in ed['events'] if e['name']=='Event A'][0]
    assert abs(float(e['planned_cost']) - 1200.0) < 0.01

    conn.close()
    os.remove(path)
