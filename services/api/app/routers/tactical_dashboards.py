from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from services.api.app.db import connect
from datetime import datetime

router = APIRouter(prefix="/tactical", tags=["tactical"])


def _now_iso():
    return datetime.utcnow().isoformat()


def _filters_dict(**kwargs):
    return {k: v for k, v in kwargs.items() if v is not None}


@router.get('/events-roi')
def events_roi(fy: Optional[int] = Query(None), qtr: Optional[int] = Query(None), month: Optional[int] = Query(None), echelon_type: Optional[str] = Query(None), unit_value: Optional[str] = Query(None), funding_line: Optional[str] = Query(None)):
    conn = connect(); cur = conn.cursor()
    filters = _filters_dict(fy=fy, qtr=qtr, month=month, echelon_type=echelon_type, unit_value=unit_value, funding_line=funding_line)
    events: List[Dict[str, Any]] = []
    missing: List[str] = []
    try:
        # Prefer singular 'event' table, fallback to legacy 'events'
        cur.execute("PRAGMA table_info(event)")
        ecols = [r[1] for r in cur.fetchall()]
        if 'id' in ecols:
            where = []
            params = []
            if fy is not None and 'fy' in ecols:
                where.append('fy=?'); params.append(fy)
            if qtr is not None and 'qtr' in ecols:
                where.append('qtr=?'); params.append(qtr)
            if month is not None and 'month' in ecols:
                where.append('month=?'); params.append(month)
            if echelon_type is not None and 'echelon_type' in ecols:
                where.append('echelon_type=?'); params.append(echelon_type)
            if unit_value is not None and 'unit_value' in ecols:
                where.append('unit_value=?'); params.append(unit_value)
            if funding_line is not None and 'funding_line' in ecols:
                where.append('funding_line=?'); params.append(funding_line)
            where_sql = 'WHERE ' + ' AND '.join(where) if where else ''
            sel = 'id, COALESCE(name,\'\') as name, COALESCE(planned_cost,0) as planned_cost, COALESCE(actual_cost,0) as actual_cost, start_dt, end_dt'
            cur.execute(f"SELECT {sel} FROM event {where_sql} ORDER BY start_dt DESC LIMIT 500", params)
            for r in cur.fetchall():
                eid = str(r[0])
                events.append({'event_id': eid, 'name': r[1], 'planned_cost': r[2] or 0, 'actual_cost': r[3] or 0, 'start_date': r[4], 'end_date': r[5]})
        else:
            # legacy events
            cur.execute("PRAGMA table_info(events)")
            cols = [r[1] for r in cur.fetchall()]
            if 'event_id' in cols:
                sel = 'event_id, COALESCE(name,\'\') as name, COALESCE(planned_cost,COALESCE(budget,0)) as planned_cost, COALESCE(actual_cost,0) as actual_cost'
                cur.execute(f"SELECT {sel} FROM events ORDER BY planned_cost DESC LIMIT 500")
                for r in cur.fetchall():
                    events.append({'event_id': r[0], 'name': r[1], 'planned_cost': r[2] or 0, 'actual_cost': r[3] or 0})
            else:
                missing.append('events/event table not present')
    except Exception:
        missing.append('event selection failed')

    # marketing cost by event
    try:
        cur.execute('SELECT COALESCE(event_id,\'\') as event_id, COALESCE(SUM(cost),0) as cost, COALESCE(SUM(activation_conversions),0) as activations FROM marketing_activities GROUP BY event_id')
        mm = {r[0]: {'cost': r[1] or 0, 'activations': r[2] or 0} for r in cur.fetchall()}
    except Exception:
        mm = {}

    # funnel totals
    total_leads = 0
    total_activations = 0
    try:
        cur.execute('SELECT COUNT(1) FROM funnel_transitions')
        total_leads = cur.fetchone()[0] or 0
    except Exception:
        missing.append('funnel_transitions')
    try:
        # activations approximated by 'activation' stage or marketing conversions
        cur.execute("SELECT COUNT(1) FROM funnel_transitions WHERE to_stage='contract' OR to_stage='accession'")
        total_activations = cur.fetchone()[0] or 0
    except Exception:
        pass

    # attach marketing and compute per-event metrics
    planned_total = 0
    actual_total = 0
    marketing_total = 0
    for ev in events:
        eid = ev.get('event_id') or ''
        m = mm.get(eid, {'cost': 0, 'activations': 0})
        ev['marketing_cost'] = m['cost']
        ev['marketing_activations'] = m['activations']
        ev['leads'] = None
        planned_total += ev.get('planned_cost') or 0
        actual_total += ev.get('actual_cost') or 0
        marketing_total += m['cost'] or 0

    events_count = len(events)
    total_cost = (actual_total or 0) + (marketing_total or 0)
    cpl = (marketing_total / total_leads) if total_leads and total_leads > 0 else None
    cpa = (marketing_total / total_activations) if total_activations and total_activations > 0 else None

    rollup = {
        'events_count': events_count,
        'planned_cost_total': planned_total,
        'actual_cost_total': actual_total,
        'marketing_cost_total': marketing_total,
        'total_cost': total_cost,
        'total_leads': total_leads,
        'total_activations': total_activations,
        'cpl': cpl,
        'cpa': cpa,
        'roi': None
    }

    return {'status': 'ok', 'as_of': _now_iso(), 'filters': filters, 'rollup': rollup, 'events': events, 'missing_data': missing}


@router.get('/marketing')
def marketing(fy: Optional[int] = Query(None), qtr: Optional[int] = Query(None), month: Optional[int] = Query(None), echelon_type: Optional[str] = Query(None), unit_value: Optional[str] = Query(None), funding_line: Optional[str] = Query(None)):
    conn = connect(); cur = conn.cursor()
    filters = _filters_dict(fy=fy, qtr=qtr, month=month, echelon_type=echelon_type, unit_value=unit_value, funding_line=funding_line)
    missing: List[str] = []
    try:
        where = []
        params = []
        if fy is not None:
            where.append('fy=?'); params.append(fy)
        if qtr is not None:
            where.append('qtr=?'); params.append(qtr)
        if month is not None:
            where.append('month=?'); params.append(month)
        if echelon_type is not None:
            where.append('echelon_type=?'); params.append(echelon_type)
        if unit_value is not None:
            where.append('unit_value=?'); params.append(unit_value)
        if funding_line is not None:
            where.append('funding_line=?'); params.append(funding_line)
        where_sql = 'WHERE ' + ' AND '.join(where) if where else ''

        # totals
        cur.execute(f'SELECT COALESCE(SUM(cost),0), COALESCE(SUM(impressions),0), COALESCE(SUM(engagement_count),0), COALESCE(SUM(activation_conversions),0) FROM marketing_activities {where_sql}', params)
        r = cur.fetchone() or (0, 0, 0, 0)
        totals = {'impressions': r[1] or 0, 'engagements': r[2] or 0, 'activations': r[3] or 0, 'cost': r[0] or 0}

        # by_channel
        by_channel = []
        try:
            cur.execute(f'SELECT channel, COALESCE(SUM(cost),0), COALESCE(SUM(impressions),0), COALESCE(SUM(engagement_count),0), COALESCE(SUM(activation_conversions),0) FROM marketing_activities {where_sql} GROUP BY channel ORDER BY 2 DESC', params)
            for rr in cur.fetchall():
                by_channel.append({'channel': rr[0], 'cost': rr[1] or 0, 'impressions': rr[2] or 0, 'engagements': rr[3] or 0, 'activations': rr[4] or 0})
        except Exception:
            by_channel = []

        # by_event
        by_event = []
        try:
            cur.execute(f'SELECT COALESCE(event_id,\'\') as event_id, COALESCE(SUM(cost),0) as cost, COALESCE(SUM(impressions),0) as impressions, COALESCE(SUM(activation_conversions),0) as activations FROM marketing_activities {where_sql} GROUP BY event_id ORDER BY 2 DESC', params)
            for rr in cur.fetchall():
                by_event.append({'event_id': rr[0], 'cost': rr[1] or 0, 'impressions': rr[2] or 0, 'activations': rr[3] or 0})
        except Exception:
            by_event = []

        efficiency = {
            'cpe': (totals['cost'] / totals['engagements']) if totals['engagements'] and totals['engagements'] > 0 else None,
            'cpa': (totals['cost'] / totals['activations']) if totals['activations'] and totals['activations'] > 0 else None,
            'cpm': (totals['cost'] / totals['impressions'] * 1000) if totals['impressions'] and totals['impressions'] > 0 else None
        }
        return {'status': 'ok', 'as_of': _now_iso(), 'filters': filters, 'rollup': efficiency, 'by_channel': by_channel, 'by_event': by_event, 'missing_data': missing}
    except Exception:
        return {'status': 'ok', 'as_of': _now_iso(), 'rollup': {'cpe': None, 'cpa': None, 'cpm': None}, 'by_channel': [], 'by_event': [], 'missing_data': ['marketing_activities']}


@router.get('/funnel')
def funnel(fy: Optional[int] = Query(None), qtr: Optional[int] = Query(None), month: Optional[int] = Query(None), echelon_type: Optional[str] = Query(None), unit_value: Optional[str] = Query(None)):
    conn = connect(); cur = conn.cursor()
    filters = _filters_dict(fy=fy, qtr=qtr, month=month, echelon_type=echelon_type, unit_value=unit_value)
    try:
        cur.execute('SELECT id, name, rank FROM funnel_stages ORDER BY rank')
        stages = [{'id': r[0], 'name': r[1], 'rank': r[2]} for r in cur.fetchall()]
    except Exception:
        stages = []

    conv = []
    try:
        cur.execute('SELECT from_stage, to_stage, COUNT(1) as cnt FROM funnel_transitions GROUP BY from_stage, to_stage')
        conv = [{'from_stage': r[0], 'to_stage': r[1], 'count': r[2]} for r in cur.fetchall()]
    except Exception:
        conv = []

    # compute conversion rates for adjacent stages
    conversions = []
    try:
        ordered = [s['id'] for s in stages]
        counts = {c['from_stage']: c['count'] for c in conv}
        for i in range(len(ordered)-1):
            a = ordered[i]; b = ordered[i+1]
            moved = 0
            for c in conv:
                if c['from_stage'] == a and c['to_stage'] == b:
                    moved = c['count']
            total_from = counts.get(a, 0)
            rate = (moved / total_from) if total_from and total_from > 0 else None
            conversions.append({'from_stage': a, 'to_stage': b, 'count': moved, 'conversion_rate': rate})
    except Exception:
        conversions = []

    return {'status': 'ok', 'as_of': _now_iso(), 'filters': filters, 'stages': stages, 'stages_conv': conversions, 'bottlenecks': []}
