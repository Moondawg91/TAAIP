import os
os.environ.pop('LOCAL_DEV_AUTH_BYPASS', None)
os.environ['DEBUG_RBAC'] = '1'
from fastapi.testclient import TestClient
from services.api.app import main as app_module
from services.api.app.models import Base
from services.api.app.database import engine, SessionLocal
from services.api.app import db as dbmod
from services.api.app import auth, models

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
os.environ['TAAIP_DB_PATH'] = './taaip_dev.db'
dbmod.init_db()

# create user
db = SessionLocal()
u = models.User(username='station_view', role=models.UserRole.STATION_VIEW, scope='1A1D')
db.add(u); db.commit()

# token
t = auth.create_token_for_user(u)

client = TestClient(app_module.app)
res = client.post('/api/v2/events', json={'station_rsid':'1A1D','id':'evt-1','name':'test','event_type':'t'}, headers={'Authorization':f'Bearer {t}'})
print('status', res.status_code)
try:
    print(res.json())
except:
    print(res.text)
