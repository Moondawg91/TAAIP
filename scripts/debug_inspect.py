from taaip_service import init_db, get_db_conn
from services.api.app.main import app
from fastapi.testclient import TestClient

init_db()
client = TestClient(app)
# create event
r = client.post('/api/v2/events', json={'name':'x','type':'y','start_date':'2025-01-01','end_date':'2025-01-02'})
print('event resp', r.status_code, r.json())
# post activity
r = client.post('/api/v2/marketing/activities', json={'event_id': r.json().get('event_id'), 'activity_type':'social','impressions':10,'engagement_count':1, 'reporting_date':'2025-01-01'})
print('post activity', r.status_code, r.json())
act = r.json().get('activity_id')
# inspect table
conn = get_db_conn()
cur = conn.cursor()
print('PRAGMA table_info:')
for row in cur.execute("PRAGMA table_info(marketing_activities)"):
    print(row)
print('select *')
for row in cur.execute('SELECT * FROM marketing_activities'):
    print(row)
# try update both columns
cur.execute('UPDATE marketing_activities SET cost=? WHERE activity_id=? OR id=?', (123.0, act, act))
conn.commit()
print('after update')
for row in cur.execute('SELECT * FROM marketing_activities'):
    print(row)
conn.close()
print('done')
