import os
from fastapi.testclient import TestClient

# ensure debug flags
os.environ['DEBUG_RBAC'] = '1'
if 'LOCAL_DEV_AUTH_BYPASS' in os.environ:
    del os.environ['LOCAL_DEV_AUTH_BYPASS']

from services.api.app import main as app_module
from services.api.app.models import Base
from services.api.app.database import engine, SessionLocal
from services.api.app import db as dbmod
from services.api.app import auth
from services.api.app import models

# prepare DB
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
os.environ['TAAIP_DB_PATH'] = './taaip_dev.db'
dbmod.init_db()

# create org and users
db = SessionLocal()
cmd = models.Command(command='CMD1', display='CMD1')
db.add(cmd); db.commit()
bde = models.Brigade(brigade_prefix='1', display='B1', command_id=cmd.id)
db.add(bde); db.commit()
bn = models.Battalion(battalion_prefix='1A', display='Bn1A', brigade_id=bde.id)
db.add(bn); db.commit()
co = models.Company(company_prefix='1A1', display='Co', battalion_id=bn.id)
db.add(co); db.commit()
st1 = models.Station(rsid='1A1D', display='St1', company_id=co.id)
st2 = models.Station(rsid='1B1D', display='St2', company_id=co.id)
db.add_all([st1, st2])
db.commit()
users = [models.User(username='usarec_admin', role=models.UserRole.USAREC, scope='USAREC'), models.User(username='bn_420t', role=models.UserRole.BATTALION_420T, scope='1A'), models.User(username='station_view', role=models.UserRole.STATION_VIEW, scope='1A1D')]
for u in users:
    db.add(u)
db.commit()

# create tokens
station_token = auth.create_token_for_user(db.query(models.User).filter(models.User.username=='station_view').one())
hq_token = auth.create_token_for_user(db.query(models.User).filter(models.User.username=='usarec_admin').one())

client = TestClient(app_module.app)

payload = {'id': 'evt-1', 'station_rsid': '1A1D', 'name': 'Test Event', 'event_type': 'test'}
res = client.post('/api/v2/events', json=payload, headers={'Authorization': f'Bearer {station_token}'})
print('station res status', res.status_code)
try:
    print('station res json', res.json())
except Exception:
    print('station res text', res.text)

res2 = client.post('/api/v2/events', json=payload, headers={'Authorization': f'Bearer {hq_token}'})
print('hq res status', res2.status_code)
try:
    print('hq res json', res2.json())
except Exception:
    print('hq res text', res2.text)

print('\n--- auth_debug.log ---')
if os.path.exists('/tmp/auth_debug.log'):
    print(open('/tmp/auth_debug.log').read())
else:
    print('no auth_debug.log')

print('\n--- rbac_debug.log ---')
if os.path.exists('/tmp/rbac_debug.log'):
    print(open('/tmp/rbac_debug.log').read())
else:
    print('no rbac_debug.log')
