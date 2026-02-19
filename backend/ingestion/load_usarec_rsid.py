import os, re, sqlite3, sys
import pandas as pd

DB = os.getenv("DB_PATH") or "/app/recruiting.db"

def split_code_name(x: str):
  x = ("" if pd.isna(x) else str(x)).strip()
  if not x:
    return None, None
  if " - " in x:
    code, name = x.split(" - ", 1)
    return code.strip(), name.strip()
  return x.strip(), None

def detect_header_row(raw: pd.DataFrame) -> int:
  target = {"cmd","bde","bn","co","stn"}
  for i in range(min(30, len(raw))):
    row = [str(v).strip().lower() for v in raw.iloc[i].tolist()]
    if target.issubset(set(row)):
      return i
  return 0

def upsert(cur, code, level, name=None, parent_code=None):
    # Use INSERT OR IGNORE then UPDATE to avoid relying on a specific UNIQUE PK
    cur.execute("""
      INSERT OR IGNORE INTO org_units(level, code, name, parent_code)
      VALUES(?, ?, ?, ?)
    """, (level, code, name, parent_code))
    if name is not None:
        cur.execute("""
          UPDATE org_units SET name=?, parent_code=? WHERE code=?
        """, (name, parent_code, code))

def main(xlsx_path: str):
  raw = pd.read_excel(xlsx_path, sheet_name=0, header=None)
  hdr = detect_header_row(raw)
  df = pd.read_excel(xlsx_path, sheet_name=0, header=hdr)

  df.columns = [str(c).strip().upper() for c in df.columns]

  needed = ["CMD","BDE","BN","CO","STN"]
  missing = [c for c in needed if c not in df.columns]
  if missing:
    print("Missing columns:", missing)
    print("Columns found:", list(df.columns))
    sys.exit(2)

  con = sqlite3.connect(DB)
  cur = con.cursor()

  # ensure tables exist
  cur.execute("""
  CREATE TABLE IF NOT EXISTS org_units (
    org_unit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    level TEXT,
    name TEXT,
    parent_code TEXT,
    created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
  )
  """)
  cur.execute("""
  CREATE TABLE IF NOT EXISTS org_unit_aliases (
    alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
    alias_code TEXT,
    alias_type TEXT,
    canonical_level TEXT,
    canonical_code TEXT,
    source_system TEXT
  )
  """)
  con.commit()

  inserted = {k:0 for k in needed}

  for _, r in df.iterrows():
    cmd = ("" if pd.isna(r.get('CMD')) else str(r.get('CMD'))).strip()
    if not cmd:
      continue
    cmd_code = cmd
    upsert(cur, cmd_code, "CMD", name=cmd_code, parent_code=None)
    inserted['CMD'] += 1

    bn_code, bn_name = split_code_name(r.get('BN'))
    co_code, co_name = split_code_name(r.get('CO'))
    stn_code, stn_name = split_code_name(r.get('STN'))
    bde_code = None
    bde_name = ("" if pd.isna(r.get('BDE')) else str(r.get('BDE'))).strip() or None
    if bn_code and len(bn_code) >= 1:
      bde_code = bn_code[0]

    if bde_code:
      upsert(cur, bde_code, "BDE", name=bde_name, parent_code=cmd_code)
      inserted['BDE'] += 1

    if bn_code:
      upsert(cur, bn_code, "BN", name=bn_name, parent_code=bde_code or cmd_code)
      inserted['BN'] += 1

    if co_code:
      upsert(cur, co_code, "CO", name=co_name, parent_code=bn_code)
      inserted['CO'] += 1

    if stn_code:
      upsert(cur, stn_code, "STN", name=stn_name, parent_code=co_code)
      inserted['STN'] += 1
      cur.execute("""
        INSERT OR IGNORE INTO org_unit_aliases(alias_code, alias_type, canonical_level, canonical_code, source_system)
        VALUES(?,?,?,?,?)
      """, (stn_code, 'RSID', 'STN', stn_code, 'USAREC'))
      cur.execute("""
        INSERT OR IGNORE INTO org_unit_aliases(alias_code, alias_type, canonical_level, canonical_code, source_system)
        VALUES(?,?,?,?,?)
      """, (stn_code, 'STN', 'STN', stn_code, 'USAREC'))

  con.commit()
  con.close()
  print(f"Loaded RSID org tree into {DB} (header_row={hdr})", inserted)

if __name__ == "__main__":
  if len(sys.argv) < 2:
    print("Usage: load_usarec_rsid.py /uploads/RSID_USAREC.xlsx")
    sys.exit(2)
  main(sys.argv[1])
