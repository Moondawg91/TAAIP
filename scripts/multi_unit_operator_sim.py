#!/usr/bin/env python3
import sys
import time
import uuid
import os
from datetime import datetime

# Ensure local package imports work when run via python -c hack
sys.path.insert(0, '.')

from services.api.app.db import get_db_conn, safe_add_column
from services.api.app.routers import v2 as v2router


def seed_units_and_leads(conn, units=5, leads_per_unit=20):
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    inserted = 0
    schools = []
    for u in range(units):
        school_id = f'SIM_S{100+u}'
        zip5 = f'{90000+u}'
        schools.append((school_id, zip5))
        for i in range(leads_per_unit):
            lid = f"sim-{school_id}-{i}-{uuid.uuid4().hex[:6]}"
            first = f"F{u}-{i}"
            last = "Test"
            email = f"{lid}@example.com"
            phone = f"555-{9000+u*100+i:04d}"
            campaign = school_id
            created = now
            # Insert in a best-effort way ignoring schema differences
            cols = ['lead_id','first_name','last_name','email','phone','source','age','education_level','cbsa_code','campaign_source','school_id','zip5','created_at']
            vals = [lid, first, last, email, phone, 'SIM', None, 'HS', zip5, campaign, school_id, zip5, created]
            placeholders = ','.join(['?']*len(vals))
            try:
                cur.execute(f"INSERT OR REPLACE INTO leads({','.join(cols)}) VALUES({placeholders})", tuple(vals))
                inserted += 1
            except Exception:
                # fallback: try minimal columns
                try:
                    cur.execute("INSERT OR REPLACE INTO leads(lead_id,first_name,last_name,campaign_source,school_id,zip5,created_at) VALUES(?,?,?,?,?,?,?)", (lid, first, last, campaign, school_id, zip5, created))
                    inserted += 1
                except Exception as e:
                    print('Insert failed for', lid, 'err', e)
    try:
        conn.commit()
    except Exception:
        pass
    return schools, inserted


def simulate_operator_actions(conn, schools, per_unit_mark=8):
    cur = conn.cursor()
    total_marked = 0
    errors = 0
    durations = []
    for school_id, zip5 in schools:
        # fetch leads for that school
        try:
            cur.execute('SELECT lead_id FROM leads WHERE school_id=? OR campaign_source=? LIMIT ?', (school_id, school_id, per_unit_mark*2))
            rows = cur.fetchall()
            lead_ids = [r[0] if isinstance(r, tuple) else r['lead_id'] for r in rows]
        except Exception:
            try:
                cur.execute('SELECT lead_id FROM leads WHERE campaign_source=? LIMIT ?', (school_id, per_unit_mark*2))
                rows = cur.fetchall()
                lead_ids = [r[0] if isinstance(r, tuple) else r['lead_id'] for r in rows]
            except Exception:
                lead_ids = []
        # mark first N leads contacted
        to_mark = lead_ids[:per_unit_mark]
        for lid in to_mark:
            start = time.time()
            try:
                payload = {'lead_id': lid, 'status': 'contacted', 'note': 'simulated contact'}
                v2router.mark_lead_contacted(payload)
                total_marked += 1
            except Exception as e:
                errors += 1
                print('Error marking lead', lid, e)
            durations.append(time.time() - start)
    return total_marked, errors, durations


def inspect_sample_before_after(conn, sample_lead_id):
    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM leads WHERE lead_id=? LIMIT 1', (sample_lead_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception:
        return None


def main():
    # Safety: require explicit opt-in to run simulation scripts in non-dev environments
    if os.getenv('ALLOW_SIMULATION') != '1' and '--allow-sim' not in sys.argv:
        print("Simulation disabled: set ALLOW_SIMULATION=1 or pass --allow-sim to run.")
        sys.exit(1)

    conn = get_db_conn()
    # ensure notes column exists
    try:
        safe_add_column(conn, 'leads', 'notes', 'TEXT')
    except Exception:
        pass

    print('Seeding units and leads...')
    t0 = time.time()
    schools, inserted = seed_units_and_leads(conn, units=5, leads_per_unit=20)
    t1 = time.time()
    print(f'Inserted {inserted} leads for {len(schools)} schools in {t1-t0:.2f}s')

    # pick a sample lead to inspect
    sample = None
    cur = conn.cursor()
    cur.execute('SELECT lead_id FROM leads LIMIT 1')
    r = cur.fetchone()
    if r:
        sample = r[0] if isinstance(r, tuple) else r['lead_id']

    before = inspect_sample_before_after(conn, sample) if sample else None
    print('\nSample before update:\n', before)

    print('\nSimulating operator actions (mark contacted) ...')
    t2 = time.time()
    total_marked, errors, durations = simulate_operator_actions(conn, schools, per_unit_mark=8)
    t3 = time.time()
    avg_mark_time = (sum(durations)/len(durations)) if durations else 0
    print(f'Operator marked {total_marked} leads with {errors} errors in {t3-t2:.2f}s (avg {avg_mark_time*1000:.1f}ms per mark)')

    after = inspect_sample_before_after(conn, sample) if sample else None
    print('\nSample after update:\n', after)

    # quick checks
    cur.execute('SELECT COUNT(*) FROM leads')
    total_leads = cur.fetchone()[0]
    print(f'Final DB lead count: {total_leads}')

    conn.close()

if __name__ == '__main__':
    main()
