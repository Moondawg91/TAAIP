#!/usr/bin/env python3
import requests
import sys
import json

BASE = 'http://127.0.0.1:8000'

def main():
    # sanity check org tree
    r = requests.get(f"{BASE}/api/v2/org/tree?unit_rsid=USAREC&depth=4")
    print('org/tree status', r.status_code)
    try:
        print(json.dumps(r.json(), indent=2)[:1000])
    except Exception:
        print(r.text[:1000])

    # post two rows
    payload = {
        'period_key': 'CURRENT_MONTH',
        'rsm_month': None,
        'rows': [
            {'station_rsid': 'STN_DEMO_01', 'cmpnt_cd': 'RA', 'loss_code': '0-9_DAYS', 'loss_count': 2},
            {'station_rsid': 'STN_DEMO_01', 'cmpnt_cd': 'AR', 'loss_code': '0-9_DAYS', 'loss_count': 1}
        ]
    }
    r = requests.post(f"{BASE}/api/v2/station/dep-loss/manual", json=payload)
    print('ingest status', r.status_code, r.text)

    # get dashboard
    r = requests.get(f"{BASE}/api/v2/station/dashboard/dep-loss?station_rsid=STN_DEMO_01")
    print('dashboard status', r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print(r.text)

if __name__ == '__main__':
    main()
