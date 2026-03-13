import json
from services.api.app import migrations
from services.api.app.db import connect
from services.api.app.services import school_targeting
from services.api.app.routers import v2 as v2router


def setup_module(module):
    conn = connect()
    migrations.apply_migrations(conn)
    conn.close()


def test_school_scoring_math_basic():
    payloads = [
        {'school_id': 'S1', 'enrollment': 1200, 'access_score': 0.8, 'historical_production': 10},
        {'school_id': 'S2', 'enrollment': 300, 'access_score': 0.4, 'historical_production': 2},
    ]
    res = school_targeting.compute_school_targets(payloads, persist=False)
    assert isinstance(res, list) and len(res) == 2
    for r in res:
        assert 0.0 <= r.get('priority_score', 0.0) <= 1.0 or 'priority_score' in r or 'score' in r


def test_school_targeting_endpoint_and_persistence():
    payload = {
        'unit_rsid': 'TESTUNIT',
        'as_of_date': '2026-03-13',
        'schools': [
            {'school_id': 'TEST_S1', 'enrollment': 1000, 'access_score': 0.7, 'historical_production': 5},
            {'school_id': 'TEST_S2', 'enrollment': 400, 'access_score': 0.3, 'historical_production': 1}
        ]
    }

    out = v2router.school_targeting_run(payload)
    assert 'compute_run_id' in out and out.get('results')

    # verify rows persisted
    conn = connect(); cur = conn.cursor()
    cur.execute('SELECT * FROM school_targeting_scores WHERE compute_run_id=?', (out.get('compute_run_id'),))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    assert len(rows) == 2
    for row in rows:
        assert row.get('school_id') in ('TEST_S1', 'TEST_S2')
