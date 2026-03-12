import sqlite3
from typing import Dict, Any


def load_enlistments(df, ctx: Dict[str, Any], conn: sqlite3.Connection) -> int:
    """Map dataframe columns to fact_enlistments and insert rows. Returns rows_loaded."""
    cur = conn.cursor()
    rows_loaded = 0
    for _, r in df.iterrows():
        try:
            unit = r.get('unit_rsid') or r.get('unit') or ctx.get('unit_rsid')
            period = r.get('period') or r.get('month') or r.get('period_date')
            contracts = r.get('contracts') if 'contracts' in r else (r.get('count') if 'count' in r else None)
            cur.execute('''INSERT INTO fact_enlistments (unit_rsid, echelon, period_date, contracts, source_system, dataset_key) VALUES (?,?,?,?,?,?)''', (unit, None, period, contracts, ctx.get('source_system'), ctx.get('dataset_key')))
            rows_loaded += 1
        except Exception:
            pass
    conn.commit()
    return rows_loaded
