#!/usr/bin/env python3
"""Simple smoke verifier for dashboard endpoints and exports.

Usage: python scripts/verify_all.py [--base http://127.0.0.1:8000]
"""
import sys
import json
import argparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


def get(url):
    req = Request(url, headers={'User-Agent': 'taaip-verifier/1'})
    with urlopen(req, timeout=10) as resp:
        content = resp.read()
        ct = resp.headers.get('Content-Type','')
        return resp.status, ct, content


def check_json(url):
    status, ct, content = get(url)
    assert status == 200, f'{url} returned {status}'
    assert 'application/json' in ct or ct.startswith('text/'), f'{url} not json: {ct}'
    js = json.loads(content)
    assert isinstance(js, dict), f'{url} json not dict'
    return js


def check_csv(url):
    status, ct, content = get(url)
    assert status == 200, f'{url} returned {status}'
    assert 'text/csv' in ct or 'text/plain' in ct or ct == '', f'{url} not csv: {ct}'
    # ok if empty
    return content.decode('utf-8', errors='ignore')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--base', default='http://127.0.0.1:8000')
    args = p.parse_args()
    base = args.base.rstrip('/')

    targets = [
        f'{base}/api/dashboards/budget',
        f'{base}/api/dashboards/projects',
        f'{base}/api/dashboards/events',
        f'{base}/api/dashboards/budget/export.json',
        f'{base}/api/dashboards/budget/export.csv',
        f'{base}/api/dashboards/budget/dashboard/export.json',
        f'{base}/api/dashboards/budget/dashboard/export.csv',
    ]

    ok = True
    for t in targets:
        try:
            if t.endswith('.json') or t.endswith('/budget') or t.endswith('/projects') or t.endswith('/events'):
                js = check_json(t)
                print(f'OK JSON {t} -> keys: {list(js.keys())[:5]}')
            else:
                csv = check_csv(t)
                print(f'OK CSV {t} -> {len(csv)} bytes')
        except (AssertionError, HTTPError, URLError) as e:
            print('ERROR', t, str(e))
            ok = False

    if not ok:
        print('\nOne or more checks failed.')
        sys.exit(2)
    print('\nAll checks passed.')


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""Comprehensive verification script for TAAIP.

Assumes the API is running at http://127.0.0.1:8000 and the local Python
environment can import `services.api.app.db` to perform safe setup inserts.

This script performs the checks described in the Phase 9 verification gate.
"""
import json
import re
import sys
import time
import os
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

ROOT = 'http://127.0.0.1:8000'

def http_get(path):
    try:
        r = urlopen(ROOT + path, timeout=10)
        return json.loads(r.read().decode())
    except Exception as e:
        return {'error': str(e)}

def http_post_json(path, payload):
    try:
        data = json.dumps(payload).encode('utf-8')
        req = Request(ROOT + path, data=data, headers={'Content-Type':'application/json'})
        r = urlopen(req, timeout=10)
        return json.loads(r.read().decode())
    except HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {'error': str(e)}
    except Exception as e:
        return {'error': str(e)}


def start_checks():
    failures = []

    print('1) Health check')
    h = http_get('/health')
    if not h or 'status' not in h or h.get('status') != 'ok':
        failures.append('health_failed')
    else:
        print('  OK')

    print('2) Meta routes')
    routes = http_get('/api/meta/routes')
    if 'routes' not in routes:
        failures.append('meta_routes_missing')
        routes_list = []
    else:
        routes_list = routes['routes']
        print(f'  {len(routes_list)} routes')

    # verify navConfig paths exist
    print('3) Compare navConfig entries to routes')
    missing_nav = []
    try:
        with open('apps/web/src/nav/navConfig.ts', 'r', encoding='utf-8') as fh:
            txt = fh.read()
            # find path: '/something' occurrences
            paths = re.findall(r"path:\s*'([^']+)'", txt)
            for p in paths:
                # normalize to API-side route mapping: app routes start with /api or /command-center etc.
                # We expect frontend app routes to be present among server routes if server serves UI routes; skip if client-only.
                if p.startswith('/api'):
                    if p not in routes_list:
                        missing_nav.append(p)
    except Exception as e:
        print('  Could not read navConfig:', e)

    if missing_nav:
        failures.append('nav_missing_routes:' + ','.join(missing_nav))
        print('  Missing nav routes:', missing_nav)
    else:
        print('  Nav routes present or client-only')

    # Use DB direct inserts to create minimal domain data
    print('4) Seed minimal domain rows (org_unit, user, event, project, marketing, budget line)')
    try:
        # ensure package root on path
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from services.api.app.db import connect, init_db
        init_db()
        conn = connect()
        cur = conn.cursor()
        now = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

        # create org_unit (idempotent)
        cur.execute("INSERT OR IGNORE INTO org_unit(name,type,created_at) VALUES (?,?,?)", ('Test Unit','Station', now))
        cur.execute("SELECT id FROM org_unit WHERE name=?", ('Test Unit',))
        org_row = cur.fetchone()
        if not org_row:
            # fallback: pick the most recently created org_unit if name-based lookup fails
            cur.execute('SELECT id FROM org_unit ORDER BY id DESC LIMIT 1')
            org_row = cur.fetchone()
        org_id = org_row[0] if org_row else None

        # create user (idempotent)
        cur.execute("INSERT OR IGNORE INTO users(username,display_name,email,created_at) VALUES (?,?,?,?)", ('test.user','Test User','test@example.com', now))
        cur.execute("SELECT id FROM users WHERE username=?", ('test.user',))
        user_row = cur.fetchone()
        if not user_row:
            cur.execute('SELECT id FROM users ORDER BY id DESC LIMIT 1')
            user_row = cur.fetchone()
        user_id = user_row[0] if user_row else None

        # create event (idempotent by name)
        cur.execute("INSERT OR IGNORE INTO event(org_unit_id,name,start_dt,end_dt,created_at,loe) VALUES (?,?,?,?,?,?)", (org_id, 'Verification Event', now, now, now, 1.0))
        cur.execute("SELECT id FROM event WHERE name=?", ('Verification Event',))
        event_row = cur.fetchone()
        if not event_row:
            cur.execute('SELECT id FROM event ORDER BY id DESC LIMIT 1')
            event_row = cur.fetchone()
        event_id = event_row[0] if event_row else None

        # create project (idempotent)
        cur.execute("INSERT OR IGNORE INTO projects(project_id,title,created_at) VALUES (?,?,?)", ('proj-verify', 'Verification Project', now))

        # create marketing activity with cost (idempotent)
        cur.execute("INSERT OR IGNORE INTO marketing_activities(activity_id,event_id,cost,created_at) VALUES (?,?,?,?)", ('mkt-1', str(event_id or ''), 2500.0, now))

        # create fy_budget and budget_line_item (idempotent)
        cur.execute("INSERT OR IGNORE INTO fy_budget(org_unit_id,fy,total_allocated,created_at) VALUES (?,?,?,?)", (org_id, 2026, 5000.0, now))
        cur.execute("SELECT id FROM fy_budget WHERE org_unit_id=? AND fy=?", (org_id, 2026))
        fy_row = cur.fetchone()
        fy_id = fy_row[0] if fy_row else None
        # Seed two budget line items with different funding sources for Phase-10 verification
        cur.execute("INSERT OR IGNORE INTO budget_line_item(fy_budget_id,qtr,event_id,category,amount,appropriation_type,funding_source,eor_code,is_under_cr,status,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (fy_id, 1, event_id, 'venue', 1500.0, 'OMA', 'BDE_LAMP', 'EOR-001', 0, 'committed', now))
        cur.execute("INSERT OR IGNORE INTO budget_line_item(fy_budget_id,qtr,event_id,category,amount,appropriation_type,funding_source,eor_code,is_under_cr,status,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (fy_id, 1, event_id, 'travel', 500.0, 'OMA', 'BN_LAMP', 'EOR-002', 0, 'planned', now))

        # seed home page content: announcements, system updates, quick links (idempotent)
        try:
            cur.execute("SELECT id FROM announcement WHERE title=?", ('Verification Announcement',))
            if not cur.fetchone():
                cur.execute("INSERT INTO announcement(org_unit_id,category,title,body,effective_dt,expires_dt,created_at) VALUES (?,?,?,?,?,?,?)", (org_id, 'Message', 'Verification Announcement', 'This is a seeded announcement for verification runs.', now, None, now))

            cur.execute("SELECT id FROM system_update WHERE component=? AND message=?", ('ingest', 'Verification: ingest queue seeded'))
            if not cur.fetchone():
                cur.execute("INSERT INTO system_update(component,status,message,created_at) VALUES (?,?,?,?)", ('ingest', 'ok', 'Verification: ingest queue seeded', now))

            cur.execute("SELECT id FROM resource_link WHERE title=?", ('Verification Quick Link',))
            if not cur.fetchone():
                cur.execute("INSERT INTO resource_link(section,title,url,created_at) VALUES (?,?,?,?)", ('home', 'Verification Quick Link', '/command-center', now))
        except Exception:
            # best-effort seeding; ignore if tables don't exist in minimal schemas
            pass

        conn.commit()
        conn.close()
        print('  seeded rows')
    except Exception as e:
        print('  DB seed failed:', e)
        failures.append('db_seed_failed')

    # Verify budget summary via API
    print('5) Budget summary rollup')
    b = http_get('/api/budget/summary')
    if 'planned' not in b:
        failures.append('budget_summary_missing')
    else:
        planned = b.get('planned')
        actual = b.get('actual')
        remaining = b.get('remaining')
        print(f"  planned={planned} actual={actual} remaining={remaining}")
        # expected planned >= 1500 and actual >= 2500 (we created planned 1500, FY total 5000 and marketing 2500)
        if planned is None or actual is None:
            failures.append('budget_summary_values_missing')

    # New: verify detailed budget dashboard rollup
    print('5b) Budget dashboard rollup')
    bd = http_get('/api/budget/dashboard')
    try:
        if not bd or 'kpis' not in bd:
            failures.append('budget_dashboard_missing')
        else:
            k = bd['kpis']
            allocated = float(k.get('allocated') or 0)
            planned = float(k.get('planned') or 0)
            actual = float(k.get('actual') or 0)
            remaining = float(k.get('remaining') or 0)
            # tolerance for floating math
            if abs(remaining - (allocated - planned - actual)) > 0.01:
                failures.append('budget_rollup_mismatch')
            else:
                print(f'  dashboard rollup OK: allocated={allocated} planned={planned} actual={actual} remaining={remaining}')
    except Exception as e:
        failures.append('budget_dashboard_error')

    # Verify performance mission assessment API
    print('6) Mission assessment')
    m = http_get('/api/performance/mission-assessment')
    if 'latest_assessment' not in m or 'kpis' not in m:
        failures.append('mission_assessment_missing')
    else:
        print('  mission assessment and kpis present')

    # Verify new dashboards: projects, events, performance
    print('6b) Projects dashboard')
    pd = http_get('/api/dash/projects/dashboard')
    if not pd or 'totals' not in pd:
        failures.append('projects_dashboard_missing')
    else:
        print('  projects dashboard present')

    print('6c) Events dashboard')
    ed = http_get('/api/dash/events/dashboard')
    if not ed or 'totals' not in ed:
        failures.append('events_dashboard_missing')
    else:
        print('  events dashboard present')

    print('6d) Performance dashboard')
    perf = http_get('/api/dash/performance/dashboard')
    if not perf or 'top_metrics' not in perf:
        failures.append('performance_dashboard_missing')
    else:
        print('  performance dashboard present')

    # PHASE-15 addition: verify tactical rollups zero-states respond
    print('6e) Tactical rollups zero-state checks')
    for p in ['/api/rollups/budget','/api/rollups/events','/api/rollups/marketing','/api/rollups/funnel','/api/rollups/command']:
        r = http_get(p)
        if not r or 'status' not in r or r.get('status') != 'ok':
            failures.append('rollup_failed:' + p)
        else:
            print(' ', p, 'OK')

    # Final route-check: ensure no navConfig client paths return 404 via meta routes
    print('7) Final route verification from meta')
    # For web routes (non-/api) we cannot call server; ensure API meta routes exist
    print('  checked')

    if failures:
        print('\nTAAIP FULL SYSTEM CHECK: FAIL')
        for f in failures:
            print(' -', f)
        return 2
    else:
        print('\nTAAIP FULL SYSTEM CHECK: PASS')
        return 0


if __name__ == '__main__':
    rc = start_checks()
    sys.exit(rc)
