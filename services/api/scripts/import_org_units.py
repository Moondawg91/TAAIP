#!/usr/bin/env python3
"""Safe, idempotent org_unit CSV importer.

Usage examples:
  .venv/bin/python services/api/scripts/import_org_units.py --csv /path/to/units.csv --dry-run
  .venv/bin/python services/api/scripts/import_org_units.py --csv /path/to/units.csv

This script upserts rows into the `org_unit` table by `rsid`.
It supports flexible header names and a two-pass parent linking step.
"""
import argparse
import csv
import os
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional

DB_PATH_ENV = "TAAIP_DB_PATH"


def get_db_path() -> str:
    return os.getenv(DB_PATH_ENV, "./data/taaip.sqlite3")


HEADER_ALIASES = {
    'display_name': ['display_name', 'name', 'unit_name'],
    'echelon': ['echelon', 'level', 'org_level'],
    'rsid': ['rsid', 'unit_code', 'unit_id'],
    'parent_rsid': ['parent_rsid', 'parent_unit', 'parent_code'],
    'uic': ['uic', 'uic_code'],
}


def normalize_row(raw: Dict[str, str], col_map: Dict[str, str]) -> Dict[str, Optional[str]]:
    out = {}
    for key in HEADER_ALIASES.keys():
        col = col_map.get(key)
        val = raw.get(col) if col else None
        if isinstance(val, str):
            val = val.strip()
            if val == '':
                val = None
        out[key] = val
    # normalize echelon to uppercase if present
    if out.get('echelon'):
        out['echelon'] = out['echelon'].upper()
    return out


def detect_columns(headers: List[str]) -> Dict[str, str]:
    """Return mapping from canonical name -> csv header name (if found)."""
    lower = {h.lower(): h for h in headers}
    mapping: Dict[str, str] = {}
    for canon, aliases in HEADER_ALIASES.items():
        for a in aliases:
            if a.lower() in lower:
                mapping[canon] = lower[a.lower()]
                break
    return mapping


def connect_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_indexes(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    # ensure required columns exist before creating indexes
    cur.execute("PRAGMA table_info('org_unit')")
    cols = {r['name'] for r in cur.fetchall()}
    # Add missing columns safely (SQLite supports ADD COLUMN)
    alter_needed = []
    if 'display_name' not in cols:
        cur.execute("ALTER TABLE org_unit ADD COLUMN display_name TEXT;")
        alter_needed.append('display_name')
    if 'echelon' not in cols:
        cur.execute("ALTER TABLE org_unit ADD COLUMN echelon TEXT;")
        alter_needed.append('echelon')
    if 'rsid' not in cols:
        cur.execute("ALTER TABLE org_unit ADD COLUMN rsid TEXT;")
        alter_needed.append('rsid')
    if 'parent_rsid' not in cols:
        cur.execute("ALTER TABLE org_unit ADD COLUMN parent_rsid TEXT;")
        alter_needed.append('parent_rsid')
    if 'parent_id' not in cols:
        cur.execute("ALTER TABLE org_unit ADD COLUMN parent_id INTEGER;")
        alter_needed.append('parent_id')
    if 'uic' not in cols:
        cur.execute("ALTER TABLE org_unit ADD COLUMN uic TEXT;")
        alter_needed.append('uic')
    if 'source' not in cols:
        cur.execute("ALTER TABLE org_unit ADD COLUMN source TEXT;")
        alter_needed.append('source')
    if 'created_at' not in cols:
        cur.execute("ALTER TABLE org_unit ADD COLUMN created_at TEXT;")
        alter_needed.append('created_at')
    if 'updated_at' not in cols:
        cur.execute("ALTER TABLE org_unit ADD COLUMN updated_at TEXT;")
        alter_needed.append('updated_at')
    if 'record_status' not in cols:
        cur.execute("ALTER TABLE org_unit ADD COLUMN record_status TEXT DEFAULT 'active';")
        alter_needed.append('record_status')
    if 'unit_key' not in cols:
        cur.execute("ALTER TABLE org_unit ADD COLUMN unit_key TEXT;")
        alter_needed.append('unit_key')
    if alter_needed:
        conn.commit()
    # Create indexes only if the columns exist
    try:
        if 'rsid' in cols or 'rsid' in alter_needed:
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_org_unit_rsid ON org_unit(rsid);")
    except Exception:
        pass
    try:
        if 'parent_rsid' in cols or 'parent_rsid' in alter_needed:
            cur.execute("CREATE INDEX IF NOT EXISTS ix_org_unit_parent_rsid ON org_unit(parent_rsid);")
    except Exception:
        pass
    try:
        if 'echelon' in cols or 'echelon' in alter_needed:
            cur.execute("CREATE INDEX IF NOT EXISTS ix_org_unit_echelon ON org_unit(echelon);")
    except Exception:
        pass
    try:
        if 'unit_key' in cols or 'unit_key' in alter_needed:
            cur.execute("CREATE INDEX IF NOT EXISTS ix_org_unit_unit_key ON org_unit(unit_key);")
    except Exception:
        pass
    conn.commit()


def upsert_rows(conn: sqlite3.Connection, rows: List[Dict[str, Any]], source: str, dry_run: bool=False) -> Dict[str,int]:
    cur = conn.cursor()
    inserted = 0
    updated = 0
    skipped = 0
    samples = []
    for r in rows:
        rsid = r.get('rsid')
        name = r.get('display_name')
        if not rsid or not name:
            skipped += 1
            print(f"Skipping row missing rsid/display_name: {r}")
            continue
        # compute canonical unit_key for storage/UI
        def _canonical_unit_key(rsid_val, echelon_hint=None):
            if not rsid_val:
                return None
            s = str(rsid_val).upper()
            if s.startswith('B') and s[1:].isdigit():
                return s
            if echelon_hint and echelon_hint.upper() == 'BDE' and s.isdigit():
                return f"B{int(s):03d}"
            if s.isdigit() and len(s) <= 2:
                return f"B{int(s):03d}"
            return s
        unit_key_val = _canonical_unit_key(rsid, r.get('echelon'))
        now = datetime.utcnow().isoformat() + 'Z'
        # check existing
        cur.execute("SELECT id, display_name, echelon, parent_rsid, uic, unit_key FROM org_unit WHERE rsid=?", (rsid,))
        exist = cur.fetchone()
        if exist:
            # determine if update required
            need_update = False
            updates = {}
            if exist['display_name'] != name:
                updates['display_name'] = name
                need_update = True
            if (r.get('echelon') or None) != (exist['echelon'] or None):
                updates['echelon'] = r.get('echelon')
                need_update = True
            if (r.get('parent_rsid') or None) != (exist['parent_rsid'] or None):
                updates['parent_rsid'] = r.get('parent_rsid')
                need_update = True
            if (r.get('uic') or None) != (exist['uic'] or None):
                updates['uic'] = r.get('uic')
                need_update = True
            # ensure unit_key is persisted/updated (sqlite3.Row doesn't support .get)
            try:
                existing_unit_key = exist['unit_key'] if 'unit_key' in exist.keys() else None
            except Exception:
                existing_unit_key = None
            if unit_key_val and (existing_unit_key or None) != unit_key_val:
                updates['unit_key'] = unit_key_val
                need_update = True
            if need_update:
                if not dry_run:
                    set_clause = ', '.join([f"{k}=?" for k in updates.keys()]) + ", updated_at=?"
                    params = list(updates.values()) + [now, rsid]
                    cur.execute(f"UPDATE org_unit SET {set_clause} WHERE rsid=?", params)
                updated += 1
            else:
                skipped += 1
        else:
            if not dry_run:
                cur.execute(
                    "INSERT INTO org_unit(display_name, name, type, echelon, rsid, parent_rsid, uic, unit_key, source, created_at, updated_at, record_status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (name, name, None, r.get('echelon'), rsid, r.get('parent_rsid'), r.get('uic'), unit_key_val, source, now, now, 'active')
                )
            inserted += 1
        if len(samples) < 10:
            samples.append({'rsid': rsid, 'display_name': name, 'echelon': r.get('echelon'), 'parent_rsid': r.get('parent_rsid')})
    if not dry_run:
        conn.commit()
    return {'inserted': inserted, 'updated': updated, 'skipped': skipped, 'samples': samples}


def link_parents(conn: sqlite3.Connection, dry_run: bool=False) -> Dict[str,int]:
    cur = conn.cursor()
    cur.execute("SELECT id, rsid, parent_rsid FROM org_unit WHERE parent_rsid IS NOT NULL")
    rows = cur.fetchall()
    linked = 0
    failed = 0
    for r in rows:
        pid = None
        parent_rsid = r['parent_rsid']
        cur.execute("SELECT id FROM org_unit WHERE rsid=?", (parent_rsid,))
        p = cur.fetchone()
        if p:
            pid = p['id']
            if not dry_run:
                cur.execute("UPDATE org_unit SET parent_id=?, updated_at=? WHERE id=?", (pid, datetime.utcnow().isoformat() + 'Z', r['id']))
            linked += 1
        else:
            failed += 1
            print(f"Parent not found for rsid={r['rsid']} parent_rsid={parent_rsid}")
    if not dry_run:
        conn.commit()
    return {'linked': linked, 'failed': failed}


def main():
    p = argparse.ArgumentParser(description='Import org units CSV into org_unit table')
    p.add_argument('--csv', dest='csv', required=True, help='Path to CSV file')
    p.add_argument('--dry-run', dest='dry_run', action='store_true', default=False, help='Do not write to DB')
    p.add_argument('--source', dest='source', default='usarec_master')
    p.add_argument('--truncate', dest='truncate', action='store_true', default=False, help='Truncate existing org_unit rows from this source')
    args = p.parse_args()

    if not os.path.exists(args.csv):
        print(f"CSV file not found: {args.csv}")
        return

    dbp = get_db_path()
    conn = connect_db(dbp)
    try:
        ensure_indexes(conn)
        if args.truncate and not args.dry_run:
            print(f"Truncating org_unit rows for source={args.source}")
            cur = conn.cursor()
            cur.execute("DELETE FROM org_unit WHERE source=?", (args.source,))
            conn.commit()

        with open(args.csv, newline='') as fh:
            reader = csv.DictReader(fh)
            headers = reader.fieldnames or []
            col_map = detect_columns(headers)
            if not col_map.get('rsid') or not col_map.get('display_name'):
                print("Warning: CSV missing an identifiable rsid or display_name column. Detected columns:", col_map)
            parsed = [normalize_row(row, col_map) for row in reader]

        # First pass upsert
        stats = upsert_rows(conn, parsed, args.source, dry_run=args.dry_run)
        print(f"Upsert summary: inserted={stats['inserted']} updated={stats['updated']} skipped={stats['skipped']}")
        print("Sample rows:")
        for s in stats['samples']:
            print(s)

        # Second pass: link parents
        link_stats = link_parents(conn, dry_run=args.dry_run)
        print(f"Parent linking: linked={link_stats['linked']} failed={link_stats['failed']}")

    finally:
        conn.close()


if __name__ == '__main__':
    main()
