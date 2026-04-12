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

# create several deterministic descendant stations under USAREC
new_stations = [
    ('Station Demo 02', 'STN_DEMO_02', 'STATION', usid),
    ('Station Demo 03', 'STN_DEMO_03', 'STATION', usid),
]
created = {}
for name, rsid, typ, parent in new_stations:
    cur.execute("SELECT id FROM org_unit WHERE rsid = ? COLLATE NOCASE", (rsid,))
    r = cur.fetchone()
    if r:
        created[rsid] = r[0]
    else:
        cur.execute("INSERT INTO org_unit(name,type,parent_id,rsid,created_at,record_status) VALUES (?,?,?,?,?,?)", (name, typ, parent, rsid, '2026-04-01', 'active'))
        created[rsid] = cur.lastrowid

# add children under those stations for more depth
children = [
    ('Station Demo 02 A', 'STN_DEMO_02_A', 'PLT', created['STN_DEMO_02']),
    ('Station Demo 03 A', 'STN_DEMO_03_A', 'PLT', created['STN_DEMO_03']),
    ('Station Demo 03 B', 'STN_DEMO_03_B', 'PLT', created['STN_DEMO_03']),
]
for name, rsid, typ, parent in children:
    cur.execute("SELECT id FROM org_unit WHERE rsid = ? COLLATE NOCASE", (rsid,))
    r = cur.fetchone()
    if r:
        created[rsid] = r[0]
    else:
        cur.execute("INSERT INTO org_unit(name,type,parent_id,rsid,created_at,record_status) VALUES (?,?,?,?,?,?)", (name, typ, parent, rsid, '2026-04-01', 'active'))
        created[rsid] = cur.lastrowid

conn.commit()
created['USAREC'] = usid
print('ORG_EXT_SEED_OK', created)
conn.close()
