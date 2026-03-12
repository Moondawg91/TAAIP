import json
from fastapi.testclient import TestClient
from services.api.app.main import app

client = TestClient(app)


def test_scoring_endpoints_empty_safe():
    endpoints = [
        '/api/command/scoring/market-capacity',
        '/api/command/scoring/mission-feasibility',
        '/api/command/scoring/resource-alignment',
        '/api/command/scoring/school-health',
        '/api/command/scoring/cep-effectiveness'
    ]
    for ep in endpoints:
        r = client.get(ep)
        assert r.status_code == 200
        data = r.json()
        assert 'status' in data
        assert 'score' in data
        assert 'tier' in data


def test_coa_recommendations_empty_safe():
    r = client.get('/api/command/coa/recommendations')
    assert r.status_code == 200
    data = r.json()
    assert 'status' in data
    assert 'coas' in data
    assert isinstance(data.get('coas'), list)
