from fastapi import APIRouter
from .. import db

router = APIRouter(prefix="/api/org", tags=["compat_org"])


def _rows_to_counts(rows):
    counts = {"MK": 0, "MW": 0, "MO": 0, "SU": 0, "UNK": 0}
    for r in rows:
        cat = r["category"] if "category" in r else r[2]
        cnt = r["count"] if "count" in r else r[3]
        counts[cat] = cnt
    return counts


@router.get("/coverage/summary")
def coverage_summary(scope: str = "USAREC", value: str = None):
    # Read latest coverage_summary rows and synthesize the legacy shape
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT as_of FROM coverage_summary WHERE scope=? ORDER BY as_of DESC LIMIT 1", (scope,))
        row = cur.fetchone()
        if not row:
            return {"counts": {"MK": 0, "MW": 0, "MO": 0, "SU": 0, "UNK": 0}, "data_as_of": None, "units": []}
        latest = row[0]
        cur.execute("SELECT scope, as_of, category, count FROM coverage_summary WHERE scope=? AND as_of=? ORDER BY category", (scope, latest))
        rows = [dict(r) for r in cur.fetchall()]
        counts = _rows_to_counts(rows)
        return {"counts": counts, "data_as_of": latest, "units": []}
    finally:
        conn.close()


@router.get("/stations/{rsid}/zip-coverage")
def station_zip_coverage(rsid: str):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT zip, metric_key, metric_value FROM zip_metrics WHERE station_rsid=? ORDER BY zip", (rsid,))
        rows = [dict(r) for r in cur.fetchall()]
        return {"rsid": rsid, "zip_coverage": rows}
    finally:
        conn.close()


@router.get("/zip/{zip_code}/station")
def zip_to_station(zip_code: str):
    # best-effort: read zip_metrics table for mapping, otherwise null
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT zip, scope, as_of, metric_key, metric_value FROM zip_metrics WHERE zip=? ORDER BY as_of DESC LIMIT 1", (zip_code,))
        row = cur.fetchone()
        if not row:
            return {"zip_code": zip_code, "station": None}
        return dict(row)
    finally:
        conn.close()
