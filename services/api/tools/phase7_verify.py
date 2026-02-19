#!/usr/bin/env python3
"""Phase-7 verification checklist script.
Performs lightweight checks: route presence, basic endpoint responses, imports, RBAC helpers, and a budget rollup smoke test.
"""
import os
import json
from fastapi.testclient import TestClient

os.environ.setdefault('LOCAL_DEV_AUTH_BYPASS', '1')
os.environ.setdefault('TAAIP_DB_PATH', './taaip_phase7.db')

REPORT = {
    'routes': {},
    'endpoints': {},
    'imports': {},
    'rbac': {},
    'budget_rollup': {},
}

# Imports
modules = [
    'services.api.app.main',
    'services.api.app.db',
    'services.api.app.routers.v2',
    'services.api.app.routers.rbac',
    'services.api.app.models',
]
for m in modules:
    try:
        __import__(m)
        REPORT['imports'][m] = 'ok'
    except Exception as e:
        REPORT['imports'][m] = f'error: {e}'

# App + routes
try:
    from services.api.app.main import app
    client = TestClient(app)
    routes = [r.path for r in app.routes]
    REPORT['routes']['count'] = len(routes)
    REPORT['routes']['has_loes'] = '/api/v2/loes' in routes
    REPORT['routes']['has_marketing_activities'] = '/api/v2/marketing/activities' in routes
    REPORT['routes']['has_funnel_stages'] = '/api/v2/funnel/stages' in routes
    REPORT['routes']['has_burden_latest'] = '/api/v2/burden/latest' in routes
except Exception as e:
    REPORT['routes'] = {'error': str(e)}
    client = None

# Basic endpoint checks (non-destructive)
if client:
    try:
        r = client.get('/api/v2/funnel/stages')
        REPORT['endpoints']['funnel/stages'] = {'status': r.status_code, 'body': r.json()}
    except Exception as e:
        REPORT['endpoints']['funnel/stages'] = {'error': str(e)}
    try:
        r = client.get('/api/v2/marketing/sources')
        REPORT['endpoints']['marketing/sources'] = {'status': r.status_code, 'body': r.json()}
    except Exception as e:
        REPORT['endpoints']['marketing/sources'] = {'error': str(e)}
    try:
        r = client.get('/api/v2/kpis', params={'event_id': 'evt_dummy'})
        REPORT['endpoints']['kpis'] = {'status': r.status_code, 'body': r.json()}
    except Exception as e:
        REPORT['endpoints']['kpis'] = {'error': str(e)}

# RBAC smoke
try:
    from services.api.app.routers import rbac
    REPORT['rbac']['has_get_current_user'] = hasattr(rbac, 'get_current_user')
    REPORT['rbac']['has_require_roles'] = hasattr(rbac, 'require_roles')
except Exception as e:
    REPORT['rbac'] = {'error': str(e)}

# Budget rollup smoke: create a budget and sum
try:
    # initialize DB schema for this check
    from services.api.app.db import init_db, get_db_conn
    init_db()
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO budgets(budget_id,event_id,campaign_name,allocated_amount,created_at,record_status) VALUES(?,?,?,?,?,?)", ('b1','evt_x','camp',100.0,'2026-01-01','active'))
    conn.commit()
    cur.execute("SELECT SUM(allocated_amount) FROM budgets WHERE event_id=?", ('evt_x',))
    s = cur.fetchone()
    total = float((s[0] or 0.0))
    REPORT['budget_rollup'] = {'inserted': True, 'sum': total}
    conn.close()
except Exception as e:
    REPORT['budget_rollup'] = {'error': str(e)}

print(json.dumps(REPORT, indent=2))
