from services.api.app.services import mission_risk_engine
from services.api.app import migrations
from services.api.app.db import connect


def setup_module(module):
    conn = connect()
    migrations.apply_migrations(conn)
    conn.close()


def test_mission_risk_bounds_and_components():
    inputs = [
        {
            'company_id': 'C1',
            'recruiter_capacity': 2,
            'mission_allocation_pressure': 0.9,
            'funnel_health': 0.3,
            'dep_loss': 2,
            'historical_production': 5,
            'market_intel': {'market_type': 'company', 'market_id': 'COMP_X'},
            'school_targeting_pressure': 0.8,
            'data_quality_flags': {'missing_fields': False}
        }
    ]
    res = mission_risk_engine.compute_mission_risks(inputs, persist=False, unit_rsid='U1', as_of_date='2026-03-13', compute_run_id='testmr')
    assert isinstance(res, list) and len(res) == 1
    r = res[0]
    assert 0.0 <= r.get('mission_risk_score') <= 1.0
    assert r.get('risk_level') in ('low', 'monitor', 'high')
    assert isinstance(r.get('top_risk_factors'), list)
    assert isinstance(r.get('confidence_score'), float)


def test_mission_risk_persistence_and_api_shape():
    # create a row and persist
    inputs = [
        {
            'company_id': 'C2',
            'recruiter_capacity': 1,
            'mission_allocation_pressure': 0.7,
            'funnel_health': 0.4,
            'dep_loss': 1,
            'historical_production': 3,
            'school_targeting_pressure': 0.2,
            'data_quality_flags': {'missing_fields': False}
        }
    ]
    res = mission_risk_engine.compute_mission_risks(inputs, persist=True, unit_rsid='U1', as_of_date='2026-03-13', compute_run_id='testmr2')
    assert isinstance(res, list) and len(res) == 1
    # check DB row exists
    c = connect(); cur = c.cursor()
    cur.execute('SELECT * FROM mission_risk_scores WHERE compute_run_id=?', ('testmr2',))
    rows = cur.fetchall()
    c.close()
    assert len(rows) >= 1
