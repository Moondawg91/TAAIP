#!/usr/bin/env python3
import os, json, datetime
os.environ['TAAIP_DB_PATH'] = os.getenv('TAAIP_DB_PATH', './taaip_dev.db')
from services.api.app import db
from services.api.app.routers import maintenance
from pprint import pprint

print('DB path:', db.get_db_path())
conn = db.connect()
cur = conn.cursor()
params = {'tasks': ['dedupe', 'purge'], 'days': 7}
created = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
cur.execute('INSERT INTO maintenance_schedules(name, enabled, interval_minutes, params_json, created_at) VALUES (?,?,?,?,?)', ('auto-maint-assistant', 1, 1, json.dumps(params), created))
conn.commit()
sid = cur.lastrowid
print('Inserted schedule id', sid)
conn.close()

admin_user = {'username': 'dev.user', 'roles': ['usarec_admin'], 'scopes': []}
print('\nTriggering schedule via maintenance.trigger_schedule...')
try:
    res = maintenance.trigger_schedule(sid, current_user=admin_user)
    pprint(res)
except Exception as e:
    print('trigger error', e)

print('\nRunning deduplicate_business_keys...')
try:
    ded = maintenance.deduplicate_business_keys(current_user=admin_user)
    pprint(ded)
except Exception as e:
    print('dedupe error', e)

print('\nRunning purge_archived...')
try:
    pur = maintenance.purge_archived(days=90, tables=None, current_user=admin_user)
    pprint(pur)
except Exception as e:
    print('purge error', e)

print('\nRecent maintenance_runs:')
conn = db.connect()
cur = conn.cursor()
cur.execute('SELECT id, schedule_id, run_type, params_json, result_json, started_at, finished_at FROM maintenance_runs ORDER BY id DESC LIMIT 20')
rows = cur.fetchall()
for r in rows:
    print(dict(r))
conn.close()
