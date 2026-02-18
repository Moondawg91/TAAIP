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


def create_org_and_user(db):
    cmd = models.Command(command='CMD1', display='CMD1')
    db.add(cmd); db.commit()
    bde = models.Brigade(brigade_prefix='1', display='B1', command_id=cmd.id)
    db.add(bde); db.commit()
    bn = models.Battalion(battalion_prefix='1A', display='Bn1A', brigade_id=bde.id)
    db.add(bn); db.commit()
    co = models.Company(company_prefix='1A1', display='Co', battalion_id=bn.id)
    db.add(co); db.commit()
    u = models.User(username='usarec_admin', role=models.UserRole.USAREC, scope='USAREC')
    db.add(u); db.commit()


def token_for(db, username):
    user = db.query(models.User).filter(models.User.username == username).one()
    return auth.create_token_for_user(user)


def test_loe_create_and_evaluate():
    db = SessionLocal()
    create_org_and_user(db)
    t = token_for(db, 'usarec_admin')
    headers = {'Authorization': f'Bearer {t}'}
    loe = {'id': 'loe-1', 'scope_type': 'CO', 'scope_value': '1A1', 'title': 'Test LOE', 'description': 'desc', 'created_by': 'usarec_admin'}
    r = client.post('/api/v2/loes', json=loe, headers=headers)
    assert r.status_code == 200

    # create metric
    lm = {'id': 'lm-1', 'loe_id': 'loe-1', 'metric_name': 'throughput', 'target_value': 100, 'warn_threshold': 70, 'fail_threshold': 50}
    r = client.post('/api/v2/loes/loe-1/metrics', json=lm, headers=headers)
    assert r.status_code == 200

    # set current_value directly in DB to simulate ingestion
    from services.api.app.models_domain import LoeMetric
    metric = db.query(LoeMetric).filter(LoeMetric.id == 'lm-1').one()
    metric.current_value = 80
    db.commit()

    r = client.post('/api/v2/loes/loe-1/evaluate', headers=headers)
    assert r.status_code == 200
    data = r.json().get('data', {})
    assert data['evaluated'] == 1
