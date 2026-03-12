from services.api.tests.test_rollups import setup_db
import sqlite3, json
import services.api.app.database as database
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from services.api.app.database import SessionLocal
from services.api.app.main import app
from fastapi.testclient import TestClient

p = setup_db()
output = {"db_path": p}
# configure SQLAlchemy
database.engine = create_engine(f"sqlite:///{p}", connect_args={"check_same_thread": False}, poolclass=NullPool)
database.SessionLocal.configure(bind=database.engine)
# insert via sqlite3
conn = sqlite3.connect(p)
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
# use lastrowid to avoid name-based lookups
org_id = cur.lastrowid
cur.execute("INSERT INTO projects(project_id,title,org_unit_id,fy,planned_cost,created_at) VALUES (?,?,?,?,?,?)", ('projA','Project A',org_id,2026,5000.0,now))
cur.execute("INSERT INTO event(org_unit_id,name,fy,planned_cost,project_id,created_at) VALUES (?,?,?,?,?,?)", (org_id,'Event A',2026,1200.0,'projA',now))
cur.execute("INSERT INTO fy_budget(org_unit_id,fy,total_allocated,created_at) VALUES (?,?,?,?)", (org_id,2026,8000.0,now))
fy_id = cur.lastrowid
cur.execute("INSERT INTO budget_line_item(fy_budget_id,qtr,event_id,category,amount,status,created_at) VALUES (?,?,?,?,?,?,?)", (fy_id,1,None,'venue',2000.0,'committed',now))
cur.execute("INSERT INTO expenses(project_id,event_id,fy,qtr,org_unit_id,amount,created_at) VALUES (?,?,?,?,?,?,?)", ('projA', None, 2026,1,org_id,400.0,now))
conn.commit()
# sqlite inspection
cur.execute('SELECT count(1) FROM projects')
output['sqlite_count'] = cur.fetchone()[0]
cur.execute('PRAGMA table_info(projects)')
output['pragma_projects'] = cur.fetchall()
conn.close()
# sqlalchemy inspection
sess = SessionLocal()
try:
    rows = sess.execute(text('SELECT project_id, title, fy, planned_cost FROM projects ORDER BY project_id')).mappings().all()
    output['sqlalchemy_rows'] = [dict(r) for r in rows]
    r = sess.execute(text('SELECT count(1) as c FROM projects WHERE fy=:fy'), {'fy':2026}).mappings().first()
    output['sqlalchemy_count_fy'] = int(r['c']) if r and r.get('c') is not None else 0
finally:
    sess.close()
# call the FastAPI route
client = TestClient(app)
resp = client.get('/api/dash/projects/dashboard?fy=2026')
output['route_status'] = resp.status_code
try:
    output['route_json'] = resp.json()
except Exception:
    output['route_text'] = resp.text
# write to file
with open('/tmp/projects_debug.json','w') as f:
    json.dump(output, f, default=str, indent=2)
print('wrote /tmp/projects_debug.json')
