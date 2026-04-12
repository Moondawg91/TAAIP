import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('data/taaip.sqlite3')
cur = conn.cursor()
now = datetime.utcnow()

# Insert a few lead_journey_fact demo rows
leads = []
for i in range(1,6):
    lead_id = f'demo-lead-{i}'
    person_key = f'person-demo-{i}'
    unit_rsid = 'STN_DEMO_01' if i%2==0 else 'USAREC'
    lead_created = (now - timedelta(days=30+i)).strftime('%Y-%m-%d')
    contact = None
    appointment = None
    applicant = None
    contract_flag = 0
    contract_dt = None
    if i == 5:
        contract_flag = 1
        contract_dt = (now - timedelta(days=1)).strftime('%Y-%m-%d')
    leads.append((lead_id, person_key, unit_rsid, 'demo', None, None, None, lead_created, contact, appointment, applicant, contract_dt, contract_flag, None, None, None, now.strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d')))

for l in leads:
    try:
        cur.execute('INSERT OR REPLACE INTO lead_journey_fact (lead_id, person_key, unit_rsid, source_type, source_detail, event_id, mac_id, lead_created_dt, contact_made_dt, appointment_dt, applicant_dt, contract_dt, contract_flag, contract_type, mos, afqt_tier, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', l)
    except Exception:
        pass

# Insert spend row
try:
    cur.execute('INSERT OR REPLACE INTO spend_fact (spend_id, unit_rsid, event_id, spend_type, amount, spend_dt, notes) VALUES (?,?,?,?,?,?,?)', ('demo-spend-1', 'USAREC', None, 'ad', 500.0, now.strftime('%Y-%m-%d'), 'demo spend'))
except Exception:
    pass

conn.commit()
print('ROI_DEMO_SEED_DONE')
cur.execute("SELECT COUNT(*) FROM lead_journey_fact WHERE lead_id LIKE 'demo-lead-%'")
print('leads:', cur.fetchone()[0])
cur.execute("SELECT SUM(amount) FROM spend_fact WHERE spend_id='demo-spend-1'")
print('spend:', cur.fetchone()[0])
conn.close()
