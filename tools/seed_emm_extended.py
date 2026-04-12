import sqlite3
from datetime import datetime

conn = sqlite3.connect('data/taaip.sqlite3')
cur = conn.cursor()

today = '2026-04-01'
rows = []
rsids = ['USAREC','STN_DEMO_01','STN_DEMO_CHILD','STN_DEMO_02','STN_DEMO_02_A','STN_DEMO_03','STN_DEMO_03_A','STN_DEMO_03_B']
for i, r in enumerate(rsids, start=1):
    aid = f'ea_ext_{r.lower()}'
    title = f'Ext Seed {r}'
    mac = f'MAC_{i}'
    activity_type = 'TRAIN' if i%2==0 else 'EXERCISE'
    status = 'COMPLETED'
    begin = today
    end = '2026-04-02'
    fy = 2026
    qtr = 3
    rsm = '2026-04'
    rows.append((aid, r, r, mac, title, activity_type, status, begin, end, fy, qtr, rsm))

for r in rows:
    try:
        cur.execute('DELETE FROM fact_emm_activity WHERE activity_id = ?', (r[0],))
    except Exception:
        pass
    cur.execute('''INSERT INTO fact_emm_activity(activity_id, rsid, unit_name, mac, title, activity_type, activity_status, begin_date, end_date, fy, qtr_num, rsm_month)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', r)

conn.commit()
print('EMM_EXT_SEED_DONE', len(rows))
for aid in [r[0] for r in rows]:
    cur.execute('SELECT activity_id, rsid, title, begin_date FROM fact_emm_activity WHERE activity_id=?', (aid,))
    print(cur.fetchone())
conn.close()
