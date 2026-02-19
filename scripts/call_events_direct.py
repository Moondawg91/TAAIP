import pathlib, sys
ROOT = str(pathlib.Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.api.tests.test_rollups import setup_db
import sqlite3
import services.api.app.database as database
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from services.api.app.routers.events_dashboard import events_dashboard

p = setup_db()
# configure engine
database.engine = create_engine(f"sqlite:///{p}", connect_args={"check_same_thread": False}, poolclass=NullPool)
database.SessionLocal.configure(bind=database.engine)
# insert rows
conn = sqlite3.connect(p)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.executescript('''
CREATE TABLE IF NOT EXISTS org_unit (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, type TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS projects (project_id TEXT PRIMARY KEY, title TEXT, org_unit_id INTEGER, fy INTEGER, planned_cost REAL, created_at TEXT);
CREATE TABLE IF NOT EXISTS event (id INTEGER PRIMARY KEY AUTOINCREMENT, org_unit_id INTEGER, name TEXT, fy INTEGER, planned_cost REAL, project_id TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, event_id INTEGER, fy INTEGER, qtr INTEGER, org_unit_id INTEGER, amount REAL, created_at TEXT);
''')
now = '2026-02-01T00:00:00Z'
cur.execute("INSERT INTO org_unit(name,type,created_at) VALUES (?,?,?)", ('Unit X','Station',now))
cur.execute("SELECT id FROM org_unit WHERE name=?", ('Unit X',))
org_id = cur.fetchone()[0]
cur.execute("INSERT INTO projects(project_id,title,org_unit_id,fy,planned_cost,created_at) VALUES (?,?,?,?,?,?)", ('projA','Project A',org_id,2026,5000.0,now))
cur.execute("INSERT INTO event(org_unit_id,name,fy,planned_cost,project_id,created_at) VALUES (?,?,?,?,?,?)", (org_id,'Event A',2026,1200.0,'projA',now))
cur.execute("INSERT INTO expenses(project_id,event_id,fy,qtr,org_unit_id,amount,created_at) VALUES (?,?,?,?,?,?,?)", ('projA', None, 2026,1,org_id,400.0,now))
conn.commit()
conn.close()
# call directly
res = events_dashboard(fy=2026)
import json
print(json.dumps(res, indent=2))
