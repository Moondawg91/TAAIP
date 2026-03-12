#!/usr/bin/env python3
"""Seed minimal domain data for local development and verification.

This script is idempotent and safe to run multiple times.
"""
import time
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)

from services.api.app.db import connect


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def seed():
    conn = connect()
    cur = conn.cursor()
    t = now()
    try:
        # org_unit
        cur.execute("INSERT OR IGNORE INTO org_unit(name,type,created_at) VALUES (?,?,?)", ('Default Unit','Station', t))
        cur.execute("SELECT id FROM org_unit WHERE name=?", ('Default Unit',))
        row = cur.fetchone()
        org_id = row[0] if row else None

        # user
        cur.execute("INSERT OR IGNORE INTO users(username,display_name,email,created_at) VALUES (?,?,?,?)", ('seed.user','Seed User','seed@example.com', t))
        cur.execute("SELECT id FROM users WHERE username=?", ('seed.user',))
        row = cur.fetchone(); user_id = row[0] if row else None

        # fy_budget and budget_line_item
        cur.execute("INSERT OR IGNORE INTO fy_budget(org_unit_id,fy,total_allocated,created_at) VALUES (?,?,?,?)", (org_id, 2026, 4000.0, t))
        cur.execute("SELECT id FROM fy_budget WHERE org_unit_id=? AND fy=?", (org_id, 2026))
        row = cur.fetchone(); fy_id = row[0] if row else None
        # seed two budget line items
        cur.execute("INSERT OR IGNORE INTO budget_line_item(fy_budget_id,qtr,event_id,category,amount,appropriation_type,funding_source,eor_code,is_under_cr,status,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (fy_id, 1, None, 'venue', 1500.0, 'OMA', 'BDE_LAMP', 'EOR-001', 0, 'committed', t))
        cur.execute("INSERT OR IGNORE INTO budget_line_item(fy_budget_id,qtr,event_id,category,amount,appropriation_type,funding_source,eor_code,is_under_cr,status,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (fy_id, 1, None, 'travel', 2500.0, 'OMA', 'BN_LAMP', 'EOR-002', 0, 'planned', t))

        # projects
        cur.execute("INSERT OR IGNORE INTO projects(project_id,title,description,owner,status,percent_complete,created_at) VALUES (?,?,?,?,?,?,?)", ('proj-seed','Seed Project','Auto-seeded project','seed.user','active',0.0,t))

        # event
        cur.execute("INSERT OR IGNORE INTO event(org_unit_id,name,start_dt,end_dt,created_at,loe) VALUES (?,?,?,?,?,?)", (org_id, 'Seed Event', t, t, t, 1.0))

        # expenses table (may not exist in minimal schemas)
        try:
            cur.execute("INSERT OR IGNORE INTO expenses(id,project_id,event_id,amount,fy,created_at) VALUES (?,?,?,?,?,?)", ('exp-seed','proj-seed', None, 0.0, 2026, t))
        except Exception:
            pass

        conn.commit()
        print('seeded minimal rows')
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == '__main__':
    seed()
