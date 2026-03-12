from fastapi import APIRouter, Query
from typing import Optional, List, Any, Dict
from services.api.app.db import connect, row_to_dict
from ..org_resolver import resolve_org_scope
from datetime import datetime

router = APIRouter(prefix="/ops/targeting", tags=["ops-targeting"])


def _now_iso():
    return datetime.utcnow().isoformat()


def _filters_dict(fy, qtr, month, unit_rsid):
    return {"fy": fy, "qtr": qtr, "month": month, "unit_rsid": unit_rsid}


@router.get('/summary')
def summary(fy: Optional[int] = None, qtr: Optional[int] = None, month: Optional[int] = None, unit_rsid: Optional[str] = None):
    conn = connect(); cur = conn.cursor()
    filters = _filters_dict(fy, qtr, month, unit_rsid)
    missing: List[str] = []
    try:
        where = ['1=1']
        params: List[Any] = []
        if fy is not None:
            where.append('fy = ?'); params.append(fy)
        if qtr is not None:
            where.append('qtr = ?'); params.append(qtr)
        if month is not None:
            where.append('month = ?'); params.append(month)

        if unit_rsid:
            try:
                scope = resolve_org_scope(unit_rsid)
                station_rsids = scope.get('station_rsids') or []
                if station_rsids:
                    where.append('station_rsid IN (' + ','.join('?' for _ in station_rsids) + ')')
                    params.extend(station_rsids)
                else:
                    where.append('unit_rsid LIKE ?'); params.append(f"{unit_rsid}%")
            except Exception:
                where.append('unit_rsid LIKE ?'); params.append(f"{unit_rsid}%")

        where_sql = ' AND '.join(where)

        # Check for derived scoring table
        try:
            cur.execute('SELECT COUNT(1) FROM targeting_score_snapshot WHERE ' + where_sql, params)
            cnt = cur.fetchone()[0] or 0
        except Exception:
            cnt = 0

        if cnt == 0:
            missing.append('targeting_score_snapshot empty')
            kpis = {'targets_total': 0, 'priority1': 0, 'priority2': 0, 'priority3': 0}
            top_targets: List[Dict] = []
            rows: List[Dict] = []
            data_as_of = None
        else:
            try:
                cur.execute(f"SELECT COUNT(1) as total, SUM(CASE WHEN priority_band='Priority 1' THEN 1 ELSE 0 END) as p1, SUM(CASE WHEN priority_band='Priority 2' THEN 1 ELSE 0 END) as p2, SUM(CASE WHEN priority_band='Priority 3' THEN 1 ELSE 0 END) as p3 FROM targeting_score_snapshot WHERE {where_sql}", params)
                agg = cur.fetchone() or [0,0,0,0]
                kpis = {'targets_total': int(agg[0]), 'priority1': int(agg[1]), 'priority2': int(agg[2]), 'priority3': int(agg[3])}
                cur.execute(f"SELECT target_id, target_type, name, unit_rsid, priority_band, scores FROM targeting_score_snapshot WHERE {where_sql} ORDER BY priority_score DESC LIMIT 50", params)
                raw = cur.fetchall() or []
                top_targets = [row_to_dict(cur, r) for r in raw]
                cur.execute(f"SELECT id, target_id, target_type, name, unit_rsid, priority_band, scores FROM targeting_score_snapshot WHERE {where_sql} LIMIT 1000", params)
                rows = [row_to_dict(cur, r) for r in cur.fetchall()]
                cur.execute(f"SELECT MAX(ingested_at) FROM targeting_score_snapshot WHERE {where_sql}", params)
                data_as_of = cur.fetchone()[0]
            except Exception:
                missing.append('query_error')
                kpis = {'targets_total': 0, 'priority1': 0, 'priority2': 0, 'priority3': 0}
                top_targets = []
                rows = []
                data_as_of = None

        return {"status": "ok", "data_as_of": data_as_of, "filters": filters, "kpis": kpis, "top_targets": top_targets, "rows": rows, "missing_data": missing}
    except Exception:
        return {"status": "ok", "data_as_of": None, "filters": filters, "kpis": {"targets_total":0, "priority1":0, "priority2":0, "priority3":0}, "top_targets": [], "rows": [], "missing_data": ["query_error"]}


@router.get('/targets')
def targets(fy: Optional[int] = None, qtr: Optional[int] = None, month: Optional[int] = None, unit_rsid: Optional[str] = None):
    conn = connect(); cur = conn.cursor()
    filters = _filters_dict(fy, qtr, month, unit_rsid)
    try:
        # ensure org scope is resolved (even if not used yet)
        unit_rsids = []
        if unit_rsid:
            try:
                scope = resolve_org_scope(unit_rsid)
                unit_rsids = scope.get('unit_rsids') or []
            except Exception:
                unit_rsids = []

        # Check for presence of a derived scoring table
        try:
            cur.execute('SELECT COUNT(1) FROM targeting_score_snapshot')
            cnt = cur.fetchone()[0] or 0
        except Exception:
            cnt = 0

        if cnt == 0:
            return {"status": "ok", "rows": [], "missing_data": ["targeting score inputs not loaded"]}

        # Read rows and map to the public target shape
        try:
            cur.execute('SELECT target_id, name as target_name, target_type, unit_rsid, scores, priority_band, recommended_action FROM targeting_score_snapshot LIMIT 1000')
            raw = cur.fetchall() or []
            out_rows: List[Dict] = []
            for r in raw:
                d = row_to_dict(cur, r)
                scores = d.get('scores') or {}
                # scores may be stored as JSON/text; if so, attempt parse
                if isinstance(scores, str):
                    try:
                        import json as _json
                        scores = _json.loads(scores)
                    except Exception:
                        scores = {}

                out_rows.append({
                    'target_id': d.get('target_id'),
                    'target_name': d.get('target_name') or d.get('name'),
                    'target_type': d.get('target_type'),
                    'unit_rsid': d.get('unit_rsid'),
                    'opportunity_score': scores.get('opportunity_score') if isinstance(scores, dict) else None,
                    'performance_score': scores.get('performance_score') if isinstance(scores, dict) else None,
                    'gap_score': scores.get('gap_score') if isinstance(scores, dict) else None,
                    'priority_score': scores.get('priority_score') if isinstance(scores, dict) else None,
                    'priority_band': d.get('priority_band'),
                    'recommended_action': d.get('recommended_action') or ''
                })

            return {"status": "ok", "rows": out_rows, "missing_data": []}
        except Exception:
            return {"status": "ok", "rows": [], "missing_data": ["query_error"]}
    except Exception:
        return {"status": "ok", "rows": [], "missing_data": ["query_error"]}



@router.get('/guidance')
def guidance(unit_rsid: Optional[str] = None):
    """Return Commander Guidance / Must Keep / Must Win blocks scoped by `unit_rsid`."""
    conn = connect(); cur = conn.cursor()
    try:
        if unit_rsid:
            cur.execute('SELECT id, unit_rsid, section, payload, created_at, updated_at FROM targeting_guidance WHERE unit_rsid = ? ORDER BY section', (unit_rsid,))
        else:
            cur.execute('SELECT id, unit_rsid, section, payload, created_at, updated_at FROM targeting_guidance ORDER BY unit_rsid, section')
        rows = [row_to_dict(cur, r) for r in cur.fetchall()]
        out = []
        for r in rows:
            p = r.get('payload')
            try:
                import json as _json
                p = _json.loads(p) if p else None
            except Exception:
                pass
            out.append({'id': r.get('id'), 'unit_rsid': r.get('unit_rsid'), 'section': r.get('section'), 'payload': p, 'created_at': r.get('created_at'), 'updated_at': r.get('updated_at')})
        return {'status': 'ok', 'rows': out}
    except Exception:
        return {'status': 'error', 'rows': []}


@router.post('/guidance')
def upsert_guidance(unit_rsid: str, section: str, payload: dict, id: Optional[str] = None):
    """Create or update a guidance block: section in ('commander_guidance','must_keep','must_win')."""
    conn = connect(); cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    rid = id or f"tg_{unit_rsid}_{section}"
    try:
        import json as _json
        cur.execute('INSERT OR REPLACE INTO targeting_guidance (id, unit_rsid, section, payload, created_at, updated_at) VALUES (?,?,?,?,?,?)', (rid, unit_rsid, section, _json.dumps(payload), now, now))
        try:
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
        return {'status': 'ok', 'id': rid}
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        return {'status': 'error'}
