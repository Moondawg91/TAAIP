from fastapi import APIRouter, Depends, HTTPException
from .. import db, auth, rbac, models

router = APIRouter(prefix="/org", tags=["compat_org"])


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
def station_zip_coverage(rsid: str, current_user: models.User = Depends(auth.get_current_user)):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT zip, metric_key, metric_value FROM zip_metrics WHERE station_rsid=? ORDER BY zip", (rsid,))
        raw_rows = [dict(r) for r in cur.fetchall()]
        rows = []
        if raw_rows:
            for r in raw_rows:
                zip_code = r.get('zip') or r.get('zip_code')
                # legacy metric_key/metric_value -> market_category
                market_category = None
                if 'metric_key' in r and r.get('metric_key') == 'market_category':
                    market_category = r.get('metric_value')
                elif 'metric_value' in r and 'metric_key' not in r:
                    # if legacy row is already flattened
                    market_category = r.get('metric_value')
                rows.append({"zip_code": zip_code, "market_category": market_category})
        else:
            try:
                from .. import database as _database
                from .. import models as _models
                sess = _database.SessionLocal()
                orm_rows = sess.query(_models.StationZipCoverage).filter(_models.StationZipCoverage.station_rsid == rsid).all()
                for r in orm_rows:
                    rows.append({"zip_code": r.zip_code, "market_category": r.market_category.name if r.market_category else None})
            except Exception:
                rows = []
        # enforce RBAC: station must be within user scope
        if not rbac.is_rsid_in_scope(current_user.scope, rsid):
            raise HTTPException(status_code=403, detail="Forbidden: out of scope")
        return {"station_rsid": rsid, "zip_coverage": rows}
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
