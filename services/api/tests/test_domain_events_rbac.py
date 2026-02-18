from fastapi.testclient import TestClient
from services.api.app import main as app_module
from services.api.app import models, database, auth
from services.api.app.models import Base
from services.api.app.database import engine, SessionLocal

client = TestClient(app_module.app)


def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    import os
    from services.api.app.db import init_db
    os.environ['TAAIP_DB_PATH'] = './taaip_dev.db'
    init_db()


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def create_org(db):
    cmd = models.Command(command='CMD1', display='CMD1')
    db.add(cmd)
    db.commit()
    bde = models.Brigade(brigade_prefix='1', display='B1', command_id=cmd.id)
    db.add(bde)
    db.commit()
    bn = models.Battalion(battalion_prefix='1A', display='Bn1A', brigade_id=bde.id)
    db.add(bn)
    db.commit()
    co = models.Company(company_prefix='1A1', display='Co', battalion_id=bn.id)
    db.add(co)
    db.commit()
    st1 = models.Station(rsid='1A1D', display='St1', company_id=co.id)
    st2 = models.Station(rsid='1B1D', display='St2', company_id=co.id)
    db.add_all([st1, st2])
    db.commit()


def create_users(db):
    users = [
        models.User(username='usarec_admin', role=models.UserRole.USAREC, scope='USAREC'),
        models.User(username='bn_420t', role=models.UserRole.BATTALION_420T, scope='1A'),
        models.User(username='station_view', role=models.UserRole.STATION_VIEW, scope='1A1D'),
    ]
    for u in users:
        db.add(u)
    db.commit()


def token_for(db, username):
    user = db.query(models.User).filter(models.User.username == username).one()
    return auth.create_token_for_user(user)


def test_event_create_and_rbac():
    db = SessionLocal()
    create_org(db)
    create_users(db)
    t_station = token_for(db, 'station_view')
    headers = {'Authorization': f'Bearer {t_station}'}

    # station_view is view-only; create should be forbidden
    payload = {'id': 'evt-1', 'station_rsid': '1A1D', 'name': 'Test Event', 'event_type': 'test'}
    r = client.post('/api/v2/events', json=payload, headers=headers)
    assert r.status_code == 403

    # forbidden create for station outside scope
    payload2 = {'id': 'evt-2', 'station_rsid': '1B1D', 'name': 'Bad Event', 'event_type': 'test'}
    r = client.post('/api/v2/events', json=payload2, headers=headers)
    assert r.status_code == 403

    # USAREC can create anywhere
    t_hq = token_for(db, 'usarec_admin')
    r = client.post('/api/v2/events', json=payload2, headers={'Authorization': f'Bearer {t_hq}'})
    assert r.status_code == 200
