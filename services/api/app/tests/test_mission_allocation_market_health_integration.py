import json
from services.api.app import migrations
from services.api.app.db import connect
from services.api.app.services import market_health_engine, mission_allocation_engine


def setup_module(module):
    conn = connect()
    migrations.apply_migrations(conn)

    # Ensure mission allocation tables exist in the test DB (some test DBs
    # may start empty depending on environment). Create minimal schemas
    # required by the engine so integration tests can run.
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


def test_mal_uses_market_health_when_present():
    # create MH row for COMPANY_A
    mh_payload = {
        'market_type': 'company',
        'market_id': 'COMP_A_TEST',
        'unit_rsid': 'TESTUNIT',
        'as_of_date': '2026-03-13',
        'historical_trend': 0.8,
        'recruiter_ratio': 0.9,
        'market_load': 0.4,
        'activity_signal': 0.6,
        'demographic_signal': 0.7,
        'penetration_signal': 0.2,
        'risk_penalty': 0.1,
        'market_size_index': 1500,
        'data_quality_flags': {'missing_fields': False}
    }
    mh = market_health_engine.compute_market_health(mh_payload, persist=True)
    assert mh and mh.get('supportability_score') is not None

    # create MAL run
    run_id = mission_allocation_engine.create_run('TESTUNIT', mission_total=5, notes='test mh integration')

    inputs = [
        {
            'company_id': 'COMP_A_TEST',
            'recruiter_capacity': 2,
            'historical_production': 4,
            'funnel_health': 0.6,
            'dep_loss': 0,
            'school_access': 0.7,
            'school_population': 500,
            'market_intel': {'market_type': 'company', 'market_id': 'COMP_A_TEST'}
        },
        {
            'company_id': 'COMP_B_TEST',
            'recruiter_capacity': 2,
            'historical_production': 3,
            'funnel_health': 0.4,
            'dep_loss': 0,
            'school_access': 0.5,
            'school_population': 400
        }
    ]
    mission_allocation_engine.add_inputs(run_id, inputs)

    ok, msg = mission_allocation_engine.compute_run(run_id)
    assert ok

    # check that evidence exists linking COMP_A to market_health
    c = connect(); cur = c.cursor()
    cur.execute('SELECT * FROM mission_allocation_evidence WHERE run_id=? AND company_id=?', (run_id, 'COMP_A_TEST'))
    ev_rows = [dict(r) for r in cur.fetchall()]
    c.close()

    assert any(e.get('evidence_type') == 'market_health' for e in ev_rows), 'market_health evidence missing for company with MH'
