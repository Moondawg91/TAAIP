"""Seed minimal demo data for the Phase-1 warehouse schema so dashboards can show values.

Run: python services/api/scripts/seed_demo_metrics.py
"""
from services.api.app.db import connect

def seed():
    conn = connect()
    cur = conn.cursor()
    # ensure our minimal warehouse schema tables exist by executing the SQL file if present
    try:
        with open('services/api/db/warehouse_schema.sql', 'r') as f:
            cur.executescript(f.read())
    except Exception:
        pass

    # seed dim_date for two days
    cur.execute("INSERT OR IGNORE INTO dim_date(date_key, date_iso, year, month, day) VALUES ('2026-02-01','2026-02-01',2026,2,1)")
    cur.execute("INSERT OR IGNORE INTO dim_date(date_key, date_iso, year, month, day) VALUES ('2026-02-02','2026-02-02',2026,2,2)")

    # seed a unit
    cur.execute("INSERT OR IGNORE INTO dim_unit(unit_key, rsid, display_name, echelon_type, parent_key, sort_order) VALUES ('USAREC','USAREC_RSID','USAREC','DIV',NULL,1)")

    # seed funnel facts
    cur.execute("INSERT INTO fact_funnel_daily(date_key, unit_key, stage, count, ingested_at) VALUES ('2026-02-01','USAREC','lead',10,datetime('now'))")
    cur.execute("INSERT INTO fact_funnel_daily(date_key, unit_key, stage, count, ingested_at) VALUES ('2026-02-02','USAREC','lead',12,datetime('now'))")

    conn.commit()
    conn.close()
    print('Seeded demo warehouse data')

if __name__ == '__main__':
    seed()
