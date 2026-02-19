from taaip_service import app
from fastapi.testclient import TestClient

client = TestClient(app)

ev = {"name": "Export Event 2", "type": "recruiting", "location": "Test", "start_date": "2025-11-01", "end_date": "2025-11-30", "budget": 2000, "team_size": 2, "targeting_principles": "export"}
resp = client.post('/api/v2/events', json=ev)
print('status', resp.status_code)
try:
    print('json:', resp.json())
except Exception as e:
    print('raw:', resp.text)

