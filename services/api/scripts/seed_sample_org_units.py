#!/usr/bin/env python3
"""Wrapper to seed the sample USAREC org units using import_org_units.py.

Run from repo root:
  .venv/bin/python services/api/scripts/seed_sample_org_units.py

This will invoke the existing importer against
`services/api/.data/seeds/usarec_units.csv` and write to the DB path
configured by `TAAIP_DB_PATH` (defaults to ./data/taaip.sqlite3).
"""
import os
import sys
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSV = (HERE.parent / '.data' / 'seeds' / 'usarec_units.csv')
IMPORTER = HERE / 'import_org_units.py'

if not CSV.exists():
    print(f"Seed CSV not found: {CSV}")
    sys.exit(2)
if not IMPORTER.exists():
    print(f"Importer not found: {IMPORTER}")
    sys.exit(2)

# Respect TAAIP_DB_PATH if set; otherwise use default
db_path = os.getenv('TAAIP_DB_PATH')
if not db_path:
    # ensure default DB directory exists
    d = Path('./data')
    d.mkdir(parents=True, exist_ok=True)

cmd = [sys.executable, str(IMPORTER), '--csv', str(CSV)]
print('Running:', ' '.join(cmd))
ret = subprocess.call(cmd)
if ret == 0:
    print('Seed completed successfully')
else:
    print('Seed script exited with code', ret)
sys.exit(ret)
