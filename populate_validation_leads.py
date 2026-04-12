from services.api.app.db import connect
from datetime import datetime
import uuid

conn = connect()
cur = conn.cursor()
now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

leads = []
for i in range(8):
    lid = f"val-{uuid.uuid4().hex[:8]}"
    leads.append((lid, f"Test{i}", f"User{i}", f"test{i}@example.com", f"555-010{i}", 'EMM', 20+i, 'High School', '12345', 'S123', now))

# Insert into leads table; columns may vary—use explicit columns from db schema
try:
    cur.executemany('''INSERT OR REPLACE INTO leads (lead_id, first_name, last_name, email, phone, source, age, education_level, cbsa_code, campaign_source, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)''', leads)
    conn.commit()
    print('Inserted', len(leads), 'validation leads')
except Exception as e:
    print('Failed to insert leads:', e)
finally:
    try:
        conn.close()
    except Exception:
        pass
