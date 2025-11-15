"""
Simple mock sync script for EMM/iKrome that posts sample payloads
to the running TAAIP service `/api/v2/marketing/sync` endpoint.

Run: python3 mocks/mock_sources.py
"""
import time
import requests
import json
import os

BASE = os.environ.get('TAAIP_BASE', 'http://localhost:8000')

def sync_emm():
    payload = {
        "source_system": "emm",
        "sync_data": {
            "auto_campaign_1": {
                "type": "social_media",
                "campaign": "Auto Sync Campaign",
                "channel": "Facebook",
                "impressions": 1200,
                "engagement": 120,
                "awareness": 0.78,
                "activation": 12
            }
        }
    }
    r = requests.post(f"{BASE}/api/v2/marketing/sync", json=payload)
    print('EMM sync:', r.status_code, r.text)

def sync_ikrome():
    payload = {
        "source_system": "ikrome",
        "sync_data": {
            "ik_campaign": {
                "type": "display",
                "campaign": "iKrome Display",
                "channel": "Display",
                "impressions": 800,
                "engagement": 40,
                "awareness": 0.65,
                "activation": 8
            }
        }
    }
    r = requests.post(f"{BASE}/api/v2/marketing/sync", json=payload)
    print('iKrome sync:', r.status_code, r.text)

if __name__ == '__main__':
    print('Starting mock syncs to', BASE)
    sync_emm()
    time.sleep(1)
    sync_ikrome()
    print('Done')
