#!/usr/bin/env python3
import sqlite3
from datetime import datetime

DB='data/taaip.sqlite3'

def canonical(rsid,echelon=None):
    if not rsid:
        return None
    s=str(rsid).upper()
    if s.startswith('B') and s[1:].isdigit():
        return s
    if echelon and str(echelon).upper()=='BDE' and s.isdigit():
        return f"B{int(s):03d}"
    if s.isdigit() and len(s)<=2:
        return f"B{int(s):03d}"
    return s

def main():
    conn=sqlite3.connect(DB)
    conn.row_factory=sqlite3.Row
    cur=conn.cursor()
    cur.execute("PRAGMA table_info('org_unit')")
    cols=[r[1] for r in cur.fetchall()]
    if 'unit_key' not in cols:
        cur.execute("ALTER TABLE org_unit ADD COLUMN unit_key TEXT;")
        conn.commit()
    cur.execute("SELECT id, rsid, echelon, unit_key FROM org_unit")
    rows=cur.fetchall()
    updated=0
    for r in rows:
        rs=r[1]
        ech=r[2]
        uk=r[3]
        desired=canonical(rs,ech)
        if desired and (uk!=desired):
            cur.execute("UPDATE org_unit SET unit_key=?, updated_at=? WHERE id=?", (desired, datetime.utcnow().isoformat()+'Z', r[0]))
            updated+=1
    conn.commit()
    print('Backfilled unit_key rows updated=',updated)
    conn.close()

if __name__=='__main__':
    main()
