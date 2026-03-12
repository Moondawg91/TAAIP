from fastapi.testclient import TestClient
from services.api.app.main import app

client = TestClient(app)


def test_system_freshness_and_alerts_endpoints():
    r1 = client.get('/api/system/freshness')
    assert r1.status_code == 200
    j1 = r1.json()
    assert 'status' in j1 and j1['status'] == 'ok'
    assert 'data_as_of' in j1 and 'last_import_at' in j1

    r2 = client.get('/api/system/alerts')
    assert r2.status_code == 200
    j2 = r2.json()
    assert 'status' in j2 and j2['status'] == 'ok'
    assert 'alerts' in j2 and 'total' in j2
