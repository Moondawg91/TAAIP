import io
import pandas as pd
from backend.db import connect


def read_any(contents: bytes, filename: str):
    # Excel
    fname = (filename or '').lower()
    if fname.endswith(('.xlsx', '.xls')):
        xls = pd.ExcelFile(io.BytesIO(contents))
        df = xls.parse(xls.sheet_names[0])
        return df, xls.sheet_names[0], 0
    # CSV
    text = contents.decode('utf-8', errors='ignore')
    lines = text.splitlines()
    header_row = 0
    for i, line in enumerate(lines[:50]):
        parts = [p.strip() for p in line.split(',')]
        if sum(1 for p in parts if p) >= 3 and 'applied' not in line.lower():
            header_row = i
            break
    df = pd.read_csv(io.StringIO(text), skiprows=header_row)
    return df, None, header_row


def normalize_columns(df: pd.DataFrame):
    df = df.dropna(how='all').dropna(axis=1, how='all')
    df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
    return df


def write_facts(batch_id: str, dataset: str, df: pd.DataFrame):
    con = connect()
    try:
        con.execute('DELETE FROM facts WHERE batch_id=?', (batch_id,))
        colmap = {
            'cmd': 'cmd', 'bde': 'bde', 'bn': 'bn', 'co': 'co', 'stn': 'stn', 'zip': 'zipcode', 'zipcode': 'zipcode'
        }
        cols = set(df.columns)
        rows = []
        for _, r in df.iterrows():
            rows.append((
                batch_id,
                dataset,
                str(r[colmap['cmd']]) if colmap['cmd'] in cols else None,
                str(r[colmap['bde']]) if colmap['bde'] in cols else None,
                str(r[colmap['bn']]) if colmap['bn'] in cols else None,
                str(r[colmap['co']]) if colmap['co'] in cols else None,
                str(r[colmap['stn']]) if colmap['stn'] in cols else None,
                str(r['zipcode']) if 'zipcode' in cols else (str(r['zip']) if 'zip' in cols else None),
                None, None, None
            ))
        con.executemany(
            """
            INSERT INTO facts(batch_id,dataset,cmd,bde,bn,co,stn,zipcode,metric_name,metric_value,event_date)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            rows,
        )
        con.commit()
    finally:
        con.close()


def compute_aggs(batch_id: str, dataset: str):
    con = connect()
    try:
        total_rows = con.execute('SELECT COUNT(*) FROM facts WHERE batch_id=?', (batch_id,)).fetchone()[0]
        total_stations = con.execute('SELECT COUNT(DISTINCT stn) FROM facts WHERE batch_id=? AND stn IS NOT NULL', (batch_id,)).fetchone()[0]
        total_companies = con.execute('SELECT COUNT(DISTINCT co) FROM facts WHERE batch_id=? AND co IS NOT NULL', (batch_id,)).fetchone()[0]
        total_battalions = con.execute('SELECT COUNT(DISTINCT bn) FROM facts WHERE batch_id=? AND bn IS NOT NULL', (batch_id,)).fetchone()[0]
        total_brigades = con.execute('SELECT COUNT(DISTINCT bde) FROM facts WHERE batch_id=? AND bde IS NOT NULL', (batch_id,)).fetchone()[0]

        con.execute(
            """
            INSERT OR REPLACE INTO agg_kpis(batch_id,dataset,total_rows,total_stations,total_companies,total_battalions,total_brigades,last_refresh)
            VALUES (?,?,?,?,?,?,?, datetime('now'))
            """,
            (batch_id, dataset, total_rows, total_stations, total_companies, total_battalions, total_brigades),
        )

        con.execute('DELETE FROM agg_charts WHERE batch_id=?', (batch_id,))

        for label, value in con.execute(
            "SELECT bde, COUNT(DISTINCT bn) as v FROM facts WHERE batch_id=? AND bde IS NOT NULL GROUP BY bde ORDER BY v DESC",
            (batch_id,),
        ).fetchall():
            con.execute('INSERT INTO agg_charts(batch_id,chart_key,label,value) VALUES (?,?,?,?)', (batch_id, 'battalions_per_bde', str(label), float(value)))

        for label, value in con.execute(
            "SELECT bde, COUNT(DISTINCT stn) as v FROM facts WHERE batch_id=? AND bde IS NOT NULL GROUP BY bde ORDER BY v DESC",
            (batch_id,),
        ).fetchall():
            con.execute('INSERT INTO agg_charts(batch_id,chart_key,label,value) VALUES (?,?,?,?)', (batch_id, 'stations_per_bde', str(label), float(value)))

        con.commit()
    finally:
        con.close()
