import os
import pandas as pd
import sqlite3


def load_test_scores(con: sqlite3.Connection, path: str, batch_id: str) -> int:
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.xls', '.xlsx'):
        df = pd.read_excel(path, engine='openpyxl')
    else:
        df = pd.read_csv(path)

    df = df.fillna("")
    cols = [str(c).strip().upper() for c in df.columns]

    # Look for a test name and score columns
    test_col = None
    score_col = None
    for c in cols:
        if 'TEST' in c and 'NAME' in c or c == 'TEST':
            test_col = c
        if 'SCORE' in c or 'AVERAGE' in c or 'AVG' in c:
            score_col = c

    if not score_col:
        raise ValueError('Score column not found')

    cur = con.cursor()
    rows = []
    for _, r in df.iterrows():
        test = r.get(test_col) if test_col else None
        avg = float(r.get(score_col)) if pd.notna(r.get(score_col)) and r.get(score_col) != '' else None
        cnt = None
        rows.append((batch_id, test, avg, cnt, None))

    cur.executemany("INSERT INTO fact_test_scores(batch_id, test_name, avg_score, count, imported_at) VALUES (?,?,?,?,?)", rows)
    con.commit()
    return len(rows)
