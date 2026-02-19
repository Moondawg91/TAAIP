#!/usr/bin/env python3
"""Seed LOEs, command priorities, marketing activities and fact_production rows."""
import os, uuid
os.environ.setdefault('TAAIP_DB_PATH', './data/taaip.sqlite3')

from services.api.app.db import connect
from datetime import datetime

now = datetime.utcnow().isoformat()
conn = connect()
try:
    cur = conn.cursor()
    # LOE (legacy integer loe)
    cur.execute("INSERT INTO loe(org_unit_id, fy, qtr, name, description, created_at) VALUES (?,?,?,?,?,?)",
                (1, '2026', 'Q1', 'Phase4 LOE', 'Seeded LOE for testing', now))
    # domain loe (string id)
    loe_id = 'loe-1'
    try:
        cur.execute("INSERT OR IGNORE INTO loes(id, scope_type, scope_value, title, description, created_by, created_at) VALUES (?,?,?,?,?,?,?)",
                    (loe_id, 'CO', '1A1', 'Domain LOE 1', 'Seeded domain LOE', 'system', now))
    except Exception:
        pass

    # command priority
    cur.execute("INSERT INTO command_priorities(org_unit_id, title, description, rank, created_at, updated_at) VALUES (?,?,?,?,?,?)",
                (1, 'Top Priority', 'Seeded priority', 1, now, now))
    priority_id = cur.lastrowid

    # assign loe to priority (priority_loe table expects loe_id text)
    cur.execute("INSERT OR IGNORE INTO priority_loe(priority_id, loe_id, created_at) VALUES (?,?,?)", (priority_id, loe_id, now))

    # marketing activity
    cur.execute("INSERT OR IGNORE INTO marketing_activities(activity_id, event_id, activity_type, campaign_name, channel, data_source, impressions, engagement_count, awareness_metric, activation_conversions, reporting_date, metadata, cost, created_at, import_job_id, record_status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ('ma-1', None, 'social_media', 'Seed Campaign', 'twitter', 'seed', 1000, 50, 0.5, 10, '2026-02-01', '{}', 200.0, now, None, 'active'))

    # fact production rows
    fp_rows = [
        ('fp-1', '1', '2026-02-01', 'throughput', 100.0),
        ('fp-2', '1', '2026-02-01', 'appointments', 5.0),
        ('fp-3', '1', '2026-02-01', 'leads', 20.0)
    ]
    for fid, org, datek, metric, val in fp_rows:
        try:
            cur.execute('INSERT OR REPLACE INTO fact_production(id, org_unit_id, date_key, metric_key, metric_value, source_system, import_job_id, created_at) VALUES (?,?,?,?,?,?,?,?)', (fid, str(org), str(datek), str(metric), float(val), 'seed', None, now))
        except Exception:
            pass

    conn.commit()
    print('Phase4 more seed complete')
finally:
    conn.close()
