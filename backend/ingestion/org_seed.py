"""
Seed org_units table from an RSID Excel file placed at /uploads/RSID_USAREC.xlsx

Usage (on droplet):
  sudo docker compose exec -T backend python /app/backend/ingestion/org_seed.py
"""
import os
import sqlite3
import uuid
import pandas as pd

DB = os.getenv('DB_PATH', '/app/recruiting.db')
XLSX = '/uploads/RSID_USAREC.xlsx'

def split_code_name(s):
    s = str(s or '').strip()
    if not s:
        return None, None
    if ' - ' in s:
        code, name = s.split(' - ', 1)
        return code.strip(), name.strip()
    return s.strip(), None

def ensure_tables(con):
    cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS org_units (
      unit_id TEXT PRIMARY KEY,
      level TEXT NOT NULL,
      unit_code TEXT NOT NULL,
      parent_unit_id TEXT,
      name TEXT,
      metadata TEXT,
      created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
      updated_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
      UNIQUE(level, unit_code)
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS org_unit_aliases (
      alias_id TEXT PRIMARY KEY,
      alias_code TEXT NOT NULL,
      alias_type TEXT NOT NULL,
      unit_id TEXT NOT NULL,
      source_system TEXT,
      confidence REAL DEFAULT 1.0
    )''')
    con.commit()

def upsert_unit(con, level, unit_code, name=None, parent_unit_id=None):
    cur = con.cursor()
    # try to find existing
    cur.execute('SELECT unit_id FROM org_units WHERE level=? AND unit_code=?', (level, unit_code))
    row = cur.fetchone()
    if row:
        uid = row[0]
        cur.execute('''UPDATE org_units SET name=COALESCE(?, name), parent_unit_id=COALESCE(?, parent_unit_id), updated_at=(strftime('%Y-%m-%dT%H:%M:%fZ','now')) WHERE unit_id=?''', (name, parent_unit_id, uid))
    else:
        uid = 'u_' + uuid.uuid4().hex
        cur.execute('''INSERT INTO org_units(unit_id, level, unit_code, parent_unit_id, name, created_at, updated_at) VALUES(?,?,?,?,?,(strftime('%Y-%m-%dT%H:%M:%fZ','now')),(strftime('%Y-%m-%dT%H:%M:%fZ','now')))''', (uid, level, unit_code, parent_unit_id, name))
    con.commit()
    return uid

def seed_from_xlsx():
    print('DB:', DB)
    print('XLSX:', XLSX, 'exists:', os.path.exists(XLSX))
    if not os.path.exists(XLSX):
        raise SystemExit('Missing RSID Excel at %s' % XLSX)
    df = pd.read_excel(XLSX, header=2).fillna("")
    con = sqlite3.connect(DB)
    ensure_tables(con)
    # collect uniq units
    for _, r in df.iterrows():
        cmd_code, cmd_name = split_code_name(r.get('CMD',''))
        bde_code, bde_name = split_code_name(r.get('BDE',''))
        bn_code, bn_name   = split_code_name(r.get('BN',''))
        co_code, co_name   = split_code_name(r.get('CO',''))
        stn_code, stn_name = split_code_name(r.get('STN',''))

        # seed in order
        if cmd_code:
            cmd_id = upsert_unit(con, 'USAREC', cmd_code, cmd_name, None)
        else:
            cmd_id = None
        if bde_code:
            bde_id = upsert_unit(con, 'BDE', bde_code, bde_name, cmd_id)
        else:
            bde_id = None
        if bn_code:
            bn_id = upsert_unit(con, 'BN', bn_code, bn_name, bde_id)
        else:
            bn_id = None
        if co_code:
            co_id = upsert_unit(con, 'CO', co_code, co_name, bn_id)
        else:
            co_id = None
        if stn_code:
            stn_id = upsert_unit(con, 'STN', stn_code, stn_name, co_id)
    con.close()
    print('OK: seeded org_units from', XLSX)

if __name__ == '__main__':
    seed_from_xlsx()
