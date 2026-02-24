import json
from fastapi.testclient import TestClient
from services.api.app.main import app

client = TestClient(app)


def test_command_center_priorities_and_loes_crud():
    # ensure list endpoints return OK structure
    r = client.get('/api/command-center/priorities')
    assert r.status_code == 200
    data = r.json()
    assert 'status' in data

    r = client.get('/api/command-center/loes')
    assert r.status_code == 200
    data = r.json()
    assert 'status' in data

    # create a priority
    payload = {'title': 'Test Priority', 'description': 'Created by test'}
    r = client.post('/api/command-center/priorities', json=payload)
    assert r.status_code == 200

    # create an LOE
    payload = {'id': 'loe-test-1', 'title': 'Test LOE', 'description': 'Created by test'}
    r = client.post('/api/command-center/loes', json=payload)
    assert r.status_code == 200

    # list loes should include our created LOE
    r = client.get('/api/command-center/loes')
    assert r.status_code == 200
    data = r.json()
    items = data.get('items', [])
    assert any(i.get('id') == 'loe-test-1' or i.get('loe_id') == 'loe-test-1' for i in items)
