from fastapi import APIRouter, Query
from typing import Optional
from services.api.app.db import connect
from . import tactical_rollups

router = APIRouter()


def _exec_metric_sql(sql_text: str, params: dict):
    conn = connect()
    cur = conn.cursor()
    # naive param substitution for sqlite named params
    try:
        cur.execute(sql_text, params)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return {"status": "ok", "data": {"rows": rows}}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/metrics/query")
def metrics_query(metric_id: str = Query(...), fy: Optional[int] = Query(None), qtr: Optional[int] = Query(None), scope_type: Optional[str] = Query(None), scope_value: Optional[str] = Query(None), station_rsid: Optional[str] = Query(None), event_id: Optional[str] = Query(None)):
    """Lightweight metrics endpoint.

    Priority order:
    1. If a stored `metric_definition` exists, execute its `sql_definition`.
    2. Otherwise proxy known metric_ids to tactical_rollups for compatibility.
    """
    mid = (metric_id or '').lower()
    # Try stored metric_definition first
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT metric_id, name, sql_definition FROM metric_definition WHERE metric_id = ?", (mid,))
        r = cur.fetchone()
        if r:
            sql = r['sql_definition'] if isinstance(r, dict) or hasattr(r, '__getitem__') else r[2]
            # pass some common params into the SQL execution
            params = {'fy': fy, 'qtr': qtr, 'scope_type': scope_type, 'scope_value': scope_value, 'station_rsid': station_rsid, 'event_id': event_id}
            return _exec_metric_sql(sql, params)
    except Exception:
        pass

    # Fallback to tactical rollups proxy for immediate compatibility
    if mid in ('funnel', 'pipeline', 'funnel_rollup'):
        return tactical_rollups.funnel_rollup(fy=fy, qtr=qtr, scope_type=scope_type, scope_value=scope_value, station_rsid=station_rsid)
    if mid in ('events', 'events_rollup'):
        return tactical_rollups.events_rollup(fy=fy, qtr=qtr, scope_type=scope_type, scope_value=scope_value, station_rsid=station_rsid, event_id=event_id)
    if mid in ('marketing', 'marketing_rollup'):
        return tactical_rollups.marketing_rollup(fy=fy, qtr=qtr, scope_type=scope_type, scope_value=scope_value, station_rsid=station_rsid, event_id=event_id)
    if mid in ('budget', 'budget_rollup'):
        return tactical_rollups.budget_rollup(fy=fy, qtr=qtr, scope_type=scope_type, scope_value=scope_value, station_rsid=station_rsid)
    if mid in ('command', 'command_rollup'):
        return tactical_rollups.command_rollup(fy=fy, qtr=qtr, scope_type=scope_type, scope_value=scope_value)

    return {"status": "error", "message": f"unknown metric_id: {metric_id}"}
