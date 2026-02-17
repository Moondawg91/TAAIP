import os
import sqlite3
import pandas as pd
from typing import Optional


def load_sama(con: sqlite3.Connection, path: str, batch_id: str) -> None:
    """Load SAMA dataset into `sama_data` table.

    Expects columns (case-insensitive): ZIP CODE, STATION, SAMA SCORE
    """
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.xls', '.xlsx'):
        df = pd.read_excel(path, engine='openpyxl')
    else:
        # try CSV
        df = pd.read_csv(path)

    # Normalize columns to uppercase stripped
    df.columns = [str(c).strip().upper() for c in df.columns]

    required = {"ZIP CODE", "STATION", "SAMA SCORE"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns for SAMA: {missing}")

    cur = con.cursor()
    for _, row in df.iterrows():
        zip_code = row.get("ZIP CODE")
        station = row.get("STATION")
        sama_score = row.get("SAMA SCORE")
        cur.execute(
            """INSERT INTO sama_data(zip_code, station, sama_score, batch_id)
               VALUES(?,?,?,?)""",
            (zip_code, station, sama_score, batch_id)
        )
    con.commit()
