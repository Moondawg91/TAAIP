#!/usr/bin/env python3
from services.api.app.db import get_db_conn
from services.api.app.routers import v2 as v2router
import json

def pick_demo_lead(conn):
    cur = conn.cursor()
    # try school_id S123 then S999 then any
    for val in ('S123','S999'):
        try:
            cur.execute("SELECT * FROM leads WHERE school_id=? OR zip5=? LIMIT 1", (val, val))
            r = cur.fetchone()
            if r:
                return dict(r)
        except Exception:
            pass
    try:
        cur.execute("SELECT * FROM leads LIMIT 1")
        r = cur.fetchone()
        return dict(r) if r else None
    except Exception:
        return None


def print_lead(conn, lead_id):
    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM leads WHERE lead_id = ? LIMIT 1', (lead_id,))
        r = cur.fetchone()
        if not r:
            print('Lead not found')
            return
        print(json.dumps(dict(r), indent=2, default=str))
    except Exception as e:
        print('Error printing lead', e)


def main():
    conn = get_db_conn()
    lead = pick_demo_lead(conn)
    if not lead:
        print('No demo lead found in DB')
        return
    lid = lead.get('lead_id') or lead.get('id')
    print('Found lead before update:')
    print_lead(conn, lid)

    payload = {'lead_id': lid, 'status': 'contacted', 'note': 'left voicemail (sim)'}
    print('\nCalling mark_lead_contacted handler...')
    try:
        res = v2router.mark_lead_contacted(payload)
        print('Handler response:', res)
    except Exception as e:
        print('Handler raised exception:', e)

    print('\nAfter update:')
    print_lead(conn, lid)
    conn.close()

if __name__ == '__main__':
    main()
