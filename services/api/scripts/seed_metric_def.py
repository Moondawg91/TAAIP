"""Seed a demo metric_definition row to test SQL execution path for /api/metrics/query.

Run: PYTHONPATH=. python services/api/scripts/seed_metric_def.py
"""
from services.api.app.db import connect

def seed():
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("INSERT OR REPLACE INTO metric_definition(metric_id, name, description, sql_definition) VALUES (?,?,?,?)", (
            'demo_funnel_counts', 'Demo Funnel Counts', 'Select aggregated funnel counts from fact_funnel_daily',
            "SELECT unit_key, stage, SUM(count) as total_count FROM fact_funnel_daily WHERE (date_key = :fy OR :fy IS NULL) GROUP BY unit_key, stage"
        ))
        conn.commit()
        print('seeded metric_definition demo_funnel_counts')
    except Exception as e:
        print('seed metric failed', e)

if __name__ == '__main__':
    seed()
