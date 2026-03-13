import json
from services.api.app import migrations
from services.api.app.db import connect
from services.api.app.services import market_health_engine


def setup_module(module):
    # ensure migrations applied to have clean schema
    conn = connect()
    migrations.apply_migrations(conn)
    conn.close()


def test_compute_market_health_basic_properties():
    payload = {
        'market_type': 'company',
        'market_id': 'TEST_CO',
        'unit_rsid': 'TESTUNIT',
        'as_of_date': '2026-03-13',
        'historical_trend': 0.6,
        'recruiter_ratio': 0.8,
        'market_load': 0.3,
        'activity_signal': 0.5,
        'demographic_signal': 0.4,
        'penetration_signal': 0.2,
        'risk_penalty': 0.0,
        'market_size_index': 1000,
        'data_quality_flags': {'missing_fields': False}
    }

    res = market_health_engine.compute_market_health(payload, persist=False)
    assert isinstance(res, dict)
    assert 0.0 <= res.get('supportability_score', 0.0) <= 1.0
    assert 0.0 <= res.get('confidence_score', 0.0) <= 1.0


def test_risk_penalty_reduces_supportability():
    base = {
        'market_type': 'company',
        'market_id': 'TEST_CO2',
        'unit_rsid': 'TESTUNIT',
        'as_of_date': '2026-03-13',
        'historical_trend': 0.6,
        'recruiter_ratio': 0.8,
        'market_load': 0.3,
        'activity_signal': 0.5,
        'demographic_signal': 0.4,
        'penetration_signal': 0.2,
        'market_size_index': 1000,
        'data_quality_flags': {'missing_fields': False}
    }

    no_risk = dict(base)
    no_risk['risk_penalty'] = 0.0
    with_risk = dict(base)
    with_risk['risk_penalty'] = 0.2

    r1 = market_health_engine.compute_market_health(no_risk, persist=False)
    r2 = market_health_engine.compute_market_health(with_risk, persist=False)

    assert r1.get('supportability_score') is not None
    assert r2.get('supportability_score') is not None
    # supportability with risk should be less-or-equal than without
    assert r2['supportability_score'] <= r1['supportability_score'] + 1e-6
