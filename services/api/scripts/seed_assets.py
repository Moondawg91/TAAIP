"""Idempotent seed for USAREC Assets Master List.
Run with: python services/api/scripts/seed_assets.py
"""
from services.api.app import db
import json
from datetime import datetime

def now():
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

ASSETS = [
    {
        'asset_id': 'mac_basic_kit',
        'asset_name': 'MAC Basic Exhibit Kit',
        'asset_type': 'MAC',
        'category': 'Activation',
        'supported_objectives': ['engagement','activation'],
        'supported_tactics': ['exhibit','digital'],
        'description': 'Portable exhibit kit with table, banner, lead device',
        'constraints': {'lead_time_days':7},
        'requires_approval_level': 'CO',
        'enabled': True,
        'version': 1
    },
    {
        'asset_id': 'digital_boost_1000',
        'asset_name': 'Digital Ad Boost (1k)',
        'asset_type': 'DIGITAL',
        'category': 'Awareness',
        'supported_objectives': ['awareness'],
        'supported_tactics': ['digital'],
        'description': 'Small digital ad budget boost',
        'constraints': {'min_spend':1000},
        'requires_approval_level': 'STN',
        'enabled': True,
        'version': 1
    }
]

def seed():
    # ensure schema exists
    try:
        db.init_schema()
    except Exception:
        pass
    conn = db.connect()
    try:
        cur = conn.cursor()
        for a in ASSETS:
            cur.execute('SELECT id, version FROM asset_catalog WHERE asset_id = ? LIMIT 1', (a['asset_id'],))
            row = cur.fetchone()
            now_ts = now()
            if row:
                # if version differs, perform an update
                if row['version'] != a.get('version'):
                    cur.execute('UPDATE asset_catalog SET asset_name=?, asset_type=?, category=?, supported_objectives=?, supported_tactics=?, description=?, constraints=?, requires_approval_level=?, enabled=?, version=?, updated_at=? WHERE asset_id=?', (
                        a['asset_name'], a['asset_type'], a['category'], json.dumps(a.get('supported_objectives') or []), json.dumps(a.get('supported_tactics') or []), a.get('description'), json.dumps(a.get('constraints') or {}), a.get('requires_approval_level'), 1 if a.get('enabled') else 0, a.get('version'), now_ts, a['asset_id']
                    ))
            else:
                cur.execute('INSERT INTO asset_catalog(asset_id, asset_name, asset_type, category, supported_objectives, supported_tactics, description, constraints, requires_approval_level, enabled, version, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', (
                    a['asset_id'], a['asset_name'], a['asset_type'], a['category'], json.dumps(a.get('supported_objectives') or []), json.dumps(a.get('supported_tactics') or []), a.get('description'), json.dumps(a.get('constraints') or {}), a.get('requires_approval_level'), 1 if a.get('enabled') else 0, a.get('version'), now_ts, now_ts
                ))
        conn.commit()
    finally:
        conn.close()

if __name__ == '__main__':
    seed()
    print('seed_assets: done')
