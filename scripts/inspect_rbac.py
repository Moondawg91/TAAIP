#!/usr/bin/env python3
import os
os.environ['TAAIP_DB_PATH'] = './taaip_dev.db'

from services.api.app.database import engine, SessionLocal
from services.api.app.models import Base

# Recreate DB schema
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

from services.api.app.db import init_db
init_db()

from services.api.app import main as app_module
from services.api.app import models, auth

# Seed minimal org structure and a station
db = SessionLocal()
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

c1 = models.StationZipCoverage(station_rsid='1A1D', zip_code='12345', market_category=models.MarketCategory.MK)
c2 = models.StationZipCoverage(station_rsid='1B1D', zip_code='23456', market_category=models.MarketCategory.MW)
db.add_all([c1, c2])
db.commit()

u = models.User(username='station_view', role=models.UserRole.STATION_VIEW, scope='1A1D')
db.add(u)
db.commit()

token = auth.create_token_for_user(u)

from fastapi.testclient import TestClient
client = TestClient(app_module.app)

r = client.get('/api/org/stations/1A1D/zip-coverage', headers={'Authorization': f'Bearer {token}'})
print('STATUS', r.status_code)
print('TEXT', r.text)
try:
    print('JSON KEYS', list(r.json().keys()))
    print('JSON', r.json())
except Exception as e:
    print('JSON PARSE ERROR', e)
