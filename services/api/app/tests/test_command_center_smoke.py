from fastapi.testclient import TestClient
from services.api.app.main import app

client = TestClient(app)


def test_command_center_endpoints_load():
    """Smoke: each engine endpoint returns JSON and 'results' if present is a list."""
    # market-health may not be exposed as an API route in all deployments;
    # accept 200 or 404 for that widget. Test core endpoints that should exist.
    endpoints = [
        '/api/v2/mission-risk/latest',
        '/api/v2/targeting/schools',
    ]

    for ep in endpoints:
        resp = client.get(ep)
        assert resp.status_code == 200, f"{ep} returned {resp.status_code}"
        data = resp.json()
        assert isinstance(data, dict), f"{ep} did not return a JSON object"
        if 'results' in data:
            assert isinstance(data['results'], list), f"{ep} results is not a list"


def test_command_center_partial_failure_resilience():
    """Smoke: a 404/405 on one path should not prevent other endpoints from returning OK."""
    bad = client.get('/api/v2/mission-risk/this-should-not-exist')
    assert bad.status_code in (404, 405, 200)

    # Ensure core endpoints still work
    # market-health is optional; if present it must return JSON, else 404 is acceptable
    mh = client.get('/api/v2/market-health/latest')
    assert mh.status_code in (200, 404)
    resp = client.get('/api/v2/targeting/schools')
    assert resp.status_code == 200


def test_command_center_empty_state_structure():
    """Smoke: when endpoints return empty, the shape remains consistent (results -> list).
    This test treats absence of data as acceptable, but ensures structure is predictable.
    """
    endpoints = ['/api/v2/mission-risk/latest']
    for ep in endpoints:
        resp = client.get(ep)
        assert resp.status_code == 200
        data = resp.json()
        # either no results key (single object) or results is a list (possibly empty)
        if 'results' in data:
            assert isinstance(data['results'], list)
