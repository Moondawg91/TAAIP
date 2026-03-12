from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Dict, Any, Optional
from services.api.app import db as dbmod
from .rbac import get_current_user
import io, csv, json

router = APIRouter(prefix="/dashboards", tags=["exports"])


def _table_exists(cur, name: str) -> bool:
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
        return cur.fetchone() is not None
    except Exception:
        return False


@router.get('/budget/export.csv')
def export_budget_csv(
    fy: Optional[int] = Query(None),
    qtr: Optional[int] = Query(None),
    funding_line: Optional[str] = Query(None),
    org_unit_id: Optional[str] = Query(None),
    user=Depends(get_current_user)
):
    conn = dbmod.connect()
    try:
        cur = conn.cursor()
        if not _table_exists(cur, 'budget_line_item'):
            return StreamingResponse(io.StringIO(''), media_type='text/csv')

        # Build WHERE clauses from provided filters
        wheres = []
        params = []
        if fy is not None:
            wheres.append('fy = ?'); params.append(fy)
        if qtr is not None:
            wheres.append('qtr = ?'); params.append(qtr)
        if funding_line is not None:
            wheres.append('funding_line = ?'); params.append(funding_line)
        if org_unit_id is not None:
            wheres.append('org_unit_id = ?'); params.append(org_unit_id)

        sql = 'SELECT id, project_id, event_id, funding_line, allocated_amount, obligated_amount, expended_amount, fy, qtr FROM budget_line_item'
        if wheres:
            sql += ' WHERE ' + ' AND '.join(wheres)
        cur.execute(sql, tuple(params))
        rows = cur.fetchall() or []
        sio = io.StringIO()
        w = csv.writer(sio)
        w.writerow(['id','project_id','event_id','funding_line','allocated_amount','obligated_amount','expended_amount','fy','qtr'])
        for r in rows:
            if isinstance(r, dict):
                w.writerow([r.get('id'), r.get('project_id'), r.get('event_id'), r.get('funding_line'), r.get('allocated_amount'), r.get('obligated_amount'), r.get('expended_amount'), r.get('fy'), r.get('qtr')])
            else:
                w.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]])
        sio.seek(0)
        return StreamingResponse(sio, media_type='text/csv')
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.get('/budget/export.json')
def export_budget_json(
    fy: Optional[int] = Query(None),
    qtr: Optional[int] = Query(None),
    funding_line: Optional[str] = Query(None),
    org_unit_id: Optional[str] = Query(None),
    user=Depends(get_current_user)
):
    conn = dbmod.connect()
    try:
        cur = conn.cursor()
        if not _table_exists(cur, 'budget_line_item'):
            return JSONResponse({'rows': []})

        wheres = []
        params = []
        if fy is not None:
            wheres.append('fy = ?'); params.append(fy)
        if qtr is not None:
            wheres.append('qtr = ?'); params.append(qtr)
        if funding_line is not None:
            wheres.append('funding_line = ?'); params.append(funding_line)
        if org_unit_id is not None:
            wheres.append('org_unit_id = ?'); params.append(org_unit_id)

        sql = 'SELECT id, project_id, event_id, funding_line, allocated_amount, obligated_amount, expended_amount, fy, qtr FROM budget_line_item'
        if wheres:
            sql += ' WHERE ' + ' AND '.join(wheres)
        cur.execute(sql, tuple(params))
        rows = cur.fetchall() or []
        out = []
        for r in rows:
            if isinstance(r, dict):
                out.append(r)
            else:
                out.append({'id': r[0], 'project_id': r[1], 'event_id': r[2], 'funding_line': r[3], 'allocated_amount': r[4], 'obligated_amount': r[5], 'expended_amount': r[6], 'fy': r[7], 'qtr': r[8]})
        return JSONResponse({'rows': out})
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.get('/projects/export.csv')
def export_projects_csv(org_unit_id: Optional[str] = Query(None), user=Depends(get_current_user)):
    conn = dbmod.connect()
    try:
        cur = conn.cursor()
        if not _table_exists(cur, 'projects'):
            return StreamingResponse(io.StringIO(''), media_type='text/csv')
        sql = 'SELECT id, name, org_unit_id, planned_cost, actual_cost, start_date, end_date FROM projects'
        params = []
        if org_unit_id is not None:
            sql += ' WHERE org_unit_id = ?'
            params.append(org_unit_id)
        cur.execute(sql, tuple(params))
        rows = cur.fetchall() or []
        sio = io.StringIO(); w = csv.writer(sio)
        w.writerow(['id','name','org_unit_id','planned_cost','actual_cost','start_date','end_date'])
        for r in rows:
            if isinstance(r, dict):
                w.writerow([r.get('id'), r.get('name'), r.get('org_unit_id'), r.get('planned_cost'), r.get('actual_cost'), r.get('start_date'), r.get('end_date')])
            else:
                w.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6]])
        sio.seek(0)
        return StreamingResponse(sio, media_type='text/csv')
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.get('/events/export.csv')
def export_events_csv(event_type: Optional[str] = Query(None), user=Depends(get_current_user)):
    conn = dbmod.connect()
    try:
        cur = conn.cursor()
        if not _table_exists(cur, 'events'):
            return StreamingResponse(io.StringIO(''), media_type='text/csv')
        sql = 'SELECT id, name, event_type, start_date, end_date, budget FROM events'
        params = []
        if event_type is not None:
            sql += ' WHERE event_type = ?'
            params.append(event_type)
        cur.execute(sql, tuple(params))
        rows = cur.fetchall() or []
        sio = io.StringIO(); w = csv.writer(sio)
        w.writerow(['id','name','event_type','start_date','end_date','budget'])
        for r in rows:
            if isinstance(r, dict):
                w.writerow([r.get('id'), r.get('name'), r.get('event_type'), r.get('start_date'), r.get('end_date'), r.get('budget')])
            else:
                w.writerow([r[0], r[1], r[2], r[3], r[4], r[5]])
        sio.seek(0)
        return StreamingResponse(sio, media_type='text/csv')
    finally:
        try:
            conn.close()
        except Exception:
            pass

# Compatibility aliases for older budget export paths
@router.get('/budget/dashboard/export.csv')
def compat_budget_export_csv(
    fy: Optional[int] = Query(None),
    qtr: Optional[int] = Query(None),
    funding_line: Optional[str] = Query(None),
    org_unit_id: Optional[str] = Query(None),
    user=Depends(get_current_user)
):
    return export_budget_csv(fy=fy, qtr=qtr, funding_line=funding_line, org_unit_id=org_unit_id, user=user)


@router.get('/budget/dashboard/export.json')
def compat_budget_export_json(
    fy: Optional[int] = Query(None),
    qtr: Optional[int] = Query(None),
    funding_line: Optional[str] = Query(None),
    org_unit_id: Optional[str] = Query(None),
    user=Depends(get_current_user)
):
    return export_budget_json(fy=fy, qtr=qtr, funding_line=funding_line, org_unit_id=org_unit_id, user=user)
