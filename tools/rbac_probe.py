from services.api.app import database, models, rbac
from services.api.app.database import SessionLocal, engine
from services.api.app.models import Base

# recreate schema
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# create sample org and users manually
from services.api.app import models as m
from sqlalchemy.orm import Session

s: Session = SessionLocal()
try:
    cmd = m.Command(command='CMD1', display='CMD1')
    s.add(cmd)
    s.commit()
    bde = m.Brigade(brigade_prefix='1', display='B1', command_id=cmd.id)
    s.add(bde); s.commit()
    bn = m.Battalion(battalion_prefix='1A', display='Bn1A', brigade_id=bde.id)
    s.add(bn); s.commit()
    co = m.Company(company_prefix='1A1', display='Co', battalion_id=bn.id)
    s.add(co); s.commit()
    st1 = m.Station(rsid='1A1D', display='St1', company_id=co.id)
    st2 = m.Station(rsid='1B1D', display='St2', company_id=co.id)
    s.add_all([st1, st2]); s.commit()

    users = [
        m.User(username='usarec_admin', role=m.UserRole.USAREC, scope='USAREC'),
        m.User(username='bn_420t', role=m.UserRole.BATTALION_420T, scope='1A'),
        m.User(username='station_view', role=m.UserRole.STATION_VIEW, scope='1A1D'),
    ]
    for u in users:
        s.add(u)
    s.commit()

    # fetch the station_view user and call authorize_create
    u = s.query(m.User).filter(m.User.username=='station_view').one()
    print('User object:', u, 'role type:', type(u.role), 'role value:', u.role)
    try:
        rbac.authorize_create(u, station_rsid='1A1D')
        print('authorize_create returned True (allowed)')
    except Exception as e:
        print('authorize_create raised:', repr(e))
finally:
    s.close()
