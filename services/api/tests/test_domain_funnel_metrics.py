from fastapi.testclient import TestClient
from services.api.app import main as app_module
from services.api.app import models, auth
from services.api.app.models import Base
from services.api.app.database import engine, SessionLocal

client = TestClient(app_module.app)


def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def create_org(db):
    cmd = models.Command(command='CMD1', display='CMD1')
    db.add(cmd); db.commit()
    bde = models.Brigade(brigade_prefix='1', display='B1', command_id=cmd.id)
    db.add(bde); db.commit()
    bn = models.Battalion(battalion_prefix='1A', display='Bn1A', brigade_id=bde.id)
    db.add(bn); db.commit()
    co = models.Company(company_prefix='1A1', display='Co', battalion_id=bn.id)
    db.add(co); db.commit()
    st = models.Station(rsid='1A1D', display='St1', company_id=co.id)
    db.add(st); db.commit()
    u = models.User(username='usarec_admin', role=models.UserRole.USAREC, scope='USAREC')
    db.add(u); db.commit()


def token_for(db, username):
    user = db.query(models.User).filter(models.User.username == username).one()
    return auth.create_token_for_user(user)


def test_funnel_stages_and_transition():
    db = SessionLocal()
    create_org(db)
    t = token_for(db, 'usarec_admin')
    headers = {'Authorization': f'Bearer {t}'}
    # get funnel stages
    r = client.get('/api/v2/funnel/stages', headers=headers)
    assert r.status_code == 200
    stages = r.json().get('data', [])
    assert any(s['id'] == 'lead' for s in stages)

    # post a transition
    tr = {'id': 'tr-1', 'lead_key': 'lead-1', 'station_rsid': '1A1D', 'from_stage': 'lead', 'to_stage': 'enlist', 'technician_user': 'tech1'}
    r = client.post('/api/v2/funnel/transition', json=tr, headers=headers)
    assert r.status_code == 200
