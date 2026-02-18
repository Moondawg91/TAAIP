from fastapi.testclient import TestClient
from services.api.app import main as app_module
from services.api.app import models, auth
from services.api.app.models import Base
from services.api.app.database import engine, SessionLocal
from datetime import date

client = TestClient(app_module.app)


def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    from services.api.app.db import init_db
    init_db()


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def create_user_and_org(db):
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
    u = models.User(username='co_cmd', role=models.UserRole.COMPANY_CMD, scope='1A1')
    db.add(u); db.commit()


def token_for(db, username):
    user = db.query(models.User).filter(models.User.username == username).one()
    return auth.create_token_for_user(user)


def test_burden_input_and_latest():
    db = SessionLocal()
    create_user_and_org(db)
    t = token_for(db, 'co_cmd')
    headers = {'Authorization': f'Bearer {t}'}
    payload = {'id': 'bi-1', 'scope_type': 'CO', 'scope_value': '1A1', 'mission_requirement': 100, 'recruiter_strength': 10, 'reporting_date': str(date.today())}
    r = client.post('/api/v2/burden/input', json=payload, headers=headers)
    assert r.status_code == 200

    r = client.get('/api/v2/burden/latest?scope_type=CO&scope_value=1A1', headers=headers)
    assert r.status_code == 200
    data = r.json().get('data', {})
    assert data['mission_requirement'] == 100
