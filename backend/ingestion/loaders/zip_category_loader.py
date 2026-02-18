import os
import pandas as pd
import sqlite3
from typing import Optional


def load_zip_category(con: sqlite3.Connection, path: str, batch_id: str) -> int:
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.xls', '.xlsx'):
        df = pd.read_excel(path, engine='openpyxl')
    else:
        df = pd.read_csv(path)

    df = df.fillna("")
    cols = [str(c).strip().upper() for c in df.columns]

    # find zip and cat columns
    zip_col = None
    cat_cols = []
    for c in cols:
        if 'ZIP' in c:
            zip_col = c
        if c.startswith('CAT') or 'CATEGORY' in c:
            cat_cols.append(c)

    if not zip_col:
        raise ValueError("ZIP column not found for ZIP-by-category loader")

    cur = con.cursor()
    rows = []
    for _, r in df.iterrows():
        zipv = r.get(zip_col)
        cats = [float(r.get(c)) if r.get(c) != '' else None for c in cat_cols[:9]]
        # pad to 9
        cats = (cats + [None]*9)[:9]
        rows.append((batch_id, None, zipv, *cats, None))

    cur.executemany(
        "INSERT INTO fact_zip_category(batch_id, rsid, zip, cat1,cat2,cat3,cat4,cat5,cat6,cat7,cat8,cat9, imported_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        rows
    )
    con.commit()
    return len(rows)
