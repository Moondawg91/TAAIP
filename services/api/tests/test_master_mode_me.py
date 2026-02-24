import os
from fastapi.testclient import TestClient

# enable master mode before importing app so startup picks it up
os.environ['TAAIP_MASTER_MODE'] = '1'

from services.api.app.main import app

client = TestClient(app)


def test_master_mode_me_returns_wildcard_permissions():
    r = client.get('/api/me')
    assert r.status_code == 200
    data = r.json()
    assert 'permissions' in data
    assert isinstance(data['permissions'], list)
    assert '*' in data['permissions']
    assert 'roles' in data
    assert 'system_admin' in [r.lower() for r in data.get('roles', [])]
