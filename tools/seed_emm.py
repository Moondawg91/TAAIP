import sqlite3

conn = sqlite3.connect('data/taaip.sqlite3')
cur = conn.cursor()
rows = [
    ('ea_seed_stn_demo_01', 'STN_DEMO_01', 'Station Demo 01', 'MAC1', 'Demo Event', 'TRAIN', 'COMPLETED', '2026-04-01', '2026-04-02', 2026, 3, '2026-04'),
    ('ea_seed_stn_child_02', 'STN_DEMO_CHILD', 'Station Demo Child', 'MAC2', 'Child Event', 'TRAIN', 'COMPLETED', '2026-04-03', '2026-04-04', 2026, 3, '2026-04'),
    ('ea_seed_usarec_03', 'USAREC', 'USAREC HQ', 'MAC-US', 'USAREC Rollup Event', 'EXERCISE', 'COMPLETED', '2026-04-05', '2026-04-06', 2026, 3, '2026-04')
]
for r in rows:
    # ensure deterministic upsert: remove existing activity_id then insert
    try:
        cur.execute('DELETE FROM fact_emm_activity WHERE activity_id = ?', (r[0],))
    except Exception:
        pass
    cur.execute('''INSERT INTO fact_emm_activity(activity_id, rsid, unit_name, mac, title, activity_type, activity_status, begin_date, end_date, fy, qtr_num, rsm_month)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', r)
conn.commit()
print('SEED_DONE', len(rows))
# verify
for aid in [r[0] for r in rows]:
    cur.execute('SELECT activity_id, rsid, title, begin_date FROM fact_emm_activity WHERE activity_id=?', (aid,))
    print(cur.fetchone())
conn.close()
