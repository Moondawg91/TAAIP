from fastapi.testclient import TestClient
from services.api.app.main import app

client = TestClient(app)


def test_market_intel_readiness_empty_safe():
    r = client.get('/api/market-intel/readiness')
    assert r.status_code == 200
    data = r.json()
    assert 'status' in data
    assert 'datasets' in data and isinstance(data['datasets'], list)
    assert 'blocking' in data and isinstance(data['blocking'], list)


def test_market_intel_export_csv_header_only():
    r = client.get('/api/market-intel/export/targets.csv')
    assert r.status_code == 200
    text = r.text
    # header should include the expected columns
    assert text.startswith('fy,qtr,rsid_prefix,zip,cbsa,market_category,priority_bucket')


def test_market_intel_import_templates_executable_keys():
    r = client.get('/api/market-intel/import-templates')
    assert r.status_code == 200
    data = r.json()
    assert 'templates' in data
    # executable templates key should be present even if empty
    assert 'executable_templates' in data
    assert isinstance(data.get('executable_templates'), list)
    # each executable template (if present) must have mapping_hints and validation_rules
    for t in data.get('executable_templates', []):
        assert 'mapping_hints' in t
        assert 'validation_rules' in t
