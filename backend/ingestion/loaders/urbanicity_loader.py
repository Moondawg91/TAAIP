import os
import pandas as pd
import sqlite3


def load_urbanicity(con: sqlite3.Connection, path: str, batch_id: str) -> int:
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.xls', '.xlsx'):
        df = pd.read_excel(path, engine='openpyxl')
    else:
        df = pd.read_csv(path)

    df = df.fillna("")
    cols = [str(c).strip().upper() for c in df.columns]

    cbsa_col = None
    urb_col = None
    for c in cols:
        if 'CBSA' in c:
            cbsa_col = c
        if 'URBANIC' in c or 'URBANICITY' in c:
            urb_col = c

    if not cbsa_col or not urb_col:
        raise ValueError('Required CBSA/Urbanicity columns not found')

    cur = con.cursor()
    rows = []
    for _, r in df.iterrows():
        cbsa = r.get(cbsa_col)
        pct = float(r.get(urb_col)) if pd.notna(r.get(urb_col)) and r.get(urb_col) != '' else None
        rows.append((batch_id, cbsa, pct, None))

    cur.executemany("INSERT INTO fact_urbanicity(batch_id, cbsa, urbanicity_percent, imported_at) VALUES (?,?,?,?)", rows)
    con.commit()
    return len(rows)
