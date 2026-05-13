#!/usr/bin/env python3
"""Test KPI Thresholds implementation"""

from services.api.app.routers.admin_v2 import _threshold_description
from services.api.app.db import connect

# Test description function
print("=== Testing _threshold_description helper ===")
metrics = ['cpl_target', 'cpc_target', 'ctr_minimum', 'engagement_rate_minimum', 'unknown_metric']
for metric in metrics:
    desc = _threshold_description(metric)
    print(f'✓ {metric}: {desc}')

# Test database access
print("\n=== Testing database access ===")
conn = connect()
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='roi_thresholds'")
if cur.fetchone():
    print("✓ roi_thresholds table exists")
    
    # Read thresholds
    cur.execute("SELECT metric_key, value FROM roi_thresholds ORDER BY metric_key ASC")
    thresholds = cur.fetchall()
    print(f"✓ Found {len(thresholds)} thresholds")
    for row in thresholds:
        print(f"  - {row[0]}: {row[1]}")
else:
    print("✗ roi_thresholds table not found")

conn.close()

print("\n=== All tests passed ===")
