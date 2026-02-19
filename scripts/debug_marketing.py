import os, sys, json
sys.path.append('.')
from taaip_service import app, init_db
from fastapi.testclient import TestClient
# ensure fresh DB
DB='./taaip_dev.db'
try:
    os.remove(DB)
except Exception:
    pass
os.environ['LOCAL_DEV_AUTH_BYPASS']='1'
os.environ['TAAIP_DB_PATH']=DB
init_db()
client=TestClient(app)
# create event via compat endpoint
ev = {"name":"TestEv","type":"recruiting","location":"Now","start_date":"2025-11-01","end_date":"2025-11-02"}
r=client.post('/api/v2/events', json=ev)
print('create event status', r.status_code, r.text)
# post two activities
p1={"event_id":"evt_test_py","activity_type":"social_media","campaign_name":"PyTest Campaign","channel":"Facebook","data_source":"emm","impressions":1000,"engagement_count":100,"awareness_metric":0.7,"activation_conversions":10,"reporting_date":"2025-11-14"}
r1=client.post('/api/v2/marketing/activities', json=p1)
print('post1', r1.status_code, r1.text)
p2={"event_id":"evt_test_py","activity_type":"email","campaign_name":"PyTest Campaign","channel":"Email","data_source":"aiem","impressions":500,"engagement_count":50,"awareness_metric":0.85,"activation_conversions":5,"reporting_date":"2025-11-14"}
r2=client.post('/api/v2/marketing/activities', json=p2)
print('post2', r2.status_code, r2.text)
# raw rows
import sqlite3
conn=sqlite3.connect(DB)
cur=conn.cursor()
cur.execute('SELECT id, activity_id, impressions, engagement_count FROM marketing_activities')
rows=cur.fetchall()
print('raw rows:', rows)
# analytics endpoint
ra=client.get('/api/v2/marketing/analytics?event_id=evt_test_py')
print('analytics', ra.status_code, ra.json())
