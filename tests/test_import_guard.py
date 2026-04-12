import os
from fastapi.testclient import TestClient
from services.api.app.main import app

client = TestClient(app)

SIM_CSV = "school_id,lead_id\nSIM_123,sim-1\n"
REAL_CSV = "school_id,lead_id\nSCH_001,lead-1\n"


def test_rejects_sim_demo_by_default():
    # ensure env var not set
    if 'ALLOW_SIMULATION_IMPORTS' in os.environ:
        del os.environ['ALLOW_SIMULATION_IMPORTS']

    files = {'file': ('sim.csv', SIM_CSV, 'text/csv')}
    r1 = client.post('/api/import/upload', files=files, data={'uploaded_by': 'pytest'})
    assert r1.status_code == 400
    assert 'simulation' in r1.json().get('detail', '').lower()

    r2 = client.post('/api/v2/import/upload', files=files, data={'uploaded_by': 'pytest'})
    assert r2.status_code == 400
    assert 'simulation' in r2.json().get('detail', '').lower()


def test_accepts_normal_when_allowed_or_normal_file():
    # normal file should be accepted
    files = {'file': ('real.csv', REAL_CSV, 'text/csv')}
    r1 = client.post('/api/import/upload', files=files, data={'uploaded_by': 'pytest'})
    assert r1.status_code == 200

    r2 = client.post('/api/v2/import/upload', files=files, data={'uploaded_by': 'pytest'})
    assert r2.status_code == 200

    # explicit override allows SIM uploads
    os.environ['ALLOW_SIMULATION_IMPORTS'] = '1'
    files = {'file': ('sim.csv', SIM_CSV, 'text/csv')}
    r3 = client.post('/api/import/upload', files=files, data={'uploaded_by': 'pytest'})
    assert r3.status_code == 200
    r4 = client.post('/api/v2/import/upload', files=files, data={'uploaded_by': 'pytest'})
    assert r4.status_code == 200
    del os.environ['ALLOW_SIMULATION_IMPORTS']
