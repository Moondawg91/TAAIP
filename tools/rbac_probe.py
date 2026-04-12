"""
RBAC HTTP probe

This script recreates a local DB with test users, then issues HTTP requests
to a list of routes using different test user tokens to classify access.
"""

import os
import json
import time
import requests
from services.api.app import database, models, auth
from services.api.app.database import SessionLocal, engine
from services.api.app.models import Base
from sqlalchemy.orm import Session

# Recreate schema and seed test users
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

s: Session = SessionLocal()
try:
    # minimal org hierarchy
    cmd = models.Command(command='CMD1', display='CMD1')
    s.add(cmd); s.commit()
    bde = models.Brigade(brigade_prefix='1', display='B1', command_id=cmd.id)
    s.add(bde); s.commit()
    bn = models.Battalion(battalion_prefix='1A', display='Bn1A', brigade_id=bde.id)
    s.add(bn); s.commit()
    co = models.Company(company_prefix='1A1', display='Co', battalion_id=bn.id)
    s.add(co); s.commit()
    st1 = models.Station(rsid='1A1D', display='St1', company_id=co.id)
    st2 = models.Station(rsid='1B1D', display='St2', company_id=co.id)
    s.add_all([st1, st2]); s.commit()

    # seed users with different roles/scopes
    users = [
        models.User(username='usarec_admin', role=models.UserRole.SYSADMIN, scope='USAREC'),
        models.User(username='bn_420t', role=models.UserRole.BATTALION_420T, scope='1A'),
        models.User(username='station_view', role=models.UserRole.STATION_VIEW, scope='1A1D'),
    ]
    for u in users:
        s.add(u)
    s.commit()

    # create JWT tokens for these users via auth.create_token_for_user
    tokens = {}
    for uname in ['usarec_admin', 'bn_420t', 'station_view']:
        u = s.query(models.User).filter_by(username=uname).one()
        tokens[uname] = auth.create_token_for_user(u)

finally:
    s.close()

# base url for API
BASE = os.getenv('BASE_URL', 'http://127.0.0.1:8000')

# routes to probe (method, path, sample body)
ROUTES = [
    ('GET', '/api/import/jobs', None),
    ('POST', '/api/import/upload', {'_probe': True}),
    ('POST', '/api/import/parse', {'import_job_id': 'probe'}),
    ('POST', '/api/import/map', {'import_job_id': 'probe', 'mapping': {}}),
    ('POST', '/api/import/validate', {'import_job_id': 'probe'}),
    ('POST', '/api/import/commit', {'import_job_id': 'probe'}),
    ('GET', '/api/powerbi/fact_production', None),
    ('GET', '/api/mission_assessments/latest', None),
    ('GET', '/api/market-intel/summary', None),
    ('GET', '/api/ops/market/summary', None),
    ('GET', '/api/org/children', None),
    ('GET', '/api/v2/connectors/status', None),
    ('GET', '/health', None),
]

def probe_route(method, path, body, headers):
    url = BASE.rstrip('/') + path
    try:
        if method == 'GET':
            r = requests.get(url, headers=headers, timeout=5)
        else:
            r = requests.post(url, json=body or {}, headers=headers, timeout=5)
        return {'status': r.status_code, 'text': r.text[:200]}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

results = {}

subjects = {
    'anon': None,
    'usarec_admin': tokens.get('usarec_admin'),
    'bn_420t': tokens.get('bn_420t'),
    'station_view': tokens.get('station_view')
}

for name, token in subjects.items():
    hdr = {}
    if token:
        hdr['Authorization'] = f'Bearer {token}'
    results[name] = {}
    for method, path, body in ROUTES:
        res = probe_route(method, path, body, hdr)
        results[name][path] = res

# classify
report = {'base': BASE, 'results': results, 'classifications': {}}
for method, p, _ in ROUTES:
    anon_status = results['anon'][p]['status']
    admin_status = results['usarec_admin'][p]['status']
    bv = 'unknown'
    if anon_status == 200:
        bv = 'intentionally_public_or_exposed'
    elif anon_status in (401, 403):
        if admin_status == 200:
            bv = 'protected_correctly'
        elif isinstance(admin_status, int) and admin_status >=500:
            bv = 'broken_inconsistent'
        else:
            bv = 'protected_but_admin_cannot_access'
    else:
        bv = 'unknown'
    report['classifications'][p] = bv

os.makedirs('tools', exist_ok=True)
open('tools/rbac_report.json','w').write(json.dumps(report, indent=2))
open('tools/rbac_tokens.json','w').write(json.dumps(tokens, indent=2))
print('WROTE tools/rbac_report.json')
