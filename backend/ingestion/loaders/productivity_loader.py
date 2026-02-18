import os
import pandas as pd
import sqlite3
from typing import Optional


def load_productivity(con: sqlite3.Connection, path: str, batch_id: str) -> int:
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.xls', '.xlsx'):
        df = pd.read_excel(path, engine='openpyxl')
    else:
        df = pd.read_csv(path)

    df = df.fillna("")
    cols = [str(c).strip().upper() for c in df.columns]

    # heuristics for common columns
    recruiter_col = None
    prod_col = None
    for c in cols:
        if 'RECRUITER' in c or 'RECRUIT' in c:
            recruiter_col = c
        if 'PRODUCTIVITY' in c or 'PRODUCTIVITYRATE' in c or 'RATE' == c:
            prod_col = c

    if not recruiter_col or not prod_col:
        raise ValueError("Required productivity columns not found")

    cur = con.cursor()
    rows = []
    for _, r in df.iterrows():
        recruiter = r.get(recruiter_col)
        prod = float(r.get(prod_col)) if pd.notna(r.get(prod_col)) and r.get(prod_col) != '' else None
        rows.append((batch_id, recruiter, prod, None, None))

    cur.executemany("INSERT INTO fact_productivity(batch_id, recruiter, productivity_rate, metric_value, imported_at) VALUES (?,?,?,?,?)", rows)
    con.commit()
    return len(rows)
