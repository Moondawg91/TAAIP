"""Importer: USAREC org hierarchy (column-based XLSX)

Implements safe, idempotent ingestion of a column-based hierarchy with columns:
  CMD | BDE | BN | CO | STN

This creates/ensures `org_unit` table and indexes, creates a backup table if org_unit
is non-empty, and upserts nodes without destructive deletes.
"""
from typing import Optional, Dict, Any
import datetime

from ..db import connect


def _now_iso():
    return datetime.datetime.utcnow().isoformat()


def _ensure_schema(conn):
    cur = conn.cursor()
    # Create table if missing (safe)
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='org_unit'")
    exists = cur.fetchone()
    if not exists:
        cur.execute('''
            CREATE TABLE org_unit (
                unit_rsid TEXT,
                parent_rsid TEXT,
                name TEXT,
                echelon TEXT,
                active INTEGER DEFAULT 1,
                created_at TEXT
            )
        ''')
        try:
            cur.execute('CREATE UNIQUE INDEX IF NOT EXISTS uq_org_unit_rsid ON org_unit(unit_rsid)')
        except Exception:
            pass
        try:
            cur.execute('CREATE INDEX IF NOT EXISTS idx_org_unit_parent ON org_unit(parent_rsid)')
        except Exception:
            pass
        try:
            cur.execute('CREATE INDEX IF NOT EXISTS idx_org_unit_echelon ON org_unit(echelon)')
        except Exception:
            pass
        conn.commit()
        return

    # Table exists: ensure required columns exist; if legacy columns present, populate new ones
    cur.execute("PRAGMA table_info('org_unit')")
    cols = [r['name'] if isinstance(r, dict) and 'name' in r.keys() else (r[1] if len(r) > 1 else None) for r in cur.fetchall()]

    def _add_col(col_def: str):
        try:
            cur.execute(f'ALTER TABLE org_unit ADD COLUMN {col_def}')
        except Exception:
            pass

    # Ensure unit_rsid
    if 'unit_rsid' not in cols:
        _add_col('unit_rsid TEXT')
        # try to populate from common legacy columns
        if 'rsid' in cols:
            try:
                cur.execute("UPDATE org_unit SET unit_rsid = rsid WHERE unit_rsid IS NULL OR unit_rsid = ''")
            except Exception:
                pass
        elif 'unit_key' in cols:
            try:
                cur.execute("UPDATE org_unit SET unit_rsid = unit_key WHERE unit_rsid IS NULL OR unit_rsid = ''")
            except Exception:
                pass

    # Ensure parent_rsid exists (populate from parent_id if present)
    if 'parent_rsid' not in cols:
        _add_col('parent_rsid TEXT')
        if 'parent_id' in cols:
            # populate parent_rsid by joining to id->rsid if rsid exists
            try:
                cur.execute("UPDATE org_unit SET parent_rsid = (SELECT rsid FROM org_unit AS p WHERE p.id = org_unit.parent_id) WHERE parent_rsid IS NULL OR parent_rsid = ''")
            except Exception:
                pass

    # Ensure name exists (map from display_name or name)
    if 'name' not in cols:
        _add_col('name TEXT')
        if 'display_name' in cols:
            try:
                cur.execute("UPDATE org_unit SET name = display_name WHERE name IS NULL OR name = ''")
            except Exception:
                pass

    # Ensure echelon exists (map from type)
    if 'echelon' not in cols:
        _add_col('echelon TEXT')
        if 'type' in cols:
            try:
                cur.execute("UPDATE org_unit SET echelon = type WHERE echelon IS NULL OR echelon = ''")
            except Exception:
                pass

    # Ensure created_at
    if 'created_at' not in cols:
        _add_col('created_at TEXT')

    # Ensure active flag
    if 'active' not in cols:
        _add_col('active INTEGER DEFAULT 1')

    # Ensure indexes
    try:
        cur.execute('CREATE INDEX IF NOT EXISTS idx_org_unit_parent ON org_unit(parent_rsid)')
    except Exception:
        pass
    try:
        cur.execute('CREATE INDEX IF NOT EXISTS idx_org_unit_echelon ON org_unit(echelon)')
    except Exception:
        pass
    try:
        cur.execute('CREATE UNIQUE INDEX IF NOT EXISTS uq_org_unit_rsid ON org_unit(unit_rsid)')
    except Exception:
        pass
    conn.commit()


def _backup_if_needed(conn) -> Optional[str]:
    cur = conn.cursor()
    cur.execute('SELECT COUNT(1) AS cnt FROM org_unit')
    r = cur.fetchone()
    cnt = r['cnt'] if r and 'cnt' in r.keys() else (r[0] if r else 0)
    if cnt and int(cnt) > 0:
        ts = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_name = f'org_unit_backup_{ts}'
        cur.execute(f'CREATE TABLE IF NOT EXISTS {backup_name} AS SELECT * FROM org_unit')
        conn.commit()
        print(f'Backup created: {backup_name} ({cnt} rows copied)')
        return backup_name
    return None


def _upsert_node(conn, unit_rsid: str, parent_rsid: Optional[str], name: Optional[str], echelon: Optional[str]):
    if not unit_rsid:
        return
    cur = conn.cursor()
    now = _now_iso()
    # Check existence
    cur.execute('SELECT unit_rsid, parent_rsid, name, echelon FROM org_unit WHERE unit_rsid=? LIMIT 1', (unit_rsid,))
    existing = cur.fetchone()
    if not existing:
        # Insert new row
        cur.execute('INSERT INTO org_unit (unit_rsid, parent_rsid, name, echelon, active, created_at) VALUES (?,?,?,?,?,?)', (unit_rsid, parent_rsid, name, echelon, 1, now))
        return

    # existing row: update parent if provided and different (do not null-out)
    try:
        existing_parent = existing.get('parent_rsid') if hasattr(existing, 'get') else existing[1]
    except Exception:
        existing_parent = None
    if parent_rsid and existing_parent != parent_rsid:
        cur.execute('UPDATE org_unit SET parent_rsid=? WHERE unit_rsid=?', (parent_rsid, unit_rsid))

    # update name/echelon only if missing
    try:
        cur_name = existing.get('name') if hasattr(existing, 'get') else existing[2]
        cur_echelon = existing.get('echelon') if hasattr(existing, 'get') else existing[3]
    except Exception:
        cur_name = None
        cur_echelon = None
    if (not cur_name) and name:
        cur.execute('UPDATE org_unit SET name=? WHERE unit_rsid=?', (name, unit_rsid))
    if (not cur_echelon) and echelon:
        cur.execute('UPDATE org_unit SET echelon=? WHERE unit_rsid=?', (echelon, unit_rsid))


def process_and_load(df, ctx: Dict[str, Any], conn, run_id: Optional[str] = None) -> int:
    """Process dataframe with columns CMD,BDE,BN,CO,STN and upsert into org_unit.

    Returns number of logical rows processed (not necessarily inserted nodes).
    """
    _ensure_schema(conn)
    backup = _backup_if_needed(conn)
    # Ensure USAREC root exists before ingesting rows so BDE parent links can be anchored.
    def ensure_root_cmd(conn):
        cur = conn.cursor()
        cur.execute("SELECT unit_rsid FROM org_unit WHERE unit_rsid='USAREC' LIMIT 1")
        if not cur.fetchone():
            now = _now_iso()
            try:
                cur.execute('INSERT INTO org_unit (unit_rsid, parent_rsid, name, echelon, active, created_at) VALUES (?,?,?,?,?,?)', ('USAREC', None, 'USAREC', 'CMD', 1, now))
                conn.commit()
                print('Inserted USAREC root')
            except Exception:
                conn.rollback()
    ensure_root_cmd(conn)
    cur = conn.cursor()
    rows_in = 0

    # iterate rows
    try:
        for idx, r in df.fillna('').iterrows():
            rows_in += 1
            cmd = (r.get('CMD') or r.get('Cmd') or r.get('cmd') or '').strip() if hasattr(r, 'get') else ''
            bde = (r.get('BDE') or r.get('Bde') or '').strip() if hasattr(r, 'get') else ''
            bn = (r.get('BN') or r.get('Bn') or '').strip() if hasattr(r, 'get') else ''
            co = (r.get('CO') or r.get('Co') or '').strip() if hasattr(r, 'get') else ''
            stn = (r.get('STN') or r.get('Stn') or r.get('STN RSID') or '').strip() if hasattr(r, 'get') else ''

            # skip if entire row blank
            if not any([cmd, bde, bn, co, stn]):
                continue

            # Upsert in hierarchical order
            if cmd:
                _upsert_node(conn, cmd, None, cmd, 'USAREC')
            if bde:
                # Force BDE parent to USAREC per importer rules
                parent = 'USAREC'
                _upsert_node(conn, bde, parent, bde, 'BDE')
            if bn:
                parent = bde if bde else (cmd if cmd else None)
                _upsert_node(conn, bn, parent, bn, 'BN')
            if co:
                parent = bn if bn else (bde if bde else (cmd if cmd else None))
                _upsert_node(conn, co, parent, co, 'COMPANY')
            if stn:
                parent = co if co else (bn if bn else (bde if bde else (cmd if cmd else None)))
                _upsert_node(conn, stn, parent, stn, 'STATION')

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise

    # post-checks
    cur.execute("SELECT COUNT(1) as cnt FROM org_unit WHERE echelon='USAREC'")
    rc = cur.fetchone()
    root_cnt = rc['cnt'] if rc and 'cnt' in rc.keys() else (rc[0] if rc else 0)
    # total nodes
    cur.execute('SELECT COUNT(1) as cnt FROM org_unit')
    t = cur.fetchone()
    total = t['cnt'] if t and 'cnt' in t.keys() else (t[0] if t else 0)
    # echelon counts
    cur.execute("SELECT echelon, COUNT(1) as cnt FROM org_unit GROUP BY echelon")
    rows = cur.fetchall()
    echelon_counts = {}
    for r in rows:
        if isinstance(r, dict):
            echelon_counts[r.get('echelon')] = r.get('cnt')
        else:
            echelon_counts[r[0]] = r[1]

    # validations (log warnings)
    if root_cnt != 1:
        print(f'Warning: root_count={root_cnt} (expected 1)')
    if (echelon_counts.get('BDE') or 0) < 1:
        print('Warning: no BDE nodes found')
    if (echelon_counts.get('BN') or 0) < 1:
        print('Warning: no BN nodes found')

    # return rows processed (for import run accounting)
    return rows_in
