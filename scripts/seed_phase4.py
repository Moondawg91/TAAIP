#!/usr/bin/env python3
"""Seed minimal production-like data for Phase-4 smoke tests."""
import os
os.environ.setdefault('TAAIP_DB_PATH', './taaip_dev.db')

from services.api.app.database import SessionLocal, engine
from services.api.app.models import Base, Command, Brigade, Battalion, Company, Station, StationZipCoverage, MarketCategory, User, UserRole

# Ensure schema exists
Base.metadata.create_all(bind=engine)

sess = SessionLocal()
try:
    # Clear small set of tables to ensure idempotency for seed
    # NOTE: keep it minimal to avoid removing data in other environments
    # Create command/brigade/battalion/company/stations
    cmd = sess.query(Command).filter(Command.command=='CMD1').one_or_none()
    if not cmd:
        cmd = Command(command='CMD1', display='Command 1')
        sess.add(cmd)
        sess.commit()

    bde = sess.query(Brigade).filter(Brigade.brigade_prefix=='1', Brigade.command_id==cmd.id).one_or_none()
    if not bde:
        bde = Brigade(brigade_prefix='1', display='Brigade 1', command_id=cmd.id)
        sess.add(bde)
        sess.commit()

    bn = sess.query(Battalion).filter(Battalion.battalion_prefix=='1A', Battalion.brigade_id==bde.id).one_or_none()
    if not bn:
        bn = Battalion(battalion_prefix='1A', display='Battalion 1A', brigade_id=bde.id)
        sess.add(bn)
        sess.commit()

    co = sess.query(Company).filter(Company.company_prefix=='1A1', Company.battalion_id==bn.id).one_or_none()
    if not co:
        co = Company(company_prefix='1A1', display='Company 1A1', battalion_id=bn.id)
        sess.add(co)
        sess.commit()

    st = sess.query(Station).filter(Station.rsid=='1A1D').one_or_none()
    if not st:
        st = Station(rsid='1A1D', display='Station 1', company_id=co.id)
        sess.add(st)
        sess.commit()

    # Add station zip coverage
    z = sess.query(StationZipCoverage).filter(StationZipCoverage.station_rsid=='1A1D', StationZipCoverage.zip_code=='12345').one_or_none()
    if not z:
        z = StationZipCoverage(station_rsid='1A1D', zip_code='12345', market_category=MarketCategory.MK)
        sess.add(z)
        sess.commit()

    # Add a couple of users
    u = sess.query(User).filter(User.username=='station_view').one_or_none()
    if not u:
        u = User(username='station_view', role=UserRole.STATION_VIEW, scope='1A1D')
        sess.add(u)
    u2 = sess.query(User).filter(User.username=='usarec_admin').one_or_none()
    if not u2:
        u2 = User(username='usarec_admin', role=UserRole.USAREC, scope='USAREC')
        sess.add(u2)
    sess.commit()

    print('Seed complete')
finally:
    sess.close()
