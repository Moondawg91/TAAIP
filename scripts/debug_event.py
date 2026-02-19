import os, json, sys
sys.path.append('.')
from taaip_service import app, init_db
from fastapi.testclient import TestClient
os.environ['LOCAL_DEV_AUTH_BYPASS']='1'
os.environ['TAAIP_DB_PATH']='./taaip_dev.db'
init_db()
client=TestClient(app)
ev = {"name":"Export Event 2","type":"recruiting","location":"Test","start_date":"2025-11-01","end_date":"2025-11-30","budget":2000,"team_size":2,"targeting_principles":"export"}
r = client.post('/api/v2/events', json=ev)
print('status', r.status_code)
try:
    print('json:', r.json())
except Exception:
    print('text:', r.text)
