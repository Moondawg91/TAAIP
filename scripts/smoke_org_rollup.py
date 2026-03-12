#!/usr/bin/env python3
"""Simple smoke script to verify org rollup and mission-feasibility endpoints.

Run with: PYTHONPATH=. python3 scripts/smoke_org_rollup.py
"""
import os
import sys
import urllib.request
import json

BASE = os.environ.get('TAAIP_API_URL', 'http://127.0.0.1:8000')

def get(path):
    url = BASE + path
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.getcode(), r.read().decode('utf-8')
    except Exception as e:
        return None, str(e)

def pretty_head(txt, n=20):
    try:
        data = json.loads(txt)
        s = json.dumps(data, indent=2)
        return '\n'.join(s.splitlines()[:n])
    except Exception:
        return '\n'.join(txt.splitlines()[:n])

def main():
    paths = [
        '/api/v2/org/tree?unit_rsid=USAREC&depth=4',
        '/api/v2/analytics/enlistments/bn?unit_rsid=USAREC&rollup=1',
        '/api/v2/mission-feasibility/summary?unit_rsid=USAREC'
    ]
    for p in paths:
        code, body = get(p)
        print('---', p, '->', code)
        if body:
            print(pretty_head(body, 30))
        print('\n')

if __name__ == '__main__':
    main()
