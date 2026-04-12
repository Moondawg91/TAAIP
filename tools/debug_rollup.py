import sqlite3
conn=sqlite3.connect('data/taaip.sqlite3')
conn.row_factory=sqlite3.Row
cur=conn.cursor()
cur.execute("SELECT id FROM org_unit WHERE rsid=? COLLATE NOCASE", ('USAREC',))
r = cur.fetchone()
if not r:
    print('USAREC not found')
else:
    oid=r['id']
    sql=f'''WITH RECURSIVE subs(id, rsid, depth) AS (
            SELECT id, rsid, 0 FROM org_unit WHERE id = ?
            UNION ALL
            SELECT o.id, o.rsid, subs.depth+1 FROM org_unit o JOIN subs ON o.parent_id = subs.id WHERE subs.depth < 50
        ) SELECT rsid FROM subs WHERE rsid IS NOT NULL;'''
    cur.execute(sql,(oid,))
    rsids=[row['rsid'] for row in cur.fetchall()]
    print('descendants:', rsids)
    cur.execute('CREATE TEMP TABLE IF NOT EXISTS tmp_rsids (rsid TEXT)')
    cur.execute('DELETE FROM tmp_rsids')
    for r in rsids:
        cur.execute('INSERT INTO tmp_rsids(rsid) VALUES (?)', (r,))
    conn.commit()
    cur.execute('SELECT activity_id, rsid, title FROM fact_emm_activity WHERE rsid IN (SELECT rsid FROM tmp_rsids)')
    rows = cur.fetchall()
    print('matched rows count:', len(rows))
    for row in rows:
        print(dict(row))
conn.close()
