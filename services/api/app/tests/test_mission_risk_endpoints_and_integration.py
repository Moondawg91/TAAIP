import json
from services.api.app import migrations
from services.api.app.db import connect
from services.api.app.routers import v2 as v2router
from services.api.app.services import mission_risk_engine, mission_allocation_engine
from services.api.app.routers import v2_mission_allocation as mal_router


def setup_module(module):
    conn = connect()
    migrations.apply_migrations(conn)
    # Ensure minimal mission_allocation tables exist for integration tests
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS mission_allocation_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT UNIQUE,
        unit_rsid TEXT,
        mission_total INTEGER,
        status TEXT,
        notes TEXT,
        created_at TEXT,
        started_at TEXT,
        finished_at TEXT,
        updated_at TEXT,
        completed_at TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS mission_allocation_inputs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT,
        company_id TEXT,
        recruiter_capacity INTEGER,
        historical_production INTEGER,
        funnel_health REAL,
        dep_loss INTEGER,
        school_access REAL,
        school_population INTEGER,
        ascope TEXT,
        pmesii TEXT,
        market_intel TEXT,
        extra_json TEXT,
        created_at TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS mission_allocation_company_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT,
        company_id TEXT,
        supportability_score REAL,
        risk_score REAL,
        confidence_score REAL,
        score_payload TEXT,
        created_at TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS mission_allocation_recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT,
        company_id TEXT,
        recommended_mission INTEGER,
        rationale TEXT,
        confidence REAL,
        created_at TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS mission_allocation_evidence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT,
        company_id TEXT,
        evidence_type TEXT,
        evidence_uri TEXT,
        description TEXT,
        created_at TEXT
    )''')
    conn.commit()
    conn.close()


def test_mission_risk_run_and_persistence():
    payload = {
        'unit_rsid': 'TESTU',
        'as_of_date': '2026-03-13',
        'inputs': [
            {
                'company_id': 'MR_COMP_1',
                'recruiter_capacity': 2,
                'mission_allocation_pressure': 0.8,
                'funnel_health': 0.4,
                'dep_loss': 1,
                'historical_production': 5,
                'school_targeting_pressure': 0.3,
                'data_quality_flags': {'missing_fields': False}
            }
        ]
    }

    out = v2router.mission_risk_run(payload)
    assert 'compute_run_id' in out
    assert isinstance(out.get('results'), list) and len(out.get('results')) == 1
    r = out['results'][0]
    assert 0.0 <= r.get('mission_risk_score') <= 1.0
    assert r.get('risk_level') in ('low', 'monitor', 'high')
    assert isinstance(r.get('confidence_score'), float)

    # persisted row exists
    conn = connect(); cur = conn.cursor()
    cur.execute('SELECT * FROM mission_risk_scores WHERE compute_run_id=?', (out.get('compute_run_id'),))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    assert len(rows) == 1


def test_mission_risk_latest_and_filtering():
    # create two runs for different units
    p1 = {'unit_rsid': 'U_A', 'as_of_date': '2026-03-13', 'inputs': [{'company_id': 'C_A', 'recruiter_capacity': 1}]}
    p2 = {'unit_rsid': 'U_B', 'as_of_date': '2026-03-13', 'inputs': [{'company_id': 'C_B', 'recruiter_capacity': 2}]}
    out1 = v2router.mission_risk_run(p1)
    out2 = v2router.mission_risk_run(p2)

    all_latest = v2router.mission_risk_latest()
    assert isinstance(all_latest.get('results'), list)
    # filter by unit
    res_a = v2router.mission_risk_latest(unit_rsid='U_A')
    assert isinstance(res_a.get('results'), list)
    # verify that returned rows (if any) have unit_rsid matching or are empty
    for rec in res_a.get('results'):
        assert rec.get('unit_rsid') == 'U_A'


def test_mal_integration_with_and_without_mission_risk():
    conn = connect(); cur = conn.cursor()

    # Ensure clean state for test companies
    cur.execute("DELETE FROM mission_risk_scores WHERE company_id IN ('COMP_WITH_MR','COMP_NO_MR')")
    cur.execute("DELETE FROM mission_allocation_runs WHERE unit_rsid='TESTUNIT_MR'")
    conn.commit()

    # Create a Mission Risk for COMP_WITH_MR
    mr_inputs = [
        {'company_id': 'COMP_WITH_MR', 'recruiter_capacity': 1, 'mission_allocation_pressure': 0.9, 'funnel_health': 0.2, 'dep_loss': 2, 'historical_production': 2}
    ]
    mr_res = mission_risk_engine.compute_mission_risks(mr_inputs, persist=True, unit_rsid='TESTUNIT_MR', as_of_date='2026-03-13', compute_run_id='mr_test_run')
    assert mr_res and len(mr_res) == 1

    # MAL run with both companies (one with MR, one without)
    run_id = mission_allocation_engine.create_run('TESTUNIT_MR', mission_total=3, notes='integration test')
    inputs = [
        {'company_id': 'COMP_WITH_MR', 'recruiter_capacity': 1, 'historical_production': 2, 'funnel_health': 0.3, 'dep_loss': 1},
        {'company_id': 'COMP_NO_MR', 'recruiter_capacity': 2, 'historical_production': 3, 'funnel_health': 0.6, 'dep_loss': 0}
    ]
    mission_allocation_engine.add_inputs(run_id, inputs)
    ok, msg = mission_allocation_engine.compute_run(run_id)
    assert ok

    # Evidence row for COMP_WITH_MR should exist
    cur.execute('SELECT * FROM mission_allocation_evidence WHERE run_id=? AND company_id=?', (run_id, 'COMP_WITH_MR'))
    ev = [dict(r) for r in cur.fetchall()]
    assert any(e.get('evidence_type') == 'mission_risk' for e in ev), 'mission_risk evidence missing for company with MR'

    # Score payload should include mission_risk for COMP_WITH_MR
    cur.execute('SELECT score_payload FROM mission_allocation_company_scores WHERE run_id=? AND company_id=?', (run_id, 'COMP_WITH_MR'))
    sp_row = cur.fetchone()
    assert sp_row is not None
    sp = json.loads(sp_row[0]) if sp_row and sp_row[0] else {}
    assert 'mission_risk' in sp and sp.get('mission_risk') is not None

    # details endpoint includes mr_summary / mr for evidence
    details = mal_router.get_supporting_details(run_id)
    found = False
    for e in details.get('evidence', []):
        if e.get('company_id') == 'COMP_WITH_MR' and e.get('evidence_type') == 'mission_risk':
            # router enrichment attaches mr_summary and mr under the evidence item
            assert 'mr_summary' in e and 'mr' in e
            found = True
    assert found, 'details endpoint did not include mission_risk evidence for company with MR'

    # Now create a MAL run for a company without mission risk and ensure it doesn't crash and no MR evidence created
    run2 = mission_allocation_engine.create_run('TESTUNIT_MR', mission_total=2, notes='no mr test')
    mission_allocation_engine.add_inputs(run2, [{'company_id': 'COMP_NO_MR', 'recruiter_capacity': 2, 'historical_production': 4, 'funnel_health': 0.7, 'dep_loss': 0}])
    ok2, msg2 = mission_allocation_engine.compute_run(run2)
    assert ok2
    cur.execute('SELECT * FROM mission_allocation_evidence WHERE run_id=? AND company_id=?', (run2, 'COMP_NO_MR'))
    ev2 = [dict(r) for r in cur.fetchall()]
    assert not any(e.get('evidence_type') == 'mission_risk' for e in ev2), 'bogus mission_risk evidence present for company without MR'

    conn.close()
