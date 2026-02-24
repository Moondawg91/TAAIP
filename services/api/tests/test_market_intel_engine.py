import json
import sqlite3
from fastapi.testclient import TestClient
from services.api.app.main import app
from services.api.app.db import connect

client = TestClient(app)


def test_engine_endpoints_empty_safe():
    endpoints = [
        '/api/market-intel/summary',
        '/api/market-intel/demographics',
        '/api/market-intel/categories',
        '/api/market-intel/export/targets.csv'
    ]
    for ep in endpoints:
        r = client.get(ep)
        assert r.status_code == 200
        # summary/demographics/categories return JSON, export returns CSV header
        if ep.endswith('.csv'):
            txt = r.text
            assert txt.startswith('fy,qtr,rsid_prefix,zip,cbsa,market_category')
        else:
            data = r.json()
            assert 'status' in data
            assert 'missing_data' in data


def test_engine_basic_calculations():
    conn = connect()
    cur = conn.cursor()
    # insert one zip row and one cbsa row and one target
    demo = json.dumps({'race': {'groupA': 30, 'groupB': 20}})
    # Insert rows using only columns that exist in the current test DB schema
    def _insert_min(table, desired_values):
        cur.execute(f"PRAGMA table_info('{table}')")
        existing = [r[1] for r in cur.fetchall()]
        cols = [c for c in desired_values.keys() if c in existing]
        vals = [desired_values[c] for c in cols]
        if not cols:
            return
        placeholders = ','.join(['?'] * len(cols))
        col_list = ','.join(cols)
        sql = f"INSERT OR REPLACE INTO {table}({col_list}) VALUES ({placeholders})"
        cur.execute(sql, tuple(vals))

    _insert_min('market_zip_fact', {
        'id': 'z1', 'fy': 2026, 'qtr': 'Q1', 'rsid_prefix': 'RS1', 'zip5': '12345', 'cbsa_code': 'CB1', 'market_category': 'MK', 'fqma': 100, 'potential_remaining': 90, 'p2p': 0.5, 'demo_json': demo, 'ingested_at': '2026-02-23T00:00:00Z'
    })
    _insert_min('market_cbsa_fact', {
        'id': 'c1', 'fy': 2026, 'qtr': 'Q1', 'rsid_prefix': 'RS1', 'cbsa_code': 'CB1', 'cbsa_name': 'MetroX', 'market_category': 'MK', 'fqma': 100, 'potential_remaining': 90, 'demo_json': json.dumps({'race':{'groupA':30}}), 'ingested_at': '2026-02-23T00:00:00Z'
    })
    _insert_min('market_targets', {
        'id': 't1', 'fy': 2026, 'qtr': 'Q1', 'rsid_prefix': 'RS1', 'target_type': 'must_keep', 'zip': '12345', 'cbsa_code': 'CB1', 'rationale': 'rationale', 'score': 0.9, 'created_at': '2026-02-23T00:00:00Z', 'ingested_at': '2026-02-23T00:00:00Z'
    })
    conn.commit()

    r = client.get('/api/market-intel/summary?fy=2026')
    assert r.status_code == 200
    data = r.json()
    # basic presence checks (schema may vary between environments)
    # ensure categories data present
    cats = data.get('kpis', {}).get('categories', {})
    assert cats.get('MK', 0) >= 1

    # CSV export returns header + row
    r2 = client.get('/api/market-intel/export/targets.csv?fy=2026')
    assert r2.status_code == 200
    txt = r2.text
    assert txt.startswith('fy,qtr,rsid_prefix,zip,cbsa,market_category')
    # ensure target id may appear in exported csv rows when mapping from market_targets exists
    assert '12345' in txt or 't1' in txt
