from fastapi.testclient import TestClient
from services.api.app import main as app_module
from services.api.app import models, database, auth
from services.api.app.models import Base
from services.api.app.database import engine, SessionLocal
from datetime import date

client = TestClient(app_module.app)


def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    import os
    from services.api.app.db import init_db
    os.environ['TAAIP_DB_PATH'] = './taaip_dev.db'
    init_db()
    # Ensure test DB starts with a clean marketing_activities table to avoid
    # pre-seeded rows from other tests or previous runs interfering with
    # aggregation expectations.
    try:
        from services.api.app.db import connect
        conn = connect()
        cur = conn.cursor()
        try:
            cur.execute('DELETE FROM marketing_activities')
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
        try:
            conn.close()
        except Exception:
            pass
    except Exception:
        pass


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def create_org_and_users(db):
    cmd = db.query(models.Command).filter(models.Command.command == 'CMD1').first()
    if not cmd:
        cmd = models.Command(command='CMD1', display='CMD1')
        db.add(cmd)
        db.commit()
    bde = models.Brigade(brigade_prefix='1', display='B1', command_id=cmd.id)
    existing_bde = db.query(models.Brigade).filter(models.Brigade.brigade_prefix == '1', models.Brigade.command_id == cmd.id).first()
    if not existing_bde:
        bde = models.Brigade(brigade_prefix='1', display='B1', command_id=cmd.id)
        db.add(bde)
        db.commit()
    else:
        bde = existing_bde
    bn = db.query(models.Battalion).filter(models.Battalion.battalion_prefix == '1A', models.Battalion.brigade_id == bde.id).first()
    if not bn:
        bn = models.Battalion(battalion_prefix='1A', display='Bn1A', brigade_id=bde.id)
        db.add(bn)
        db.commit()
    co = db.query(models.Company).filter(models.Company.company_prefix == '1A1', models.Company.battalion_id == bn.id).first()
    if not co:
        co = models.Company(company_prefix='1A1', display='Co', battalion_id=bn.id)
        db.add(co)
        db.commit()
    st1 = db.query(models.Station).filter(models.Station.rsid == '1A1D').first()
    if not st1:
        st1 = models.Station(rsid='1A1D', display='St1', company_id=co.id)
        db.add(st1)
        db.commit()
    u = db.query(models.User).filter(models.User.username == 'usarec_admin').first()
    if not u:
        u = models.User(username='usarec_admin', role=models.UserRole.USAREC, scope='USAREC')
        db.add(u)
        db.commit()


def token_for(db, username):
    user = db.query(models.User).filter(models.User.username == username).one()
    return auth.create_token_for_user(user)


def test_marketing_summary():
    db = SessionLocal()
    create_org_and_users(db)
    t = token_for(db, 'usarec_admin')
    headers = {'Authorization': f'Bearer {t}'}
    a1 = {'id': 'ma-1', 'station_rsid': '1A1D', 'activity_type': 'social_media', 'impressions': 100, 'engagements': 10, 'clicks': 5, 'conversions': 1, 'cost': 50, 'reporting_date': str(date.today())}
    a2 = {'id': 'ma-2', 'station_rsid': '1A1D', 'activity_type': 'email', 'impressions': 200, 'engagements': 20, 'clicks': 10, 'conversions': 2, 'cost': 30, 'reporting_date': str(date.today())}
    r = client.post('/api/v2/marketing/activities', json=a1, headers=headers)
    assert r.status_code == 200
    r = client.post('/api/v2/marketing/activities', json=a2, headers=headers)
    assert r.status_code == 200

    r = client.get('/api/v2/marketing/summary', headers=headers)
    assert r.status_code == 200
    data = r.json().get('data', {})
    assert data['impressions'] == 300
    assert data['conversions'] == 3
