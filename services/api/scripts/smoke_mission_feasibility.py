#!/usr/bin/env python3
import requests
import os

BASE = os.getenv('TAAIP_API_BASE', 'http://127.0.0.1:8000')

def main():
    url = f"{BASE}/api/v2/mission-feasibility/summary"
    try:
        r = requests.get(url, timeout=5)
        print('STATUS', r.status_code)
        try:
            print(r.json())
        except Exception:
            print(r.text)
    except Exception as e:
        print('ERROR', e)

if __name__ == '__main__':
    main()
