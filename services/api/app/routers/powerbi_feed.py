from fastapi import APIRouter, Depends
from typing import Optional, List, Any
from ..db import connect
from .rbac import get_allowed_org_units
from fastapi.responses import StreamingResponse
import csv
import io

router = APIRouter(prefix="/powerbi", tags=["powerbi"])


@router.get("/events")
def export_events(org_unit_id: Optional[int] = None, fy: Optional[int] = None, qtr: Optional[int] = None, limit: int = 1000, allowed_orgs: Optional[list] = Depends(get_allowed_org_units)):
    conn = connect()
    try:
        cur = conn.cursor()
        sql = 'SELECT id as event_id, org_unit_id, name, event_type, start_dt, end_dt, location_city, location_state, cbsa, loe, status, created_at, updated_at FROM event WHERE 1=1'
        params: List[Any] = []
        # enforce scope: allowed_orgs==None means unrestricted
        if allowed_orgs is not None:
            # if org_unit_id provided, ensure it's within allowed
            if org_unit_id is not None:
                if org_unit_id not in allowed_orgs:
                    return []
                sql += ' AND org_unit_id=?'; params.append(org_unit_id)
            else:
                placeholders = ','.join(['?'] * len(allowed_orgs)) if allowed_orgs else 'NULL'
                sql += f' AND org_unit_id IN ({placeholders})'
                params.extend(allowed_orgs)
        else:
            if org_unit_id is not None:
                sql += ' AND org_unit_id=?'; params.append(org_unit_id)
        sql += ' ORDER BY start_dt DESC LIMIT ?'; params.append(limit)
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

@router.get('/export/csv', summary='Export a PowerBI-friendly CSV for a named table')
def export_table_csv(table: str = 'event', limit: int = 1000, allowed_orgs: Optional[list] = Depends(get_allowed_org_units)):
    """Basic CSV export for small/medium tables. Respects RBAC by filtering on org_unit_id where applicable."""
    conn = db.connect()
    try:
        cur = conn.cursor()
        # whitelist simple tables to avoid arbitrary SQL
        allowed_tables = {
            'event': ('event', ['id','org_unit_id','name','event_type','start_dt','end_dt','location_city','location_state','cbsa','loe','status']),
            'fy_budget': ('fy_budget', ['id','org_unit_id','fy','total_allocated','created_at']),
            'fact_metric': ('fact_metric', ['id','metric_key','metric_value','unit','org_unit_id','recorded_at','source'])
        }
        if table not in allowed_tables:
            raise HTTPException(status_code=400, detail='unsupported_table')

        tbl, cols = allowed_tables[table]
        base_sql = f"SELECT {', '.join(cols)} FROM {tbl} WHERE 1=1"
        params = []
        if allowed_orgs is not None:
            # if the table has org_unit_id column, filter by allowed_orgs
            placeholders = ','.join(['?'] * len(allowed_orgs)) if allowed_orgs else 'NULL'
            base_sql += f" AND org_unit_id IN ({placeholders})"
            params.extend(allowed_orgs)
        base_sql += ' ORDER BY id DESC LIMIT ?'
        params.append(limit)
        cur.execute(base_sql, tuple(params))
        rows = cur.fetchall()

        # stream CSV
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(cols)
        for r in rows:
            writer.writerow([r[c] for c in cols])
        buf.seek(0)
        return StreamingResponse(iter([buf.getvalue()]), media_type='text/csv')
    finally:
        conn.close()


@router.get('/budgets')
def export_budgets(org_unit_id: Optional[int] = None, fy: Optional[int] = None, limit: int = 1000, allowed_orgs: Optional[list] = Depends(get_allowed_org_units)):
    conn = connect()
    try:
        cur = conn.cursor()
        sql = 'SELECT fb.id as fy_budget_id, fb.org_unit_id, fb.fy, fb.total_allocated, fli.id as line_item_id, fli.qtr, fli.event_id, fli.category, fli.amount FROM fy_budget fb LEFT JOIN budget_line_item fli ON fli.fy_budget_id=fb.id WHERE 1=1'
        params: List[Any] = []
        if allowed_orgs is not None:
            if org_unit_id is not None:
                if org_unit_id not in allowed_orgs:
                    return []
                sql += ' AND fb.org_unit_id=?'; params.append(org_unit_id)
            else:
                placeholders = ','.join(['?'] * len(allowed_orgs)) if allowed_orgs else 'NULL'
                sql += f' AND fb.org_unit_id IN ({placeholders})'
                params.extend(allowed_orgs)
        else:
            if org_unit_id is not None:
                sql += ' AND fb.org_unit_id=?'; params.append(org_unit_id)
        if fy is not None:
            sql += ' AND fb.fy=?'; params.append(fy)
        sql += ' LIMIT ?'; params.append(limit)
        cur.execute(sql, tuple(params))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.get('/facts')
def export_facts(metric_key: Optional[str] = None, org_unit_id: Optional[int] = None, since: Optional[str] = None, limit: int = 2000, allowed_orgs: Optional[list] = Depends(get_allowed_org_units)):
    conn = connect()
    try:
        cur = conn.cursor()
        sql = 'SELECT id, metric_key, metric_value, unit, org_unit_id, recorded_at, source, import_job_id FROM fact_metric WHERE 1=1'
        params: List[Any] = []
        if metric_key:
            sql += ' AND metric_key=?'; params.append(metric_key)
        if allowed_orgs is not None:
            if org_unit_id is not None:
                if org_unit_id not in allowed_orgs:
                    return []
                sql += ' AND org_unit_id=?'; params.append(org_unit_id)
            else:
                placeholders = ','.join(['?'] * len(allowed_orgs)) if allowed_orgs else 'NULL'
                sql += f' AND org_unit_id IN ({placeholders})'
                params.extend(allowed_orgs)
        else:
            if org_unit_id:
                sql += ' AND org_unit_id=?'; params.append(org_unit_id)
        if since:
            sql += ' AND recorded_at>=?'; params.append(since)
        sql += ' ORDER BY recorded_at DESC LIMIT ?'; params.append(limit)
        cur.execute(sql, tuple(params))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
from typing import List, Dict, Optional
from .. import db
import os


def row_to_dict(row) -> Dict:
    return {k: row[k] for k in row.keys()}


@router.get("/kpis")
def get_kpis(scope: Optional[str] = "USAREC", as_of: Optional[str] = None, allowed_orgs: Optional[list] = Depends(get_allowed_org_units)) -> List[Dict]:
    conn = db.connect()
    try:
        cur = conn.cursor()
        if as_of:
            cur.execute("SELECT * FROM kpi_snapshot WHERE scope=? AND as_of=? ORDER BY id", (scope, as_of))
        else:
            # pick latest as_of for scope
            cur.execute("SELECT as_of FROM kpi_snapshot WHERE scope=? ORDER BY as_of DESC LIMIT 1", (scope,))
            row = cur.fetchone()
            if not row:
                return []
            latest = row[0]
            cur.execute("SELECT * FROM kpi_snapshot WHERE scope=? AND as_of=? ORDER BY id", (scope, latest))
        rows = cur.fetchall()
        out = [row_to_dict(r) for r in rows]
        if out:
            return out
        # empty DB: return empty rows + schema metadata
        return {"rows": [], "schema": ["id","scope","as_of","metric_key","metric_value","source","notes"]}
    finally:
        conn.close()


@router.get("/coverage/summary")
def get_coverage_summary(scope: Optional[str] = "USAREC", as_of: Optional[str] = None, allowed_orgs: Optional[list] = Depends(get_allowed_org_units)) -> List[Dict]:
    conn = db.connect()
    try:
        cur = conn.cursor()
        if as_of:
            cur.execute("SELECT * FROM coverage_summary WHERE scope=? AND as_of=? ORDER BY category", (scope, as_of))
        else:
            cur.execute("SELECT as_of FROM coverage_summary WHERE scope=? ORDER BY as_of DESC LIMIT 1", (scope,))
            row = cur.fetchone()
            if not row:
                return []
            latest = row[0]
            cur.execute("SELECT * FROM coverage_summary WHERE scope=? AND as_of=? ORDER BY category", (scope, latest))
        rows = cur.fetchall()
        out = [row_to_dict(r) for r in rows]
        if out:
            return out
        return {"rows": [], "schema": ["id","scope","as_of","category","count","source","notes"]}
    finally:
        conn.close()


@router.get("/zip/metrics")
def get_zip_metrics(zip: Optional[str] = None, scope: Optional[str] = "USAREC", as_of: Optional[str] = None, allowed_orgs: Optional[list] = Depends(get_allowed_org_units)):
    conn = db.connect()
    try:
        cur = conn.cursor()
        if as_of:
            if zip:
                cur.execute("SELECT * FROM zip_metrics WHERE scope=? AND as_of=? AND zip=? ORDER BY id", (scope, as_of, zip))
            else:
                cur.execute("SELECT * FROM zip_metrics WHERE scope=? AND as_of=? ORDER BY zip", (scope, as_of))
        else:
            cur.execute("SELECT as_of FROM zip_metrics WHERE scope=? ORDER BY as_of DESC LIMIT 1", (scope,))
            row = cur.fetchone()
            if not row:
                return []
            latest = row[0]
            if zip:
                cur.execute("SELECT * FROM zip_metrics WHERE scope=? AND as_of=? AND zip=? ORDER BY id", (scope, latest, zip))
            else:
                cur.execute("SELECT * FROM zip_metrics WHERE scope=? AND as_of=? ORDER BY zip", (scope, latest))
        rows = cur.fetchall()
        out = [row_to_dict(r) for r in rows]
        if out:
            return out
        return {"rows": [], "schema": ["id","zip","scope","as_of","metric_key","metric_value","source","notes"]}
    finally:
        conn.close()


@router.get("/cbsa/metrics")
def get_cbsa_metrics(cbsa: Optional[str] = None, scope: Optional[str] = "USAREC", as_of: Optional[str] = None, allowed_orgs: Optional[list] = Depends(get_allowed_org_units)):
    conn = db.connect()
    try:
        cur = conn.cursor()
        if as_of:
            if cbsa:
                cur.execute("SELECT * FROM cbsa_metrics WHERE scope=? AND as_of=? AND cbsa=? ORDER BY id", (scope, as_of, cbsa))
            else:
                cur.execute("SELECT * FROM cbsa_metrics WHERE scope=? AND as_of=? ORDER BY cbsa", (scope, as_of))
        else:
            cur.execute("SELECT as_of FROM cbsa_metrics WHERE scope=? ORDER BY as_of DESC LIMIT 1", (scope,))
            row = cur.fetchone()
            if not row:
                return []
            latest = row[0]
            if cbsa:
                cur.execute("SELECT * FROM cbsa_metrics WHERE scope=? AND as_of=? AND cbsa=? ORDER BY id", (scope, latest, cbsa))
            else:
                cur.execute("SELECT * FROM cbsa_metrics WHERE scope=? AND as_of=? ORDER BY cbsa", (scope, latest))
        rows = cur.fetchall()
        out = [row_to_dict(r) for r in rows]
        if out:
            return out
        return {"rows": [], "schema": ["id","cbsa","scope","as_of","metric_key","metric_value","source","notes"]}
    finally:
        conn.close()


@router.get("/geo/zip")
def get_geo_zip(scope: Optional[str] = "USAREC", as_of: Optional[str] = None, allowed_orgs: Optional[list] = Depends(get_allowed_org_units)) -> List[Dict]:
    """Return aggregated ZIP-level counts suitable for MapRenderer.

    If `zip_metrics` table exists and has rows, aggregate metric_value by zip.
    Returns an empty list when no data exists to encourage empty-state handling.
    """
    conn = db.connect()
    try:
        cur = conn.cursor()
        rows = []
        try:
            if as_of:
                cur.execute("SELECT zip, SUM(metric_value) as value FROM zip_metrics WHERE scope=? AND as_of=? GROUP BY zip ORDER BY value DESC", (scope, as_of))
            else:
                cur.execute("SELECT as_of FROM zip_metrics WHERE scope=? ORDER BY as_of DESC LIMIT 1", (scope,))
                row = cur.fetchone()
                if row:
                    latest = row[0]
                    cur.execute("SELECT zip, SUM(metric_value) as value FROM zip_metrics WHERE scope=? AND as_of=? GROUP BY zip ORDER BY value DESC", (scope, latest))
                else:
                    rows = []
            if rows == []:
                rows = cur.fetchall()
        except Exception:
            rows = []

        if rows:
            out = []
            for r in rows:
                # sqlite Row supports mapping access
                z = r['zip'] if isinstance(r, dict) or hasattr(r, 'keys') else r[0]
                val = r['value'] if isinstance(r, dict) or hasattr(r, 'keys') else r[1]
                out.append({"zip": str(z), "value": int(val or 0), "label": str(z)})
            return out

        # empty DB: return empty rows + schema metadata for consumers
        return {"rows": [], "schema": ["zip","value","label","category"]}
    finally:
        conn.close()


@router.get("/geo/cbsa")
def get_geo_cbsa(scope: Optional[str] = "USAREC", as_of: Optional[str] = None, allowed_orgs: Optional[list] = Depends(get_allowed_org_units)) -> List[Dict]:
    """Return aggregated CBSA-level counts suitable for MapRenderer.

    Aggregates `cbsa_metrics.metric_value` by cbsa and returns an empty list when no data exists.
    """
    conn = db.connect()
    try:
        cur = conn.cursor()
        rows = []
        try:
            if as_of:
                cur.execute("SELECT cbsa, SUM(metric_value) as value FROM cbsa_metrics WHERE scope=? AND as_of=? GROUP BY cbsa ORDER BY value DESC", (scope, as_of))
            else:
                cur.execute("SELECT as_of FROM cbsa_metrics WHERE scope=? ORDER BY as_of DESC LIMIT 1", (scope,))
                row = cur.fetchone()
                if row:
                    latest = row[0]
                    cur.execute("SELECT cbsa, SUM(metric_value) as value FROM cbsa_metrics WHERE scope=? AND as_of=? GROUP BY cbsa ORDER BY value DESC", (scope, latest))
                else:
                    rows = []
            if rows == []:
                rows = cur.fetchall()
        except Exception:
            rows = []

        if rows:
            out = []
            for r in rows:
                c = r['cbsa'] if isinstance(r, dict) or hasattr(r, 'keys') else r[0]
                val = r['value'] if isinstance(r, dict) or hasattr(r, 'keys') else r[1]
                out.append({"cbsa": str(c), "value": int(val or 0), "label": str(c)})
            return out

        return {"rows": [], "schema": ["cbsa","value","label"]}
    finally:
        conn.close()
