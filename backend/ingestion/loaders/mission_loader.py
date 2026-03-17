import os
import pandas as pd
import sqlite3


def load_mission(con: sqlite3.Connection, path: str, batch_id: str) -> int:
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.xls', '.xlsx'):
        df = pd.read_excel(path, engine='openpyxl')
    else:
        df = pd.read_csv(path)

    df = df.fillna("")
    cols = [str(c).strip().upper() for c in df.columns]

    # find mission category column and a value column
    mission_col = None
    value_col = None
    for c in cols:
        if 'MISSION' in c and 'CATEGORY' in c or c == 'MISSION':
            mission_col = c
        if c in ('VALUE','COUNT','TOTAL','NUM') or 'TOTAL' in c:
            value_col = c

    if not mission_col:
        raise ValueError('Mission category column not found')

    cur = con.cursor()
    rows = []
    for _, r in df.iterrows():
        mission = r.get(mission_col)
        val = float(r.get(value_col)) if value_col and pd.notna(r.get(value_col)) and r.get(value_col) != '' else None
        rows.append((batch_id, mission, val, None))
    # Determine target table shape: some runtimes (services) define a different
    # `fact_mission_category` schema. If the loader's expected columns exist,
    # insert as originally intended; otherwise adapt to the existing schema
    # by writing into (mission_category, metric_name, metric_value, source_system, ingest_run_id).
    try:
        cur.execute("PRAGMA table_info('fact_mission_category')")
        cols = [r[1] for r in cur.fetchall()]
    except Exception:
        cols = []

    if 'batch_id' in cols:
        cur.executemany("INSERT INTO fact_mission_category(batch_id, mission_category, value, imported_at) VALUES (?,?,?,?)", rows)
    else:
        # adapt rows to existing schema
        adapted = []
        for b, mission, val, imp in rows:
            adapted.append((mission, 'value', val, 'USAREC_MISSION', b))
        cur.executemany("INSERT INTO fact_mission_category(mission_category, metric_name, metric_value, source_system, ingest_run_id) VALUES (?,?,?,?,?)", adapted)
    con.commit()
    return len(rows)
