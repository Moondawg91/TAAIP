import sqlite3
from datetime import datetime


def refresh_agg_kpis(conn: sqlite3.Connection, unit_rsid: str = None):
    """Simple KPI refresh: populate a small agg_kpis_period table with contract counts per unit/month."""
    cur = conn.cursor()
    # ensure table
    try:
        cur.executescript('''
        CREATE TABLE IF NOT EXISTS agg_kpis_period (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_rsid TEXT,
            period TEXT,
            contracts INTEGER,
            updated_at TEXT
        );
        ''')
    except Exception:
        pass

    # recompute aggregates
    where = ''
    params = []
    if unit_rsid:
        where = 'WHERE f.unit_rsid = ?'
        params = [unit_rsid]
    try:
        cur.execute(f"SELECT f.unit_rsid, f.period_date, SUM(COALESCE(f.contracts,0)) as contracts FROM fact_enlistments f {where} GROUP BY f.unit_rsid, f.period_date", params)
        rows = cur.fetchall()
        for unit, period, contracts in rows:
            cur.execute('INSERT INTO agg_kpis_period (unit_rsid, period, contracts, updated_at) VALUES (?,?,?,?)', (unit, period, contracts, datetime.utcnow().isoformat()))
        conn.commit()
    except Exception:
        pass
