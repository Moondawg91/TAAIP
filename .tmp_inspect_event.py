from taaip_service import app, init_db
from fastapi.testclient import TestClient
init_db()
client = TestClient(app)
ev = {'name':'Export Event 2','type':'recruiting','location':'Test','start_date':'2025-11-01','end_date':'2025-11-30','budget':2000,'team_size':2,'targeting_principles':'export'}
r = client.post('/api/v2/events', json=ev)
print('status', r.status_code)
print('headers', dict(r.headers))
try:
    print('json', r.json())
except Exception:
    print('text', r.text)
