import os
from fastapi.testclient import TestClient
import pytest

from services.api.app import main as app_module
from services.api.app import models, database, auth
from services.api.app.models import Base
from services.api.app.database import engine, SessionLocal


client = TestClient(app_module.app)


def setup_module(module):
    # ensure a clean schema for tests
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    # drop tables after tests
    Base.metadata.drop_all(bind=engine)


def create_org_fixture(db):
    # create a simple org: command -> brigade 1 -> battalions 1A,1B -> companies -> stations
    cmd = models.Command(command='CMD1', display='CMD1')
    db.add(cmd)
    db.commit()

    bde = models.Brigade(brigade_prefix='1', display='Br1', command_id=cmd.id)
    db.add(bde)
    db.commit()

    bn1 = models.Battalion(battalion_prefix='1A', display='Bn1A', brigade_id=bde.id)
    bn2 = models.Battalion(battalion_prefix='1B', display='Bn1B', brigade_id=bde.id)
    db.add_all([bn1, bn2])
    db.commit()

    co1 = models.Company(company_prefix='1A1', display='Co1A1', battalion_id=bn1.id)
    co2 = models.Company(company_prefix='1B1', display='Co1B1', battalion_id=bn2.id)
    db.add_all([co1, co2])
    db.commit()

    st1 = models.Station(rsid='1A1D', display='Station1', company_id=co1.id)
    st2 = models.Station(rsid='1B1D', display='Station2', company_id=co2.id)
    db.add_all([st1, st2])
    db.commit()

    # add coverage
    c1 = models.StationZipCoverage(station_rsid='1A1D', zip_code='12345', market_category=models.MarketCategory.MK)
    c2 = models.StationZipCoverage(station_rsid='1B1D', zip_code='23456', market_category=models.MarketCategory.MW)
    db.add_all([c1, c2])
    db.commit()


def create_users(db):
    users = [
        models.User(username='station_view', role=models.UserRole.STATION_VIEW, scope='1A1D'),
        models.User(username='bn_420t', role=models.UserRole.BATTALION_420T, scope='1A'),
        models.User(username='usarec_admin', role=models.UserRole.USAREC, scope='USAREC'),
    ]
    for u in users:
        db.add(u)
    db.commit()


def token_for_username(db, username):
    user = db.query(models.User).filter(models.User.username == username).one()
    return auth.create_token_for_user(user)


def test_rbac_scope_access():
    db = SessionLocal()
    create_org_fixture(db)
    create_users(db)

    # station_view token
    t_station = token_for_username(db, 'station_view')
    headers = {'Authorization': f'Bearer {t_station}'}

    # allowed: station 1
    r = client.get('/api/org/stations/1A1D/zip-coverage', headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data['station_rsid'] == '1A1D'
    assert any(item['zip_code'] == '12345' for item in data['zip_coverage'])

    # forbidden: station 2
    r = client.get('/api/org/stations/1B1D/zip-coverage', headers=headers)
    assert r.status_code == 403

    # bn_420t token
    t_bn = token_for_username(db, 'bn_420t')
    headers_bn = {'Authorization': f'Bearer {t_bn}'}
    r = client.get('/api/org/stations/1A1D/zip-coverage', headers=headers_bn)
    assert r.status_code == 200
    r = client.get('/api/org/stations/1B1D/zip-coverage', headers=headers_bn)
    assert r.status_code == 403

    # USAREC can see both
    t_hq = token_for_username(db, 'usarec_admin')
    headers_hq = {'Authorization': f'Bearer {t_hq}'}
    r = client.get('/api/org/stations/1A1D/zip-coverage', headers=headers_hq)
    assert r.status_code == 200
    r = client.get('/api/org/stations/1B1D/zip-coverage', headers=headers_hq)
    assert r.status_code == 200
