from fastapi.testclient import TestClient
from services.api.app.main import app

client = TestClient(app)


def test_market_intel_summary_empty_safe():
    r = client.get('/api/market-intel/summary')
    assert r.status_code == 200
    data = r.json()
    assert 'status' in data
    assert 'data_as_of' in data
    assert 'filters' in data


def test_market_intel_zip_rankings_and_tables():
    r = client.get('/api/market-intel/zip-rankings')
    assert r.status_code == 200
    data = r.json()
    assert 'tables' in data or 'breakdowns' in data
    # should contain zip_rankings key even when empty
    container = data.get('tables', {}) if 'tables' in data else data.get('breakdowns', {})
    assert 'zip_rankings' in container


def test_market_intel_cbsa_and_targets():
    r = client.get('/api/market-intel/cbsa-rollup')
    assert r.status_code == 200
    data = r.json()
    assert 'tables' in data or 'breakdowns' in data

    r2 = client.get('/api/market-intel/targets')
    assert r2.status_code == 200
    data2 = r2.json()
    assert 'tables' in data2 or 'breakdowns' in data2


def test_market_intel_import_templates():
    r = client.get('/api/market-intel/import-templates')
    assert r.status_code == 200
    data = r.json()
    assert 'templates' in data
    assert isinstance(data.get('templates'), list)
