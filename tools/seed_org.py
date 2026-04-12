import sqlite3
conn = sqlite3.connect('data/taaip.sqlite3')
cur = conn.cursor()
# ensure USAREC exists
cur.execute("SELECT id FROM org_unit WHERE rsid = ? COLLATE NOCASE", ('USAREC',))
row = cur.fetchone()
if row:
    usid = row[0]
else:
    cur.execute("INSERT INTO org_unit(name,type,rsid,created_at,record_status) VALUES (?,?,?,?,?)", ('USAREC HQ','HQ','USAREC','2026-04-01','active'))
    usid = cur.lastrowid
# ensure STN_DEMO_01 exists under USAREC
cur.execute("SELECT id FROM org_unit WHERE rsid = ? COLLATE NOCASE", ('STN_DEMO_01',))
row = cur.fetchone()
if row:
    s1 = row[0]
else:
    cur.execute("INSERT INTO org_unit(name,type,parent_id,rsid,created_at,record_status) VALUES (?,?,?,?,?,?)", ('Station Demo 01','STATION',usid,'STN_DEMO_01','2026-04-01','active'))
    s1 = cur.lastrowid
# ensure STN_DEMO_CHILD exists under STN_DEMO_01
cur.execute("SELECT id FROM org_unit WHERE rsid = ? COLLATE NOCASE", ('STN_DEMO_CHILD',))
row = cur.fetchone()
if row:
    s2 = row[0]
else:
    cur.execute("INSERT INTO org_unit(name,type,parent_id,rsid,created_at,record_status) VALUES (?,?,?,?,?,?)", ('Station Demo Child','PLT',s1,'STN_DEMO_CHILD','2026-04-01','active'))
    s2 = cur.lastrowid
conn.commit()
print('ORG_SEED_OK', {'USAREC_id': usid, 'STN_DEMO_01_id': s1, 'STN_DEMO_CHILD_id': s2})
conn.close()
