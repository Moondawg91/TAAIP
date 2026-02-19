from fastapi import APIRouter, Depends, HTTPException
from .. import db, auth, rbac, models
from sqlalchemy import text
from sqlalchemy.orm import Session

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
def station_zip_coverage(rsid: str, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(auth.get_db)):
    rows = []
    try:
        # Try reading legacy zip_metrics table first via the shared Session
        try:
            q = text("SELECT zip, metric_key, metric_value FROM zip_metrics WHERE station_rsid=:rsid ORDER BY zip")
            raw_rows = db.execute(q, {"rsid": rsid}).mappings().all()
        except Exception:
            raw_rows = []

        if raw_rows:
            for r in raw_rows:
                zip_code = r.get('zip') or r.get('zip_code')
                market_category = None
                if 'metric_key' in r and r.get('metric_key') == 'market_category':
                    market_category = r.get('metric_value')
                elif 'metric_value' in r and 'metric_key' not in r:
                    market_category = r.get('metric_value')
                rows.append({"zip_code": zip_code, "market_category": market_category})
        else:
            try:
                orm_rows = db.query(models.StationZipCoverage).filter(models.StationZipCoverage.station_rsid == rsid).all()
                for r in orm_rows:
                    rows.append({"zip_code": r.zip_code, "market_category": r.market_category.name if r.market_category else None})
            except Exception:
                rows = []

        # enforce RBAC: station must be within user scope
        try:
            # resolve authoritative scope from DB-backed user record when possible
            db_user = db.query(models.User).filter(models.User.username == getattr(current_user, 'username', None)).one_or_none()
            user_scope = db_user.scope if db_user is not None else getattr(current_user, 'scope', None)
        except Exception:
            user_scope = getattr(current_user, 'scope', None)
        # Inline scope normalization and check to avoid mismatches between different
        # user dict formats used by other RBAC helpers.
        ns = rbac.normalize_scope(user_scope)
        allowed = False
        if ns['type'] == 'USAREC':
            allowed = True
        elif ns['type'] == 'BDE' and rsid.startswith(ns['value']):
            allowed = True
        elif ns['type'] == 'BN' and rsid.startswith(ns['value']):
            allowed = True
        elif ns['type'] == 'CO' and rsid.startswith(ns['value']):
            allowed = True
        elif ns['type'] == 'STN' and rsid == ns['value']:
            allowed = True
        if not allowed:
            raise HTTPException(status_code=403, detail="Forbidden: out of scope")
        return {"station_rsid": rsid, "zip_coverage": rows}
    except HTTPException:
        # Authorization/HTTP errors should propagate to the client
        raise
    except Exception:
        # ensure we surface unexpected issues as empty result rather than crashing the app
        return {"station_rsid": rsid, "zip_coverage": []}


@router.get("/zip/{zip_code}/station")
def zip_to_station(zip_code: str, db: Session = Depends(auth.get_db)):
    # best-effort: read zip_metrics table for mapping, otherwise null
    try:
        q = text("SELECT zip, scope, as_of, metric_key, metric_value FROM zip_metrics WHERE zip=:zip_code ORDER BY as_of DESC LIMIT 1")
        row = db.execute(q, {"zip_code": zip_code}).mappings().first()
        if not row:
            return {"zip_code": zip_code, "station": None}
        return dict(row)
    except Exception:
        return {"zip_code": zip_code, "station": None}
