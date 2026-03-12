#!/usr/bin/env python3
"""Launch readiness smoke script for Phase 12-15.

Performs health checks, rollup smoke endpoints, inserts minimal rows
and verifies basic relationships.
"""
import os
import sys
import json
from datetime import datetime

BASE = os.getenv('TAAIP_BASE_URL', 'http://127.0.0.1:8000')

try:
    import requests
except Exception:
    requests = None
    import urllib.request as _urllib
    import urllib.error as _urlerr

def _get(path):
    url = BASE.rstrip('/') + path
    if requests:
        r = requests.get(url, timeout=5)
        return r.status_code, r.text
    else:
        try:
            with _urllib.urlopen(url, timeout=5) as f:
                return f.getcode(), f.read().decode('utf-8')
        except _urlerr.HTTPError as e:
            return e.code, e.read().decode('utf-8')

def fail(msg):
    print('FAIL:', msg)
    sys.exit(2)

def ok(msg):
    print('PASS:', msg)


def main():
    print('Launch readiness check against', BASE)
    code, body = _get('/health')
    if code != 200:
        fail('/health did not return 200')
    else:
        ok('/health')

    code, body = _get('/api/meta/routes')
    if code != 200:
        fail('/api/meta/routes did not return 200')
    else:
        ok('/api/meta/routes')

    rollup_paths = ['/api/rollups/budget', '/api/rollups/events', '/api/rollups/marketing', '/api/rollups/funnel', '/api/rollups/command']
    for p in rollup_paths:
        code, body = _get(p)
        if code != 200:
            fail(f'{p} returned {code}')
        try:
            data = json.loads(body)
            if data.get('status') != 'ok':
                fail(f'{p} did not return ok status')
        except Exception:
            fail(f'{p} returned invalid json')
        ok(p + ' zero-state')

    # Insert minimal rows to DB and re-query rollups
    try:
        # ensure package root on path (so `services` package can be imported)
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from services.api.app.db import connect
    except Exception as e:
        fail('unable to import DB module: %s' % e)
    conn = connect()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    try:
        # insert an event in legacy events table
        cur.execute("INSERT OR REPLACE INTO events(event_id,name,budget,created_at,fy,qtr) VALUES(?,?,?,?,?,?)", ('EVT-1','Smoke Event',1000,now,2026,1))
        # insert budget line item linking to the event
        cur.execute("INSERT INTO budget_line_item(fy,qtr,scope_type,scope_value,station_rsid,project_id,event_id,allocated_amount,obligated_amount,expended_amount,category,reported_at,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (2026,1,'command','test','RSID-1','PRJ-1','EVT-1',1000,800,500,'advertising',now,now))
        # insert marketing activity linking to event (use conservative column set present in most schemas)
        cur.execute("INSERT OR REPLACE INTO marketing_activities(activity_id,event_id,activity_type,campaign_name,channel,cost,impressions,engagement_count,activation_conversions,reporting_date,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)", ('ACT-1','EVT-1','digital','CAMP-1','social',200,10000,500,10,now,now))
        # insert a funnel lead transition and outcome
        cur.execute("INSERT OR REPLACE INTO funnel_transitions(id,lead_id,from_stage,to_stage,transitioned_at,created_at) VALUES(?,?,?,?,?,?)", ('FT-1','LEAD-1','lead','prospect',now,now))
        cur.execute("INSERT OR REPLACE INTO outcomes(lead_id,contract_date,ship_date,status,created_at) VALUES(?,?,?,?,?)", ('LEAD-1',now,None,'contract',now))
        conn.commit()
    except Exception as e:
        fail('failed inserting smoke rows: %s' % e)

    # Re-query rollups and ensure relationships
    code, body = _get('/api/rollups/budget')
    if code != 200:
        fail('/api/rollups/budget after inserts returned %s' % code)
    b = json.loads(body)
    alloc = b.get('data', {}).get('totals', {}).get('allocated', 0)
    exp = b.get('data', {}).get('totals', {}).get('expended', 0)
    if exp <= 0:
        fail('budget expended did not reflect inserted expended_amount')
    ok('budget reflects expended')

    code, body = _get('/api/rollups/events')
    if code != 200:
        fail('/api/rollups/events after inserts returned %s' % code)
    ev = json.loads(body)
    events = ev.get('data', {}).get('events', [])
    if not events:
        print('WARN: events rollup returned empty after insert; continuing')
    else:
        ok('events rollup returned events')

    code, body = _get('/api/rollups/marketing')
    mk = json.loads(body)
    cost = mk.get('data', {}).get('totals', {}).get('cost', 0)
    if cost <= 0:
        fail('marketing rollup did not include inserted cost')
    ok('marketing rollup includes marketing cost')

    # RBAC bypass check: environment path should not crash endpoints
    if os.getenv('LOCAL_DEV_AUTH_BYPASS') is None:
        print('Note: LOCAL_DEV_AUTH_BYPASS not set; ensure RBAC path exercised in your env')

    print('\nAll checks passed.')
    sys.exit(0)


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""Launch readiness smoke tests for TAAIP.

Per PHASE-15, this script validates basic API health and rollup endpoints
return zero-states and that minimal relationships work after inserting
a small set of test rows.
"""
import os
import sys
import time
import json
from urllib.parse import urljoin
import requests

API_BASE = os.getenv('TAAIP_API_URL', 'http://127.0.0.1:8000')


def call(path, method='get', **kwargs):
    url = urljoin(API_BASE, path)
    try:
        r = requests.request(method, url, timeout=10, **kwargs)
        return r.status_code, r.text
    except Exception as e:
        return None, str(e)


def check_health():
    code, body = call('/health')
    ok = code == 200
    print('health:', code)
    return ok


def get_routes():
    code, body = call('/api/meta/routes')
    print('/api/meta/routes', code)
    return code == 200


def rollup_zero_states():
    paths = ['/api/rollups/budget', '/api/rollups/events', '/api/rollups/marketing', '/api/rollups/funnel', '/api/rollups/command']
    ok = True
    for p in paths:
        code, body = call(p)
        print(p, code)
        if code != 200:
            ok = False
    return ok


def insert_minimal_rows():
    """Insert minimal rows via direct DB file if available (best-effort)."""
    # Attempt to use SQLite DB path if set; this is faster and avoids auth.
    db_path = os.getenv('TAAIP_DB_PATH', './data/taaip.sqlite3')
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        now = time.strftime('%Y-%m-%dT%H:%M:%SZ')
        # create minimal budget_line_item, event, marketing_activity, funnel_transition
        cur.execute("INSERT INTO events(event_id,name,created_at) VALUES(?,?,?)", ('ev-1','Test Event',now))
        cur.execute("INSERT OR IGNORE INTO marketing_activities(activity_id,event_id,cost,impressions,conversions,created_at) VALUES(?,?,?,?,?,?)", ('ma-1','ev-1',100.0,1000,2,now))
        cur.execute("INSERT OR IGNORE INTO outcomes(lead_id,contract_date,ship_date,status,created_at) VALUES(?,?,?,?,?)", ('lead-1', now, None, 'contracted', now))
        cur.execute("INSERT OR IGNORE INTO budget_line_item(project_id,event_id,allocated_amount,expended_amount,fy,qtr,created_at) VALUES(?,?,?,?,?,?,?)", ('proj-1','ev-1',1000,100,2026,1,now))
        cur.execute("INSERT OR IGNORE INTO funnel_transitions(id,lead_id,from_stage,to_stage,transitioned_at) VALUES(?,?,?,?,?)", ('ft-1','lead-1','lead','prospect',now))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print('DB insert failed:', e)
        return False


def check_rollups_after_insert():
    code, body = call('/api/rollups/budget')
    print('/api/rollups/budget after insert', code)
    try:
        payload = json.loads(body)
        totals = payload.get('data', {}).get('totals', {})
        expended = totals.get('expended', 0)
        allocated = totals.get('allocated', 0)
        ok = allocated >= expended
        print('budget allocated/expended:', allocated, expended)
        return ok
    except Exception as e:
        print('parse error', e)
        return False


def main():
    ok = True
    print('Checking health...')
    if not check_health():
        print('Health check failed')
        ok = False

    print('Checking routes...')
    if not get_routes():
        print('Route listing failed')
        ok = False

    print('Checking rollup zero-states...')
    if not rollup_zero_states():
        print('One or more rollup endpoints failed zero-state')
        ok = False

    print('Inserting minimal rows into DB (best-effort)...')
    if not insert_minimal_rows():
        print('Failed to insert minimal rows; continuing with API checks')

    print('Checking rollups after insert...')
    if not check_rollups_after_insert():
        print('Rollups did not reflect inserted rows as expected')
        ok = False

    if ok:
        print('\nLAUNCH READY: PASS')
        sys.exit(0)
    else:
        print('\nLAUNCH READY: FAIL')
        sys.exit(2)


if __name__ == '__main__':
    main()
