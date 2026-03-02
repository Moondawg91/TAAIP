import sqlite3
from typing import List, Dict, Any, Optional
from . import db


def normalize_echelon(echelon: Optional[str]) -> Optional[str]:
    if not echelon:
        return None
    return str(echelon).upper()


def get_children(conn: sqlite3.Connection, unit_rsid: str) -> List[Dict[str, Any]]:
    """Return direct children of a unit (by rsid). Each child is a dict with rsid, name, type/echelon."""
    try:
        cur = conn.cursor()
        cur.execute('SELECT id FROM org_unit WHERE rsid = ? OR upper(rsid)=? LIMIT 1', (unit_rsid, str(unit_rsid).upper()))
        row = cur.fetchone()
        if not row or row.get('id') is None:
            return []
        oid = row.get('id')
        cur.execute('SELECT rsid, name, type FROM org_unit WHERE parent_id = ? AND record_status != "deleted"', (oid,))
        out = []
        for r in cur.fetchall():
            out.append({'unit_rsid': r.get('rsid'), 'unit_name': r.get('name'), 'echelon': r.get('type')})
        return out
    except Exception:
        return []


def get_descendant_units(conn, unit_rsid: str, max_depth: int = 50) -> List[str]:
    """Return list of rsids including the given unit and all descendants using a recursive CTE.
    Falls back to [unit_rsid] if not found or on error.
    """
    try:
        cur = conn.cursor()
        cur.execute('SELECT id FROM org_unit WHERE rsid = ? OR upper(rsid)=? LIMIT 1', (unit_rsid, str(unit_rsid).upper()))
        row = cur.fetchone()
        if not row or row.get('id') is None:
            return [unit_rsid]
        oid = row.get('id')
        sql = f'''WITH RECURSIVE subs(id, rsid, depth) AS (
            SELECT id, rsid, 0 FROM org_unit WHERE id = ?
            UNION ALL
            SELECT o.id, o.rsid, subs.depth+1 FROM org_unit o JOIN subs ON o.parent_id = subs.id WHERE subs.depth < {int(max_depth)}
        ) SELECT rsid FROM subs WHERE rsid IS NOT NULL;'''
        cur.execute(sql, (oid,))
        rows = [r.get('rsid') for r in cur.fetchall() if r.get('rsid')]
        return rows if rows else [unit_rsid]
    except Exception:
        return [unit_rsid]


def get_ancestors(conn, unit_rsid: str, max_depth: int = 50) -> List[str]:
    """Return ancestor rsids ordered from parent up to root."""
    try:
        cur = conn.cursor()
        cur.execute('SELECT id FROM org_unit WHERE rsid = ? OR upper(rsid)=? LIMIT 1', (unit_rsid, str(unit_rsid).upper()))
        row = cur.fetchone()
        if not row or row.get('id') is None:
            return []
        oid = row.get('id')
        sql = f'''WITH RECURSIVE parents(id, rsid, depth) AS (
            SELECT parent_id, (SELECT rsid FROM org_unit WHERE id = org_unit.parent_id), 0 FROM org_unit WHERE id = ?
            UNION ALL
            SELECT o.parent_id, o2.rsid, parents.depth+1 FROM org_unit o JOIN parents ON o.id = parents.id JOIN org_unit o2 ON o.parent_id = o2.id WHERE parents.depth < {int(max_depth)}
        ) SELECT rsid FROM parents WHERE rsid IS NOT NULL;'''
        cur.execute(sql, (oid,))
        rows = [r.get('rsid') for r in cur.fetchall() if r.get('rsid')]
        return rows
    except Exception:
        return []

