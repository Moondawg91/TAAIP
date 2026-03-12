from fastapi import APIRouter, Query
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from services.api.app.db import connect

router = APIRouter()

logger = logging.getLogger(__name__)


def _now_iso():
    return datetime.utcnow().isoformat()


def _filters_dict(**kwargs):
    return {k: v for k, v in kwargs.items() if v is not None}


@router.get("/rollups/budget")
def budget_rollup(fy: Optional[int] = Query(None), qtr: Optional[int] = Query(None), scope_type: Optional[str] = None, scope_value: Optional[str] = None, station_rsid: Optional[str] = None, funding_source: Optional[str] = None):
    conn = connect()
    cur = conn.cursor()
    where = []
    params = []
    if fy is not None:
        where.append("fy = ?")
        params.append(fy)
    if qtr is not None:
        where.append("qtr = ?")
        params.append(qtr)
    if scope_type is not None:
        where.append("scope_type = ?")
        params.append(scope_type)
    if scope_value is not None:
        where.append("scope_value = ?")
        params.append(scope_value)
    if station_rsid is not None:
        where.append("station_rsid = ?")
        params.append(station_rsid)
    if funding_source is not None:
        where.append("funding_source = ?")
        params.append(funding_source)
    where_clause = "WHERE " + " AND ".join(where) if where else ""

    q_totals = f"SELECT COALESCE(SUM(allocated_amount),0) as allocated, COALESCE(SUM(obligated_amount),0) as obligated, COALESCE(SUM(expended_amount),0) as expended FROM budget_line_item {where_clause}"
    cur.execute(q_totals, params)
    row = cur.fetchone() or (0, 0, 0)
    allocated, obligated, expended = row[0] or 0, row[1] or 0, row[2] or 0
    remaining = (allocated or 0) - (expended or 0)

    def top_by(col):
        q = f"SELECT {col}, COALESCE(SUM(expended_amount),0) as val FROM budget_line_item {where_clause} GROUP BY {col} ORDER BY val DESC LIMIT 10"
        cur.execute(q, params)
        return [{"key": r[0], "value": r[1]} for r in cur.fetchall()]

    breakdown_by_funding = []
    try:
        cur.execute(f"SELECT COALESCE(funding_source,'') as fs, COALESCE(SUM(expended_amount),0) FROM budget_line_item {where_clause} GROUP BY funding_source ORDER BY 2 DESC")
        breakdown_by_funding = [{"funding_source": r[0], "expended": r[1]} for r in cur.fetchall()]
    except Exception:
        breakdown_by_funding = []

    resp = {
        "status": "ok",
        "as_of": _now_iso(),
        "filters": _filters_dict(fy=fy, qtr=qtr, scope_type=scope_type, scope_value=scope_value, station_rsid=station_rsid, funding_source=funding_source),
        "data": {
            "totals": {"allocated": allocated, "obligated": obligated, "expended": expended, "remaining": remaining},
            "breakdown_by_funding_source": breakdown_by_funding,
            "breakdown_by_category": top_by('category'),
            "breakdown_by_project": top_by('project_id'),
            "breakdown_by_event": top_by('event_id'),
            "data_freshness": {}
        }
    }
    try:
        cur.execute("SELECT MAX(ingested_at), MAX(updated_at) FROM budget_line_item")
        fres = cur.fetchone()
        resp['data']['data_freshness'] = {"last_import_at": fres[0], "last_updated_at": fres[1]}
    except Exception:
        resp['data']['data_freshness'] = {"last_import_at": None, "last_updated_at": None}
    return resp


@router.get("/rollups/events")
def events_rollup(fy: Optional[int] = None, qtr: Optional[int] = None, scope_type: Optional[str] = None, scope_value: Optional[str] = None, station_rsid: Optional[str] = None, event_id: Optional[str] = None, debug: bool = False):
    conn = connect()
    cur = conn.cursor()
    diagnostics = []
    where = []
    params = []
    if fy is not None:
        where.append("e.fy = ?")
        params.append(fy)
    if qtr is not None:
        where.append("e.qtr = ?")
        params.append(qtr)
    if scope_type is not None:
        where.append("e.scope_type = ?")
        params.append(scope_type)
    if scope_value is not None:
        where.append("e.scope_value = ?")
        params.append(scope_value)
    if station_rsid is not None:
        where.append("e.station_rsid = ?")
        params.append(station_rsid)
    if event_id is not None:
        where.append("(e.event_id = ? OR e.id = ?) ")
        params.extend([event_id, event_id])
    where_clause = "WHERE " + " AND ".join(where) if where else ""

    # List events
    # Helper to detect columns on a table
    def table_has_cols(tbl, cols_needed):
        try:
            cur.execute(f"PRAGMA table_info({tbl})")
            existing = [r[1] for r in cur.fetchall()]
            return all(c in existing for c in cols_needed)
        except Exception:
            return False

    events = []
    # Query legacy 'events' table if present
    try:
        if table_has_cols('events', ['event_id', 'name']):
            try:
                cur.execute("PRAGMA table_info(events)")
                cols = [r[1] for r in cur.fetchall()]
                cur.execute("SELECT COUNT(1) FROM events")
                cnt = cur.fetchone()[0] or 0
                diagnostics.append({"table": "events", "columns": cols, "row_count": cnt})
            except Exception:
                diagnostics.append({"table": "events", "columns": [], "row_count": 0})
            # build a where clause only for columns that exist on this table
            ev_where = []
            ev_params = []
            if 'fy' in cols and fy is not None:
                ev_where.append('fy = ?'); ev_params.append(fy)
            if 'qtr' in cols and qtr is not None:
                ev_where.append('qtr = ?'); ev_params.append(qtr)
            if 'scope_type' in cols and scope_type is not None:
                ev_where.append('scope_type = ?'); ev_params.append(scope_type)
            if 'scope_value' in cols and scope_value is not None:
                ev_where.append('scope_value = ?'); ev_params.append(scope_value)
            ev_where_clause = 'WHERE ' + ' AND '.join(ev_where) if ev_where else ''
            cur.execute(f"SELECT event_id, name, COALESCE(budget,0) FROM events {ev_where_clause} ORDER BY 3 DESC LIMIT 200", ev_params)
            for r in cur.fetchall():
                ev_id = r[0]
                planned = r[2] or 0
                try:
                    cur.execute("SELECT COALESCE(SUM(expended_amount),0) FROM budget_line_item WHERE event_id = ?", (ev_id,))
                    actual = cur.fetchone()[0] or 0
                except Exception:
                    actual = 0
                events.append({"event_id": ev_id, "name": r[1], "planned_cost": planned, "actual_cost": actual, "variance": planned - actual})
    except Exception:
        logger.exception("error querying legacy events table")

    # Also query singular 'event' table
    try:
        if table_has_cols('event', ['id', 'name']):
            try:
                cur.execute("PRAGMA table_info(event)")
                ecols = [r[1] for r in cur.fetchall()]
                cur.execute("SELECT COUNT(1) FROM event")
                ecnt = cur.fetchone()[0] or 0
                diagnostics.append({"table": "event", "columns": ecols, "row_count": ecnt})
            except Exception:
                diagnostics.append({"table": "event", "columns": [], "row_count": 0})
            ev_where = []
            ev_params = []
            if 'fy' in ecols and fy is not None:
                ev_where.append('fy = ?'); ev_params.append(fy)
            if 'qtr' in ecols and qtr is not None:
                ev_where.append('qtr = ?'); ev_params.append(qtr)
            ev_where_clause = 'WHERE ' + ' AND '.join(ev_where) if ev_where else ''
            # prefer planned_cost column if available
            if 'planned_cost' in ecols:
                cur.execute(f"SELECT id, name, COALESCE(planned_cost, budget, 0) FROM event {ev_where_clause} ORDER BY 3 DESC LIMIT 200", ev_params)
            else:
                cur.execute(f"SELECT id, name, COALESCE(budget, 0) FROM event {ev_where_clause} ORDER BY 3 DESC LIMIT 200", ev_params)
            for r in cur.fetchall():
                ev_id = str(r[0])
                planned = r[2] or 0
                try:
                    cur.execute("SELECT COALESCE(SUM(expended_amount),0) FROM budget_line_item WHERE event_id = ?", (ev_id,))
                    actual = cur.fetchone()[0] or 0
                except Exception:
                    actual = 0
                # avoid duplicates
                if not any(e.get('event_id') == ev_id for e in events):
                    events.append({"event_id": ev_id, "name": r[1], "planned_cost": planned, "actual_cost": actual, "variance": planned - actual})
    except Exception:
        logger.exception("error querying singular event table")

    # Event outcomes: best-effort counts
    missing_fields: List[str] = []
    try:
        cur.execute("SELECT COUNT(1) FROM funnel_transitions")
        leads = cur.fetchone()[0] or 0
    except Exception:
        leads = 0
        missing_fields.append('funnel_transitions')
    try:
        cur.execute("SELECT COUNT(1) FROM outcomes WHERE status='contract'")
        contracts = cur.fetchone()[0] or 0
    except Exception:
        contracts = 0
        missing_fields.append('outcomes')
    try:
        cur.execute("SELECT COUNT(1) FROM outcomes WHERE status='ship'")
        ships = cur.fetchone()[0] or 0
    except Exception:
        ships = 0
        if 'outcomes' not in missing_fields:
            missing_fields.append('outcomes')

    # Link marketing cost by event
    try:
        cur.execute("SELECT event_id, COALESCE(SUM(cost),0), COALESCE(SUM(conversions),0) FROM marketing_activities GROUP BY event_id")
        marketing_map = {r[0]: {"cost": r[1], "conversions": r[2]} for r in cur.fetchall()}
    except Exception:
        marketing_map = {}

    # Compute ROI metrics per event aggregated
    for ev in events:
        mid = ev.get('event_id')
        m = marketing_map.get(mid, {"cost": 0, "conversions": 0})
        ev['marketing_cost'] = m['cost']
        ev['marketing_conversions'] = m['conversions']
        leads_for_event = leads if leads > 0 else 0
        ev['cpl'] = (m['cost'] / leads_for_event) if leads_for_event > 0 else None
        ev['cpc'] = (m['cost'] / m['conversions']) if m['conversions'] and m['conversions'] > 0 else None

    resp = {"status": "ok", "as_of": _now_iso(), "filters": _filters_dict(fy=fy, qtr=qtr, scope_type=scope_type, scope_value=scope_value, station_rsid=station_rsid, event_id=event_id), "data": {"events": events, "event_outcomes": {"leads": leads, "contracts": contracts, "ships": ships}, "missing_fields": missing_fields}}
    if debug:
        try:
            logger.info("events_rollup diagnostics: %s", diagnostics)
            resp['data']['diagnostics'] = diagnostics
        except Exception:
            pass
    return resp


@router.get("/rollups/marketing")
def marketing_rollup(fy: Optional[int] = None, qtr: Optional[int] = None, scope_type: Optional[str] = None, scope_value: Optional[str] = None, station_rsid: Optional[str] = None, event_id: Optional[str] = None, campaign_id: Optional[str] = None):
    conn = connect()
    cur = conn.cursor()
    where = []
    params = []
    if fy is not None:
        where.append("fy = ?")
        params.append(fy)
    if qtr is not None:
        where.append("qtr = ?")
        params.append(qtr)
    if scope_type is not None:
        where.append("scope_type = ?")
        params.append(scope_type)
    if scope_value is not None:
        where.append("scope_value = ?")
        params.append(scope_value)
    if station_rsid is not None:
        where.append("station_rsid = ?")
        params.append(station_rsid)
    if event_id is not None:
        where.append("event_id = ?")
        params.append(event_id)
    if campaign_id is not None:
        where.append("campaign_id = ?")
        params.append(campaign_id)
    where_clause = "WHERE " + " AND ".join(where) if where else ""

    # support legacy column names: impressions, engagement_count, activation_conversions, cost
    q = f"SELECT COALESCE(SUM(impressions),0), COALESCE(SUM(engagement_count),0), COALESCE(SUM(activation_conversions),0), COALESCE(SUM(cost),0) FROM marketing_activities {where_clause}"
    try:
        cur.execute(q, params)
        tot = cur.fetchone() or (0, 0, 0, 0, 0)
    except Exception:
        tot = (0, 0, 0, 0, 0)
    impressions, engagements, conversions, cost = (tot[0] or 0, tot[1] or 0, tot[2] or 0, tot[3] or 0)

    efficiency = {
        "cpm": (cost / impressions * 1000) if impressions and impressions > 0 else None,
        "cpe": (cost / engagements) if engagements and engagements > 0 else None,
        "cpc": None,
        "cpa": (cost / conversions) if conversions and conversions > 0 else None,
    }

    # by_channel breakdown
    by_channel = []
    try:
        cur.execute(f"SELECT channel, COALESCE(SUM(impressions),0), COALESCE(SUM(engagement_count),0), COALESCE(SUM(activation_conversions),0), COALESCE(SUM(cost),0) FROM marketing_activities {where_clause} GROUP BY channel ORDER BY 5 DESC")
        by_channel = [{"channel": r[0], "impressions": r[1], "engagements": r[2], "conversions": r[3], "cost": r[4]} for r in cur.fetchall()]
    except Exception:
        by_channel = []

    attribution_mode = 'direct' if event_id else ('campaign' if campaign_id else 'data_source')

    return {"status": "ok", "as_of": _now_iso(), "filters": _filters_dict(fy=fy, qtr=qtr, scope_type=scope_type, scope_value=scope_value, station_rsid=station_rsid, event_id=event_id, campaign_id=campaign_id), "data": {"totals": {"impressions": impressions, "engagements": engagements, "clicks": clicks, "conversions": conversions, "cost": cost}, "efficiency": efficiency, "by_channel": by_channel, "attribution_mode": attribution_mode}}


@router.get("/rollups/funnel")
def funnel_rollup(fy: Optional[int] = None, qtr: Optional[int] = None, scope_type: Optional[str] = None, scope_value: Optional[str] = None, station_rsid: Optional[str] = None):
    conn = connect()
    cur = conn.cursor()
    # stages ordered
    stages = []
    try:
        cur.execute("SELECT id, name, rank FROM funnel_stages ORDER BY rank ASC")
        stages = [{"id": r[0], "name": r[1], "rank": r[2]} for r in cur.fetchall()]
    except Exception:
        stages = []

    # transitions counts between stages
    dropoffs = []
    try:
        cur.execute("SELECT from_stage, to_stage, COUNT(1) FROM funnel_transitions GROUP BY from_stage, to_stage")
        trans = [{"from": r[0], "to": r[1], "count": r[2]} for r in cur.fetchall()]
    except Exception:
        trans = []

    # compute simple conversion rates
    conv_rates = []
    try:
        # for each stage compute ingress and egress
        for i in range(len(stages)-1):
            a = stages[i]['id']
            b = stages[i+1]['id']
            cur.execute("SELECT COUNT(1) FROM funnel_transitions WHERE from_stage = ? AND to_stage = ?", (a, b))
            moved = cur.fetchone()[0] or 0
            cur.execute("SELECT COUNT(1) FROM funnel_transitions WHERE from_stage = ?", (a,))
            total_from = cur.fetchone()[0] or 0
            rate = (moved / total_from) if total_from and total_from > 0 else None
            conv_rates.append({"from": a, "to": b, "rate": rate, "moved": moved, "total_from": total_from})
    except Exception:
        conv_rates = []

    # average time-in-stage (best-effort using transitioned_at)
    avg_time = None
    try:
        cur.execute("SELECT AVG(julianday(to_t.updated_at) - julianday(from_t.updated_at)) as days_avg FROM (SELECT lead_id, transitioned_at as updated_at FROM funnel_transitions) as from_t JOIN (SELECT lead_id, transitioned_at as updated_at FROM funnel_transitions) as to_t ON from_t.lead_id = to_t.lead_id WHERE to_t.updated_at > from_t.updated_at")
        avg_time = cur.fetchone()[0]
    except Exception:
        avg_time = None

    # bottleneck flags simple thresholds
    bottlenecks = []
    try:
        for cr in conv_rates:
            if cr['rate'] is not None and cr['rate'] < 0.2:
                bottlenecks.append({"from": cr['from'], "to": cr['to'], "reason": "high_dropoff", "rate": cr['rate']})
    except Exception:
        bottlenecks = []

    return {"status": "ok", "as_of": _now_iso(), "filters": _filters_dict(fy=fy, qtr=qtr, scope_type=scope_type, scope_value=scope_value, station_rsid=station_rsid), "data": {"stages": stages, "conversion_rates": conv_rates, "dropoffs": trans, "average_time_in_stage_days": avg_time, "bottlenecks": bottlenecks}}


@router.get("/rollups/command")
def command_rollup(fy: Optional[int] = None, qtr: Optional[int] = None, scope_type: Optional[str] = None, scope_value: Optional[str] = None):
    conn = connect()
    cur = conn.cursor()
    # pull command priorities
    try:
        cur.execute("SELECT id, title, description FROM command_priorities ORDER BY rank ASC")
        priorities = [{"id": r[0], "title": r[1], "description": r[2]} for r in cur.fetchall()]
    except Exception:
        priorities = []

    # LOE evaluation: load loes and mappings
    loe_statuses = []
    try:
        cur.execute("SELECT id, name FROM loe")
        loes = cur.fetchall()
        for l in loes:
            lid = l[0]
            lname = l[1]
            # load metric mappings
            cur.execute("SELECT metric_key, metric_type, threshold, comparator FROM loe_metric_map WHERE loe_id = ?", (lid,))
            maps = cur.fetchall()
            overall = "MET"
            rationale = []
            for m in maps:
                metric_key, metric_type, threshold, comparator = m[0], m[1], m[2], m[3]
                # very small evaluator: support budget.expended and events.leads
                val = None
                if metric_type == 'budget' and metric_key == 'expended':
                    cur.execute("SELECT COALESCE(SUM(expended_amount),0) FROM budget_line_item WHERE fy = ? AND qtr = ?", (fy, qtr))
                    val = cur.fetchone()[0] or 0
                elif metric_type == 'events' and metric_key == 'leads':
                    cur.execute("SELECT COUNT(1) FROM funnel_transitions")
                    val = cur.fetchone()[0] or 0
                else:
                    val = None
                if val is None:
                    status = 'AT_RISK'
                    rationale.append(f"metric {metric_key} not available")
                    overall = 'AT_RISK'
                else:
                    try:
                        if comparator in ('lte', '<='):
                            good = (val <= threshold)
                        else:
                            good = (val >= threshold)
                        status = 'MET' if good else 'NOT_MET'
                        if not good and overall != 'NOT_MET':
                            overall = 'NOT_MET'
                        rationale.append(f"{metric_type}.{metric_key}={val} {comparator} {threshold} => {status}")
                    except Exception:
                        status = 'AT_RISK'
                        overall = 'AT_RISK'
                        rationale.append(f"error evaluating {metric_key}")
                loe_statuses.append({"loe_id": lid, "loe_name": lname, "metric": metric_key, "status": status})
    except Exception:
        loe_statuses = []

    return {"status": "ok", "as_of": _now_iso(), "filters": _filters_dict(fy=fy, qtr=qtr, scope_type=scope_type, scope_value=scope_value), "data": {"priorities": priorities, "loe_statuses": loe_statuses}}
from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime
from services.api.app.db import connect

router = APIRouter()


def _now_iso():
    return datetime.utcnow().isoformat()


def _filters_dict(fy, qtr, scope_type, scope_value, station_rsid=None, **kwargs):
    return {k: v for k, v in dict(fy=fy, qtr=qtr, scope_type=scope_type, scope_value=scope_value, station_rsid=station_rsid, **kwargs).items() if v is not None}


@router.get("/rollups/budget")
def budget_rollup(fy: Optional[int] = Query(None), qtr: Optional[int] = Query(None), scope_type: Optional[str] = Query(None), scope_value: Optional[str] = Query(None), station_rsid: Optional[str] = Query(None), funding_source: Optional[str] = Query(None)):
    conn = connect()
    cur = conn.cursor()
    filters = _filters_dict(fy, qtr, scope_type, scope_value, station_rsid, funding_source=funding_source)
    params = []
    where = []
    if fy is not None:
        where.append("fy = ?")
        params.append(fy)
    if qtr is not None:
        where.append("qtr = ?")
        params.append(qtr)
    if scope_type is not None:
        where.append("scope_type = ?")
        params.append(scope_type)
    if scope_value is not None:
        where.append("scope_value = ?")
        params.append(scope_value)
    if station_rsid is not None:
        where.append("station_rsid = ?")
        params.append(station_rsid)
    if funding_source is not None:
        where.append("funding_source = ?")
        params.append(funding_source)

    where_sql = "WHERE " + " AND ".join(where) if where else ""

    # totals
    try:
        cur.execute(f"SELECT COALESCE(SUM(allocated_amount),0) as allocated, COALESCE(SUM(obligated_amount),0) as obligated, COALESCE(SUM(expended_amount),0) as expended FROM budget_line_item {where_sql}", params)
        row = cur.fetchone() or (0, 0, 0)
        allocated, obligated, expended = row[0] or 0, row[1] or 0, row[2] or 0
    except Exception:
        allocated = obligated = expended = 0

    remaining = allocated - expended

    # breakdowns
    breakdown_by_funding = []
    try:
        q = f"SELECT funding_source, COALESCE(SUM(allocated_amount),0) as allocated, COALESCE(SUM(expended_amount),0) as expended FROM budget_line_item {where_sql} GROUP BY funding_source ORDER BY allocated DESC LIMIT 50"
        cur.execute(q, params)
        for r in cur.fetchall():
            breakdown_by_funding.append({'funding_source': r[0], 'allocated': r[1] or 0, 'expended': r[2] or 0})
    except Exception:
        pass

    breakdown_by_category = []
    try:
        q = f"SELECT category, COALESCE(SUM(allocated_amount),0) as allocated FROM budget_line_item {where_sql} GROUP BY category ORDER BY allocated DESC LIMIT 50"
        cur.execute(q, params)
        for r in cur.fetchall():
            breakdown_by_category.append({'category': r[0], 'allocated': r[1] or 0})
    except Exception:
        pass

    breakdown_by_project = []
    try:
        q = f"SELECT project_id, COALESCE(SUM(allocated_amount),0) as allocated FROM budget_line_item {where_sql} GROUP BY project_id ORDER BY allocated DESC LIMIT 10"
        cur.execute(q, params)
        for r in cur.fetchall():
            breakdown_by_project.append({'project_id': r[0], 'allocated': r[1] or 0})
    except Exception:
        pass

    breakdown_by_event = []
    try:
        q = f"SELECT event_id, COALESCE(SUM(allocated_amount),0) as allocated FROM budget_line_item {where_sql} GROUP BY event_id ORDER BY allocated DESC LIMIT 10"
        cur.execute(q, params)
        for r in cur.fetchall():
            breakdown_by_event.append({'event_id': r[0], 'allocated': r[1] or 0})
    except Exception:
        pass

    # data freshness: last import or updated timestamps
    last_import_at = None
    last_updated_at = None
    try:
        cur.execute("SELECT MAX(ingested_at) FROM budget_line_item")
        last_import_at = (cur.fetchone() or [None])[0]
        cur.execute("SELECT MAX(updated_at) FROM budget_line_item")
        last_updated_at = (cur.fetchone() or [None])[0]
    except Exception:
        pass

    return {
        'status': 'ok',
        'as_of': _now_iso(),
        'filters': filters,
        'data': {
            'totals': {'allocated': allocated, 'obligated': obligated, 'expended': expended, 'remaining': remaining},
            'breakdown_by_funding_source': breakdown_by_funding,
            'breakdown_by_category': breakdown_by_category,
            'breakdown_by_project': breakdown_by_project,
            'breakdown_by_event': breakdown_by_event,
            'data_freshness': {'last_import_at': last_import_at, 'last_updated_at': last_updated_at}
        }
    }


@router.get("/rollups/events")
def events_rollup(fy: Optional[int] = Query(None), qtr: Optional[int] = Query(None), scope_type: Optional[str] = Query(None), scope_value: Optional[str] = Query(None), station_rsid: Optional[str] = Query(None), event_id: Optional[str] = Query(None), debug: Optional[bool] = Query(None)):
    conn = connect()
    cur = conn.cursor()
    filters = _filters_dict(fy, qtr, scope_type, scope_value, station_rsid, event_id=event_id)
    where = []
    params = []
    if event_id:
        where.append("event_id = ?")
        params.append(event_id)
    if fy is not None:
        where.append("fy = ?")
        params.append(fy)
    if qtr is not None:
        where.append("qtr = ?")
        params.append(qtr)
    if scope_type is not None:
        where.append("scope_type = ?")
        params.append(scope_type)
    if scope_value is not None:
        where.append("scope_value = ?")
        params.append(scope_value)
    if station_rsid is not None:
        where.append("station_rsid = ?")
        params.append(station_rsid)
    where_sql = "WHERE " + " AND ".join(where) if where else ""

    events = []
    diagnostics = []
    # gather diagnostics about event tables for debug endpoint
    try:
        cur.execute("PRAGMA table_info(events)")
        ecols = [r[1] for r in cur.fetchall()]
        cur.execute("SELECT COUNT(1) FROM events")
        ecnt = cur.fetchone()[0] or 0
        diagnostics.append({"table": "events", "columns": ecols, "row_count": ecnt})
    except Exception:
        diagnostics.append({"table": "events", "columns": [], "row_count": 0})
    try:
        cur.execute("PRAGMA table_info(event)")
        ecols2 = [r[1] for r in cur.fetchall()]
        cur.execute("SELECT COUNT(1) FROM event")
        ecnt2 = cur.fetchone()[0] or 0
        diagnostics.append({"table": "event", "columns": ecols2, "row_count": ecnt2})
    except Exception:
        diagnostics.append({"table": "event", "columns": [], "row_count": 0})
    try:
        # build a safe select for events table depending on available columns
        try:
            cur.execute("PRAGMA table_info(events)")
            ev_cols = [r[1] for r in cur.fetchall()]
        except Exception:
            ev_cols = []
        if 'planned_cost' in ev_cols:
            sel = "COALESCE(e.planned_cost,0) as planned_cost, COALESCE(e.planned_cost,0) as actual_cost"
        elif 'budget' in ev_cols:
            sel = "COALESCE(e.budget,0) as planned_cost, COALESCE(e.budget,0) as actual_cost"
        else:
            sel = "0 as planned_cost, 0 as actual_cost"
        q = f"SELECT e.event_id, e.name, {sel} FROM events e {where_sql} LIMIT 500"
        cur.execute(q, params)
        for r in cur.fetchall():
            events.append({'event_id': r[0], 'name': r[1], 'planned_cost': r[2] or 0, 'actual_cost': r[3] or 0, 'variance': (r[3] or 0) - (r[2] or 0)})
    except Exception:
        logger.exception("error selecting from events table")

    # link marketing costs by event_id
    marketing_by_event = {}
    try:
        q = f"SELECT COALESCE(event_id,'') as event_id, COALESCE(SUM(cost),0) as cost, COALESCE(SUM(conversions),0) as conversions FROM marketing_activities {where_sql} GROUP BY event_id"
        cur.execute(q, params)
        for r in cur.fetchall():
            marketing_by_event[r[0]] = {'cost': r[1] or 0, 'conversions': r[2] or 0}
    except Exception:
        pass

    # outcomes rollup (best-effort)
    outcomes = {'leads': 0, 'qualified': 0, 'contracts': 0, 'ships': 0}
    missing_fields = []
    try:
        # if outcomes table exists, aggregate
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='outcomes'")
        if cur.fetchone():
            cur.execute("SELECT COUNT(1) FROM outcomes")
            outcomes['contracts'] = (cur.fetchone() or [0])[0] or 0
        else:
            missing_fields.append('outcomes')
    except Exception:
        pass

    # attach marketing sums to events list
    for ev in events:
        mid = ev.get('event_id') or ''
        mk = marketing_by_event.get(mid, {'cost': 0, 'conversions': 0})
        ev['marketing_cost'] = mk['cost']
        ev['marketing_conversions'] = mk['conversions']

    # ROI metrics sample: CPL (cost per lead), CPC (cost per click), CPS (cost per sale)
    roi = None
    try:
        # compute over all marketing rows in scope
        cur.execute(f"SELECT COALESCE(SUM(cost),0), COALESCE(SUM(conversions),0), COALESCE(SUM(clicks),0) FROM marketing_activities {where_sql}", params)
        r = cur.fetchone() or (0, 0, 0)
        total_cost, total_conv, total_clicks = r[0] or 0, r[1] or 0, r[2] or 0
        roi = {
            'CPL': (total_cost / total_conv) if total_conv and total_conv > 0 else None,
            'CPC': (total_cost / total_clicks) if total_clicks and total_clicks > 0 else None,
            'CPS': (total_cost / outcomes.get('contracts')) if outcomes.get('contracts') else None,
        }
    except Exception:
        roi = {'CPL': None, 'CPC': None, 'CPS': None}

    resp = {'status': 'ok', 'as_of': _now_iso(), 'filters': filters, 'data': {'events': events, 'event_outcomes': outcomes, 'missing_fields': missing_fields, 'ROI': roi}}
    if debug:
        try:
            resp['data']['diagnostics'] = diagnostics
        except Exception:
            pass
    return resp


@router.get("/rollups/marketing")
def marketing_rollup(fy: Optional[int] = Query(None), qtr: Optional[int] = Query(None), scope_type: Optional[str] = Query(None), scope_value: Optional[str] = Query(None), station_rsid: Optional[str] = Query(None), event_id: Optional[str] = Query(None), campaign_id: Optional[str] = Query(None), debug: Optional[bool] = Query(None)):
    conn = connect()
    cur = conn.cursor()
    filters = _filters_dict(fy, qtr, scope_type, scope_value, station_rsid, event_id=event_id, campaign_id=campaign_id)
    where = []
    params = []
    if fy is not None:
        where.append("fy = ?")
        params.append(fy)
    if qtr is not None:
        where.append("qtr = ?")
        params.append(qtr)
    if scope_type is not None:
        where.append("scope_type = ?")
        params.append(scope_type)
    if scope_value is not None:
        where.append("scope_value = ?")
        params.append(scope_value)
    if station_rsid is not None:
        where.append("station_rsid = ?")
        params.append(station_rsid)
    if event_id is not None:
        where.append("event_id = ?")
        params.append(event_id)
    if campaign_id is not None:
        where.append("campaign_id = ?")
        params.append(campaign_id)
    where_sql = "WHERE " + " AND ".join(where) if where else ""

    # diagnostics for debug
    diagnostics = []
    try:
        cur.execute("PRAGMA table_info(marketing_activities)")
        mcols = [r[1] for r in cur.fetchall()]
        cur.execute("SELECT COUNT(1) FROM marketing_activities")
        mcount = cur.fetchone()[0] or 0
        diagnostics.append({"table": "marketing_activities", "columns": mcols, "row_count": mcount})
    except Exception:
        diagnostics.append({"table": "marketing_activities", "columns": [], "row_count": 0})

    totals = {'impressions': 0, 'engagements': 0, 'conversions': 0, 'cost': 0}
    try:
        # support legacy names: impressions, engagement_count, activation_conversions, cost
        q = f"SELECT COALESCE(SUM(impressions),0), COALESCE(SUM(engagement_count),0), COALESCE(SUM(activation_conversions),0), COALESCE(SUM(cost),0) FROM marketing_activities {where_sql}"
        cur.execute(q, params)
        r = cur.fetchone() or (0, 0, 0, 0)
        totals = {'impressions': r[0] or 0, 'engagements': r[1] or 0, 'conversions': r[2] or 0, 'cost': r[3] or 0}
    except Exception:
        pass

    efficiency = {
        'cpm': (totals['cost'] / totals['impressions'] * 1000) if totals['impressions'] and totals['impressions'] > 0 else None,
        'cpe': (totals['cost'] / totals['engagements']) if totals['engagements'] and totals['engagements'] > 0 else None,
        'cpc': None,
        'cpa': (totals['cost'] / totals['conversions']) if totals['conversions'] and totals['conversions'] > 0 else None,
    }

    by_channel = []
    try:
        cur.execute(f"SELECT channel, COALESCE(SUM(impressions),0), COALESCE(SUM(engagement_count),0), COALESCE(SUM(activation_conversions),0), COALESCE(SUM(cost),0) FROM marketing_activities {where_sql} GROUP BY channel ORDER BY 5 DESC", params)
        by_channel = [{"channel": r[0], "impressions": r[1], "engagements": r[2], "conversions": r[3], "cost": r[4]} for r in cur.fetchall()]
    except Exception:
        by_channel = []

    attribution = 'data_source'
    if event_id:
        attribution = 'direct'
    elif campaign_id:
        attribution = 'campaign'

    resp = {'status': 'ok', 'as_of': _now_iso(), 'filters': filters, 'data': {'totals': totals, 'efficiency': efficiency, 'by_channel': by_channel, 'attribution': attribution}}
    if debug:
        resp['data']['diagnostics'] = diagnostics
    return resp


@router.get("/rollups/funnel")
def funnel_rollup(fy: Optional[int] = Query(None), qtr: Optional[int] = Query(None), scope_type: Optional[str] = Query(None), scope_value: Optional[str] = Query(None), station_rsid: Optional[str] = Query(None)):
    conn = connect()
    cur = conn.cursor()
    filters = _filters_dict(fy, qtr, scope_type, scope_value, station_rsid)
    # stages ordered by funnel_stages.rank
    stages = []
    try:
        cur.execute('SELECT id, name, rank FROM funnel_stages ORDER BY rank')
        stages = [{'id': r[0], 'name': r[1], 'rank': r[2]} for r in cur.fetchall()]
    except Exception:
        pass

    # counts per stage
    stage_counts = {}
    try:
        cur.execute('SELECT from_stage, COUNT(1) FROM funnel_transitions GROUP BY from_stage')
        for r in cur.fetchall():
            stage_counts[r[0]] = r[1]
    except Exception:
        pass

    # conversion rates and dropoffs (simple adjacent calculations)
    ordered = [s['id'] for s in stages]
    conversions = []
    dropoffs = []
    for i in range(len(ordered)-1):
        cur_stage = ordered[i]
        next_stage = ordered[i+1]
        cur_count = stage_counts.get(cur_stage, 0)
        next_count = stage_counts.get(next_stage, 0)
        rate = (next_count / cur_count) if cur_count and cur_count > 0 else None
        conversions.append({'from': cur_stage, 'to': next_stage, 'rate': rate, 'from_count': cur_count, 'to_count': next_count})
        drop = cur_count - next_count
        dropoffs.append({'from': cur_stage, 'to': next_stage, 'dropoff': drop})

    # average time-in-stage not available without timestamps per-lead
    avg_time_in_stage = None

    # simple bottleneck flags: dropoff > 0.5 of from_count or absence
    bottlenecks = []
    for d in dropoffs:
        from_c = d.get('dropoff', 0) + (stage_counts.get(d['to'], 0) or 0)
        flag = False
        if d['dropoff'] and from_c and (d['dropoff'] / from_c) > 0.5:
            flag = True
        bottlenecks.append({'from': d['from'], 'to': d['to'], 'dropoff': d['dropoff'], 'flag': flag})

    return {'status': 'ok', 'as_of': _now_iso(), 'filters': filters, 'data': {'stages': stages, 'conversions': conversions, 'dropoffs': dropoffs, 'avg_time_in_stage': avg_time_in_stage, 'bottlenecks': bottlenecks}}


@router.get("/rollups/command")
def command_rollup(fy: Optional[int] = Query(None), qtr: Optional[int] = Query(None), scope_type: Optional[str] = Query(None), scope_value: Optional[str] = Query(None)):
    conn = connect()
    cur = conn.cursor()
    filters = _filters_dict(fy, qtr, scope_type, scope_value)
    priorities = []
    try:
        cur.execute('SELECT id, title, description FROM command_priorities ORDER BY rank')
        for r in cur.fetchall():
            priorities.append({'id': r[0], 'title': r[1], 'description': r[2]})
    except Exception:
        pass

    # LOE statuses: best-effort mapping using loe_metric_map table if present
    loe_statuses = []
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='loe_metric_map'")
        if not cur.fetchone():
            # create lightweight mapping table if missing (idempotent)
            cur.executescript('''
            CREATE TABLE IF NOT EXISTS loe_metric_map (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                loe_id TEXT,
                metric_type TEXT,
                threshold REAL,
                comparator TEXT,
                created_at TEXT
            );
            ''')
        # attempt to produce statuses (no-op / empty list if no mappings)
        cur.execute('SELECT loe_id, metric_type, threshold, comparator FROM loe_metric_map')
        for r in cur.fetchall():
            loe_statuses.append({'loe_id': r[0], 'metric_type': r[1], 'threshold': r[2], 'comparator': r[3], 'status': 'AT_RISK', 'rationale': 'mapping exists; evaluation deferred'})
    except Exception:
        pass

    return {'status': 'ok', 'as_of': _now_iso(), 'filters': filters, 'data': {'command_priorities': priorities, 'loe_statuses': loe_statuses}}
