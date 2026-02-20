from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime
from services.api.app.db import connect

router = APIRouter(prefix="/command-center", tags=["command-center"])


def _now_iso():
    return datetime.utcnow().isoformat()


def _filters(fy, qtr, month, scope_type, scope_value, funding_line):
    return {"fy": fy, "qtr": qtr, "month": month, "scope_type": scope_type, "scope_value": scope_value, "funding_line": funding_line}


@router.get("/overview")
def overview(fy: Optional[int] = None, qtr: Optional[int] = None, month: Optional[int] = None, scope_type: Optional[str] = None, scope_value: Optional[str] = None, funding_line: Optional[str] = None):
    conn = connect()
    cur = conn.cursor()
    missing = []
    try:
        cur.execute("SELECT COUNT(1) FROM command_priorities")
        priorities = cur.fetchone()[0] or 0
    except Exception:
        priorities = 0
        missing.append('command_priorities')
    try:
        cur.execute("SELECT COUNT(1) FROM loes")
        loes = cur.fetchone()[0] or 0
    except Exception:
        loes = 0
        missing.append('loes')
    try:
        cur.execute("SELECT COUNT(1) FROM home_alerts WHERE record_status='active' AND (acked_at IS NULL OR acked_at='')")
        alerts = cur.fetchone()[0] or 0
    except Exception:
        alerts = 0

    # simple risk placeholders
    burden_risk = 'unknown'
    processing_risk = 'unknown'

    return {"status": "ok", "as_of_utc": _now_iso(), "summary": {"priorities_count": priorities, "loes_count": loes, "alerts_count": alerts, "burden_risk": burden_risk, "processing_risk": processing_risk}, "missing_data": missing}


@router.get('/priorities')
def list_priorities(fy: Optional[int] = None, qtr: Optional[int] = None, scope_type: Optional[str] = None, scope_value: Optional[str] = None):
    conn = connect(); cur = conn.cursor()
    try:
        cur.execute('SELECT id, title, description, rank, created_at FROM command_priorities ORDER BY rank ASC')
        rows = cur.fetchall()
        return {"status":"ok", "items": [dict(r) for r in rows]}
    except Exception:
        return {"status":"ok", "items": []}


@router.post('/priorities')
def create_priority(payload: dict):
    conn = connect(); cur = conn.cursor()
    now = _now_iso()
    try:
        cur.execute('INSERT INTO command_priorities(title, description, created_at) VALUES (?,?,?)', (payload.get('title'), payload.get('description'), now))
        conn.commit()
        return {"status":"ok"}
    except Exception:
        return {"status":"ok"}


@router.put('/priorities/{pid}')
def update_priority(pid: str, payload: dict):
    conn = connect(); cur = conn.cursor()
    try:
        cur.execute('UPDATE command_priorities SET title=?, description=? WHERE id=?', (payload.get('title'), payload.get('description'), pid))
        conn.commit()
    except Exception:
        pass
    return {"status":"ok"}


@router.delete('/priorities/{pid}')
def delete_priority(pid: str):
    conn = connect(); cur = conn.cursor()
    try:
        cur.execute('DELETE FROM command_priorities WHERE id=?', (pid,))
        conn.commit()
    except Exception:
        pass
    return {"status":"ok"}


# LOEs endpoints (basic CRUD)
@router.get('/loes')
def list_loes():
    conn = connect(); cur = conn.cursor()
    try:
        cur.execute('SELECT id, title, description, created_at FROM loes ORDER BY created_at DESC')
        return {"status":"ok", "items": [dict(r) for r in cur.fetchall()]}
    except Exception:
        return {"status":"ok", "items": []}


@router.post('/loes')
def create_loe(payload: dict):
    conn = connect(); cur = conn.cursor(); now = _now_iso()
    try:
        cur.execute('INSERT INTO loes(id, title, description, created_at) VALUES (?,?,?,?)', (payload.get('id'), payload.get('title'), payload.get('description'), now))
        conn.commit()
    except Exception:
        pass
    return {"status":"ok"}


@router.put('/loes/{id}')
def update_loe(id: str, payload: dict):
    conn = connect(); cur = conn.cursor()
    try:
        cur.execute('UPDATE loes SET title=?, description=? WHERE id=?', (payload.get('title'), payload.get('description'), id))
        conn.commit()
    except Exception:
        pass
    return {"status":"ok"}


@router.delete('/loes/{id}')
def delete_loe(id: str):
    conn = connect(); cur = conn.cursor()
    try:
        cur.execute('DELETE FROM loes WHERE id=?', (id,))
        conn.commit()
    except Exception:
        pass
    return {"status":"ok"}


@router.get('/loes/evaluate')
def evaluate_loes():
    conn = connect(); cur = conn.cursor(); out = []
    try:
        cur.execute('SELECT id, title FROM loes')
        for r in cur.fetchall():
            out.append({"loe_id": r[0], "title": r[1], "status": 'unknown', 'rationale': 'no metrics'})
    except Exception:
        pass
    return {"status":"ok", "items": out, "missing_data": []}


@router.get('/mission-assessment')
def mission_assessment(fy: Optional[int] = None, qtr: Optional[int] = None, month: Optional[int] = None, scope_type: Optional[str] = None, scope_value: Optional[str] = None, funding_line: Optional[str] = None):
    # composite endpoint returning tactical rollups (read-only)
    conn = connect(); cur = conn.cursor()
    filters = _filters(fy, qtr, month, scope_type, scope_value, funding_line)
    missing = []
    try:
        # Events rollup: count and costs
        events_count = 0
        planned_total = 0
        actual_total = 0
        try:
            cur.execute("SELECT COUNT(1) FROM event")
            events_count = cur.fetchone()[0] or 0
        except Exception:
            missing.append('event')
        try:
            # sum planned/actual if columns exist
            cur.execute("PRAGMA table_info(event)")
            cols = [r[1] for r in cur.fetchall()]
            sel_parts = []
            if 'planned_cost' in cols:
                sel_parts.append('COALESCE(SUM(planned_cost),0)')
            if 'actual_cost' in cols:
                sel_parts.append('COALESCE(SUM(actual_cost),0)')
            if sel_parts:
                sel = ','.join(sel_parts)
                cur.execute(f"SELECT {sel} FROM event")
                row = cur.fetchone() or []
                if 'planned_cost' in cols:
                    planned_total = row[0] or 0
                if 'actual_cost' in cols:
                    actual_total = row[1] if len(row) > 1 else (row[0] or 0)
        except Exception:
            pass

        # Marketing rollup
        impressions = 0
        engagements = 0
        activations = 0
        marketing_cost = 0
        try:
            cur.execute("PRAGMA table_info(marketing_activities)")
            mcols = [r[1] for r in cur.fetchall()]
            sel = []
            if 'cost' in mcols:
                sel.append('COALESCE(SUM(cost),0)')
            if 'impressions' in mcols:
                sel.append('COALESCE(SUM(impressions),0)')
            if 'engagement_count' in mcols:
                sel.append('COALESCE(SUM(engagement_count),0)')
            if 'activation_conversions' in mcols:
                sel.append('COALESCE(SUM(activation_conversions),0)')
            if sel:
                cur.execute('SELECT ' + ','.join(sel) + ' FROM marketing_activities')
                mr = cur.fetchone() or []
                idx = 0
                if 'cost' in mcols:
                    marketing_cost = mr[idx] or 0; idx += 1
                if 'impressions' in mcols:
                    impressions = mr[idx] or 0; idx += 1
                if 'engagement_count' in mcols:
                    engagements = mr[idx] or 0; idx += 1
                if 'activation_conversions' in mcols:
                    activations = mr[idx] or 0; idx += 1
        except Exception:
            missing.append('marketing_activities')

        # Funnel rollup: overall conversion rate between first and last stage
        conversion_rate = None
        try:
            cur.execute("SELECT id FROM funnel_stages ORDER BY rank LIMIT 1")
            first = cur.fetchone(); cur.execute("SELECT id FROM funnel_stages ORDER BY rank DESC LIMIT 1"); last = cur.fetchone()
            if first and last:
                f = first[0]; l = last[0]
                cur.execute('SELECT COUNT(1) FROM funnel_transitions WHERE from_stage=?', (f,))
                total_from = cur.fetchone()[0] or 0
                cur.execute('SELECT COUNT(1) FROM funnel_transitions WHERE from_stage=? AND to_stage=?', (f, l))
                moved = cur.fetchone()[0] or 0
                conversion_rate = (moved / total_from) if total_from and total_from > 0 else None
        except Exception:
            missing.append('funnel_transitions')

        tactical = {
            'events': {'count': events_count, 'planned_total': planned_total, 'actual_total': actual_total},
            'marketing': {'impressions': impressions, 'engagements': engagements, 'activations': activations, 'cost': marketing_cost},
            'funnel': {'conversion_rate': conversion_rate}
        }

        return {"status": "ok", "period": {"fy": fy, "qtr": qtr, "month": month}, "scope": {"type": scope_type, "value": scope_value}, "priorities": [], "loe_evaluation": [], "burden": {"ratio": None, "risk_band": "unknown"}, "processing_health": {"risk_band": "unknown", "top_issues": []}, "tactical_rollup": tactical, "missing_data": missing}
    except Exception:
        return {"status": "ok", "period": {}, "scope": {}, "priorities": [], "loe_evaluation": [], "burden": {}, "processing_health": {}, "tactical_rollup": {}, "missing_data": []}
