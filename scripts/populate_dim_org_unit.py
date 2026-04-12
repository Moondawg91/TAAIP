#!/usr/bin/env python3
"""
Populate `dim_org_unit` from authoritative `org_unit` table.
This script walks the org_unit parent chain to derive cmd/bde/bn/co fields
and upserts rows into dim_org_unit. Idempotent and safe to run repeatedly.

Usage: PYTHONPATH=. python scripts/populate_dim_org_unit.py
"""
import sys
import os
from datetime import datetime

# Ensure package root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.api.app.db import connect


def now_iso():
    return datetime.utcnow().isoformat()


def build_org_map(cur):
    # Determine available columns and map to canonical names
    cur.execute("PRAGMA table_info('org_unit')")
    cols = [r[1] for r in cur.fetchall()]
    # possible column mappings
    unit_col = None
    if 'unit_rsid' in cols:
        unit_col = 'unit_rsid'
    elif 'rsid' in cols:
        unit_col = 'rsid'
    elif 'unit_key' in cols:
        unit_col = 'unit_key'
    elif 'name' in cols:
        # fallback: use name as id (not ideal)
        unit_col = 'name'

    parent_col = 'parent_rsid' if 'parent_rsid' in cols else ('parent_id' if 'parent_id' in cols else None)
    name_col = 'name' if 'name' in cols else None
    echelon_col = 'echelon' if 'echelon' in cols else ('type' if 'type' in cols else None)

    if not unit_col:
        return {}

    select_cols = [unit_col]
    if parent_col:
        select_cols.append(parent_col)
    else:
        select_cols.append('NULL')
    if name_col:
        select_cols.append(name_col)
    else:
        select_cols.append(unit_col)
    if echelon_col:
        select_cols.append(echelon_col)
    else:
        select_cols.append('NULL')

    q = f"SELECT {','.join(select_cols)} FROM org_unit"
    cur.execute(q)
    rows = cur.fetchall()
    org = {}
    for r in rows:
        # sqlite3.Row supports mapping access via column name, use that when available
        try:
            if hasattr(r, 'keys'):
                unit = r[unit_col] if unit_col in r.keys() else r[0]
                parent = r[parent_col] if parent_col and parent_col in r.keys() else r[1] if len(r) > 1 else None
                name = r[name_col] if name_col and name_col in r.keys() else r[2] if len(r) > 2 else None
                echelon = r[echelon_col] if echelon_col and echelon_col in r.keys() else r[3] if len(r) > 3 else None
            else:
                unit = r[0]
                parent = r[1]
                name = r[2]
                echelon = r[3] if len(r) > 3 else None
        except Exception:
            # last-resort tuple-style access
            unit = r[0]
            parent = r[1] if len(r) > 1 else None
            name = r[2] if len(r) > 2 else None
            echelon = r[3] if len(r) > 3 else None
        if unit:
            org[str(unit)] = {'parent': parent, 'name': name, 'echelon': echelon}
    return org


def derive_ancestors(unit, org_map):
    cmd = bde = bn = co = None
    seen = set()
    cur = unit
    depth = 0
    while cur and cur not in seen and depth < 50:
        seen.add(cur)
        node = org_map.get(cur)
        if not node:
            break
        echelon = (node.get('echelon') or '').upper() if isinstance(node.get('echelon'), str) else None
        if echelon in ('USAREC', 'CMD') and not cmd:
            cmd = cur
        elif echelon == 'BDE' and not bde:
            bde = cur
        elif echelon == 'BN' and not bn:
            bn = cur
        elif echelon in ('COMPANY','CO') and not co:
            co = cur
        cur = node.get('parent')
        depth += 1
    return cmd, bde, bn, co


def populate_dim():
    conn = connect()
    cur = conn.cursor()

    # ensure dim_org_unit exists
    cur.execute('''
    CREATE TABLE IF NOT EXISTS dim_org_unit (
      cmd TEXT,
      bde TEXT,
      bn TEXT,
      co TEXT,
      rsid TEXT,
      name TEXT,
      source_system TEXT,
      imported_at TEXT,
      PRIMARY KEY (cmd,bde,bn,co,rsid)
    );
    ''')
    conn.commit()

    org_map = build_org_map(cur)
    inserted = 0
    updated = 0
    now = now_iso()
    # Inspect existing dim_org_unit columns to pick an insertion strategy
    cur.execute("PRAGMA table_info('dim_org_unit')")
    dim_cols = [r[1] for r in cur.fetchall()]

    for unit, meta in org_map.items():
        name = meta.get('name') or unit
        cmd, bde, bn, co = derive_ancestors(unit, org_map)
        try:
            # If dim_org_unit uses the newer analytics schema use that
            if set(['cmd','bde','bn','co','rsid','name']).issubset(set(dim_cols)):
                icmd = cmd or ''
                ibde = bde or ''
                ibn = bn or ''
                ico = co or ''
                cur.execute("INSERT OR REPLACE INTO dim_org_unit (cmd,bde,bn,co,rsid,name,source_system,imported_at) VALUES (?,?,?,?,?,?,?,?)",
                            (icmd, ibde, ibn, ico, unit, name, 'ORG', now))
            else:
                # legacy dim_org_unit: id,name,type,parent_id,rsid,uic,state,city,zip
                parent = meta.get('parent') or ''
                echelon = meta.get('echelon') or ''
                # Fill optional geo fields with empty strings
                cur.execute("INSERT OR REPLACE INTO dim_org_unit (id,name,type,parent_id,rsid,uic,state,city,zip) VALUES (?,?,?,?,?,?,?,?,?)",
                            (unit, name, echelon, parent, unit, '', '', '', ''))
            inserted += 1
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
    try:
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass

    # report counts
    try:
        cur.execute('SELECT COUNT(1) FROM dim_org_unit')
        total = cur.fetchone()[0]
    except Exception:
        total = None
    print(f'Populated dim_org_unit rows (total now: {total})')


if __name__ == '__main__':
    populate_dim()
