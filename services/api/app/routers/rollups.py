from fastapi import APIRouter, Request
from typing import Dict, Any
from ..db import connect
from ..utils.rollup_utils import apply_common_filters, build_empty_rollup_contract, safe_table_exists
from datetime import datetime

router = APIRouter()


def _now_iso():
    return datetime.utcnow().isoformat() + 'Z'


@router.get('/rollups/events/dashboard')
def events_dashboard(request: Request) -> Dict[str, Any]:
    params = dict(request.query_params)
    filters = apply_common_filters(params)
    kpi_keys = ['total_events', 'total_cost', 'total_outcomes', 'cost_per_outcome', 'avg_event_cost']
    breakdown_keys = ['by_event_type', 'by_funding_line', 'by_project']
    trend_keys = ['outcomes_over_time', 'spend_over_time']
    conn = connect()
    try:
        if not safe_table_exists(conn, 'event'):
            return build_empty_rollup_contract(filters, kpi_keys, breakdown_keys, trend_keys)
        cur = conn.cursor()
        # totals
        try:
            cur.execute('SELECT COUNT(1) as c FROM event')
            r = cur.fetchone(); total_events = int(r['c'] or 0)
        except Exception:
            total_events = 0
        try:
            cur.execute('SELECT SUM(COALESCE(amount,0)) as s FROM expenses')
            r = cur.fetchone(); total_cost = float(r['s'] or 0)
        except Exception:
            total_cost = 0.0
        try:
            cur.execute('SELECT SUM(COALESCE(contracts,0)) as s FROM event_metrics')
            r = cur.fetchone(); total_outcomes = float(r['s'] or 0)
        except Exception:
            total_outcomes = 0.0
        cost_per_outcome = (total_cost / total_outcomes) if total_outcomes else 0.0
        avg_event_cost = (total_cost / total_events) if total_events else 0.0

        payload = {
            'status': 'ok',
            'data_as_of': _now_iso(),
            'filters': filters,
            'kpis': {
                'total_events': total_events,
                'total_cost': round(total_cost,2),
                'total_outcomes': int(total_outcomes),
                'cost_per_outcome': round(cost_per_outcome,2),
                'avg_event_cost': round(avg_event_cost,2)
            },
            'breakdowns': {
                'by_event_type': [],
                'by_funding_line': [],
                'by_project': []
            },
            'trends': {
                'outcomes_over_time': [],
                'spend_over_time': []
            },
            'missing_data': []
        }
        return payload
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.get('/rollups/marketing/dashboard')
def marketing_dashboard(request: Request) -> Dict[str, Any]:
    params = dict(request.query_params)
    filters = apply_common_filters(params)
    kpi_keys = ['total_spend', 'total_impressions', 'total_engagements', 'total_activations', 'cost_per_activation']
    breakdown_keys = ['by_channel', 'by_event']
    trend_keys = ['spend_over_time', 'activation_over_time']
    conn = connect()
    try:
        if not safe_table_exists(conn, 'marketing_activities'):
            return build_empty_rollup_contract(filters, kpi_keys, breakdown_keys, trend_keys)
        cur = conn.cursor()
        try:
            cur.execute('SELECT SUM(COALESCE(cost,0)) as s FROM marketing_activities')
            r = cur.fetchone(); total_spend = float(r['s'] or 0)
        except Exception:
            total_spend = 0.0
        try:
            cur.execute('SELECT SUM(COALESCE(impressions,0)) as s FROM marketing_activities')
            r = cur.fetchone(); total_impressions = int(r['s'] or 0)
        except Exception:
            total_impressions = 0
        try:
            cur.execute('SELECT SUM(COALESCE(engagement_count,0)) as s FROM marketing_activities')
            r = cur.fetchone(); total_engagements = int(r['s'] or 0)
        except Exception:
            total_engagements = 0
        try:
            cur.execute('SELECT SUM(COALESCE(activation_conversions,0)) as s FROM marketing_activities')
            r = cur.fetchone(); total_activations = int(r['s'] or 0)
        except Exception:
            total_activations = 0
        cost_per_activation = (total_spend / total_activations) if total_activations else 0.0

        payload = {
            'status': 'ok',
            'data_as_of': _now_iso(),
            'filters': filters,
            'kpis': {
                'total_spend': round(total_spend,2),
                'total_impressions': total_impressions,
                'total_engagements': total_engagements,
                'total_activations': total_activations,
                'cost_per_activation': round(cost_per_activation,2)
            },
            'breakdowns': {'by_channel': [], 'by_event': []},
            'trends': {'spend_over_time': [], 'activation_over_time': []},
            'missing_data': []
        }
        return payload
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.get('/rollups/funnel/dashboard')
def funnel_dashboard(request: Request) -> Dict[str, Any]:
    params = dict(request.query_params)
    filters = apply_common_filters(params)
    kpi_keys = ['total_leads', 'total_appointments', 'total_contracts', 'conversion_rate', 'flash_to_bang_days']
    breakdown_keys = ['by_stage', 'bottlenecks']
    trend_keys = ['conversion_trend']
    conn = connect()
    try:
        # rely on 'leads' and 'event_metrics' tables if present
        if not safe_table_exists(conn, 'leads') and not safe_table_exists(conn, 'event_metrics'):
            return build_empty_rollup_contract(filters, kpi_keys, breakdown_keys, trend_keys)
        cur = conn.cursor()
        try:
            cur.execute('SELECT COUNT(1) as c FROM leads')
            r = cur.fetchone(); total_leads = int(r['c'] or 0)
        except Exception:
            total_leads = 0
        try:
            cur.execute('SELECT SUM(COALESCE(appts_made,0)) as s FROM event_metrics')
            r = cur.fetchone(); total_appointments = int(r['s'] or 0)
        except Exception:
            total_appointments = 0
        try:
            cur.execute('SELECT SUM(COALESCE(contracts,0)) as s FROM event_metrics')
            r = cur.fetchone(); total_contracts = int(r['s'] or 0)
        except Exception:
            total_contracts = 0
        conversion_rate = (total_contracts / total_leads) if total_leads else 0.0
        payload = {
            'status': 'ok',
            'data_as_of': _now_iso(),
            'filters': filters,
            'kpis': {
                'total_leads': total_leads,
                'total_appointments': total_appointments,
                'total_contracts': total_contracts,
                'conversion_rate': round(conversion_rate,4),
                'flash_to_bang_days': None
            },
            'breakdowns': {'by_stage': [], 'bottlenecks': []},
            'trends': {'conversion_trend': []},
            'missing_data': []
        }
        return payload
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.get('/rollups/command/mission-assessment')
def command_mission_assessment(request: Request) -> Dict[str, Any]:
    # Build priorities by pulling from existing rollups
    params = dict(request.query_params)
    filters = apply_common_filters(params)
    # Reuse other endpoints internally (call functions which read request.query_params)
    ev = events_dashboard(request)
    fu = funnel_dashboard(request)
    mk = marketing_dashboard(request)
    priorities = []
    risk_flags = []
    missing = []
    # If upstream rollups are empty, indicate insufficient_data
    if (not ev.get('kpis') or ev.get('kpis') == {}) and (not fu.get('kpis') or fu.get('kpis') == {}) and (not mk.get('kpis') or mk.get('kpis') == {}):
        missing.append('insufficient_rollup_data')
        return {'status': 'ok', 'data_as_of': None, 'priorities': [], 'risk_flags': [], 'missing_data': missing}
    # Simple heuristic to populate priorities from funnel and events
    try:
        total_events = ev.get('kpis', {}).get('total_events', 0)
        total_leads = fu.get('kpis', {}).get('total_leads', 0)
        priorities.append({'id': 'p1', 'title': 'Event Reach', 'loe': None, 'standard': None, 'actual': total_events, 'status': 'met' if total_events>0 else 'insufficient_data'})
        priorities.append({'id': 'p2', 'title': 'Lead Flow', 'loe': None, 'standard': None, 'actual': total_leads, 'status': 'met' if total_leads>0 else 'insufficient_data'})
    except Exception:
        pass
    return {'status': 'ok', 'data_as_of': _now_iso(), 'priorities': priorities, 'risk_flags': risk_flags, 'missing_data': missing}


# --- Top-level aliases to match requested API contract paths ---
@router.get('/events/dashboard')
def events_dashboard_alias(request: Request):
    return events_dashboard(request)


@router.get('/marketing/dashboard')
def marketing_dashboard_alias(request: Request):
    return marketing_dashboard(request)


@router.get('/funnel/dashboard')
def funnel_dashboard_alias(request: Request):
    return funnel_dashboard(request)


@router.get('/command/mission-assessment')
def command_mission_assessment_alias(request: Request):
    return command_mission_assessment(request)

