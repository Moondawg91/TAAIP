import os
import tempfile
from services.api.app import crud, models, rbac
from services.api.app.database import SessionLocal, engine


def setup_module(module):
    # ensure a clean schema for tests
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)


def create_org_fixture(db):
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


def test_rbac_query_filters():
    db = SessionLocal()
    create_org_fixture(db)
    create_users(db)

    # station_view should only see 1A1D
    user_station = db.query(models.User).filter(models.User.username == 'station_view').one()
    q = crud.get_station_zip_coverage(db, '1A1D')
    qf = rbac.apply_scope_filter(q, models.StationZipCoverage, user_station.scope)
    res = qf.all()
    assert len(res) == 1

    # station_view cannot see 1B1D
    q2 = crud.get_station_zip_coverage(db, '1B1D')
    q2f = rbac.apply_scope_filter(q2, models.StationZipCoverage, user_station.scope)
    assert q2f.count() == 0

    # battalion user (1A) can see 1A1D but not 1B1D
    user_bn = db.query(models.User).filter(models.User.username == 'bn_420t').one()
    q_a = crud.get_station_zip_coverage(db, '1A1D')
    assert rbac.apply_scope_filter(q_a, models.StationZipCoverage, user_bn.scope).count() == 1
    q_b = crud.get_station_zip_coverage(db, '1B1D')
    assert rbac.apply_scope_filter(q_b, models.StationZipCoverage, user_bn.scope).count() == 0

    # USAREC can see both
    user_hq = db.query(models.User).filter(models.User.username == 'usarec_admin').one()
    assert rbac.apply_scope_filter(crud.get_station_zip_coverage(db, '1A1D'), models.StationZipCoverage, user_hq.scope).count() == 1
    assert rbac.apply_scope_filter(crud.get_station_zip_coverage(db, '1B1D'), models.StationZipCoverage, user_hq.scope).count() == 1

