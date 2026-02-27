from fastapi import APIRouter, Depends
from services.api.app.db import get_db_conn
from services.api.app.routers.rbac import get_current_user
from services.api.app import ingest_registry
from datetime import datetime
import uuid

router = APIRouter(prefix="/v1")


@router.post("/ingestLead")
async def ingest_lead(payload: dict, user: dict = Depends(get_current_user)):
    conn = get_db_conn()
    cur = conn.cursor()
    lid = payload.get("lead_id") or ("lead_" + uuid.uuid4().hex[:10])
    cur.execute(
        "INSERT OR REPLACE INTO leads(lead_id,first_name,last_name,email,phone,source,age,education_level,cbsa_code,campaign_source,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            lid,
            payload.get("first_name"),
            payload.get("last_name"),
            payload.get("email"),
            payload.get("phone"),
            payload.get("source"),
            payload.get("age"),
            payload.get("education_level"),
            payload.get("cbsa_code"),
            payload.get("campaign_source"),
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "lead_id": lid}


@router.post("/scoreLead")
async def score_lead(payload: dict):
    """Lightweight scoring endpoint used by the lightweight frontend demo.

    Returns a mocked score and recommendation derived from simple heuristics.
    """
    # Basic heuristics for demo purposes
    age = int(payload.get('age') or 30)
    education = (payload.get('education_level') or '').lower()
    campaign = payload.get('campaign_source') or ''
    base = 50
    # age influence
    if age < 25:
        base += 10
    elif age >= 45:
        base -= 5
    # education
    if 'masters' in education or 'phd' in education:
        base += 10
    elif 'high' in education:
        base -= 5
    # campaign boost
    if campaign:
        base += 5
    score = max(0, min(100, base))
    prob = round(score / 100.0, 3)
    rec = 'Recommend contact' if score >= 60 else 'Monitor and nurture'
    return {
        'lead_id': payload.get('lead_id') or f"lead-{int(datetime.utcnow().timestamp())}",
        'score': score,
        'predicted_probability': prob,
        'recommendation': rec,
    }


# --- ROI contract endpoints (minimal implementations)
@router.get('/roi/kpis')
def roi_kpis(unit_rsid: str = None, echelon: str = None, period_from: str = None, period_to: str = None, conn=None):
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        # aggregate from funnel_event where available, fallback to roi_result
        q = 'SELECT SUM(spend) as spend, SUM(impressions) as impressions, SUM(engagements) as prospect_engagements, SUM(leads) as adj_leads, SUM(appts_made) as appt_made, SUM(appts_conducted) as appt_conducted, SUM(contracts) as contracts FROM funnel_event WHERE 1=1'
        params = []
        if unit_rsid:
            q += ' AND unit_rsid = ?'
            params.append(unit_rsid)
        if period_from:
            q += ' AND timestamp >= ?'
            params.append(period_from)
        if period_to:
            q += ' AND timestamp <= ?'
            params.append(period_to)
        try:
            cur.execute(q, tuple(params))
            r = cur.fetchone()
            spend = float(r['spend'] or 0)
            impressions = int(r['impressions'] or 0)
            engagements = int(r['prospect_engagements'] or 0)
            adj_leads = int(r['adj_leads'] or 0)
            appt_made = int(r['appt_made'] or 0)
            appt_conducted = int(r['appt_conducted'] or 0)
            contracts = int(r['contracts'] or 0)
        except Exception:
            # fallback to roi_result
            cur.execute('SELECT SUM(spend) as spend, SUM(impressions) as impressions FROM roi_result WHERE 1=1')
            rr = cur.fetchone()
            spend = float(rr['spend'] or 0)
            impressions = int(rr['impressions'] or 0)
            engagements = adj_leads = appt_made = appt_conducted = contracts = 0

        rates = {
            'lead_to_appt': (appt_made / adj_leads) if adj_leads else None,
            'appt_to_conduct': (appt_conducted / appt_made) if appt_made else None,
            'conduct_to_contract': (contracts / appt_conducted) if appt_conducted else None,
            'lead_to_contract': (contracts / adj_leads) if adj_leads else None,
        }
        unit_costs = {
            'cpm': (spend / (impressions/1000)) if impressions else None,
            'cpe': (spend / engagements) if engagements else None,
            'cpl': (spend / adj_leads) if adj_leads else None,
            'cost_per_contract': (spend / contracts) if contracts else None,
        }

        return {
            'unit': {'unit_rsid': unit_rsid or 'unknown', 'echelon': echelon or None, 'name': None},
            'period': {'from': period_from, 'to': period_to},
            'spend': {'committed': spend, 'actual': spend, 'currency': 'USD'},
            'volume': {
                'impressions': impressions,
                'prospect_engagements': engagements,
                'adj_leads': adj_leads,
                'appt_made': appt_made,
                'appt_conducted': appt_conducted,
                'contracts': contracts
            },
            'rates': rates,
            'unit_costs': unit_costs,
            'roi': {'method': 'BENCHMARK_INDEX', 'roi_score': None, 'notes': ''},
            'data_quality': {'completeness': 1.0, 'missing_fields': [], 'last_ingested_at': None}
        }
    finally:
        try:
            conn.close()
        except Exception:
            pass


# --- Importer registry API
@router.get('/importers')
def list_importers():
    """Return the deterministic importer registry used by the ingest pipeline."""
    return {'importers': ingest_registry.list_importers()}


@router.get('/importers/{importer_id}')
def get_importer(importer_id: str):
    spec = ingest_registry.get_importer(importer_id)
    if not spec:
        return {'error': 'not_found'}, 404
    return {'importer': spec}


@router.get('/roi/funnel')
def roi_funnel(unit_rsid: str = None, period_from: str = None, period_to: str = None):
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        q = 'SELECT objective, channel, SUM(spend) as spend_actual, SUM(impressions) as impressions, SUM(engagements) as prospect_engagements, SUM(leads) as adj_leads, SUM(appts_made) as appt_made, SUM(appts_conducted) as appt_conducted, SUM(contracts) as contracts FROM funnel_event WHERE 1=1'
        params = []
        if unit_rsid:
            q += ' AND unit_rsid = ?'
            params.append(unit_rsid)
        if period_from:
            q += ' AND timestamp >= ?'
            params.append(period_from)
        if period_to:
            q += ' AND timestamp <= ?'
            params.append(period_to)
        q += ' GROUP BY objective, channel'
        cur.execute(q, tuple(params))
        rows = []
        for r in cur.fetchall():
            rdict = dict(r)
            adj_leads = int(rdict.get('adj_leads') or 0)
            appt_made = int(rdict.get('appt_made') or 0)
            appt_conducted = int(rdict.get('appt_conducted') or 0)
            contracts = int(rdict.get('contracts') or 0)
            rates = {
                'lead_to_appt': (appt_made / adj_leads) if adj_leads else None,
                'appt_to_conduct': (appt_conducted / appt_made) if appt_made else None,
                'conduct_to_contract': (contracts / appt_conducted) if appt_conducted else None,
                'lead_to_contract': (contracts / adj_leads) if adj_leads else None,
            }
            unit_costs = {
                'cpm': None,
                'cpe': None,
                'cpl': (float(rdict.get('spend_actual',0)) / adj_leads) if adj_leads else None,
                'cpa': (float(rdict.get('spend_actual',0)) / appt_made) if appt_made else None,
                'cost_per_contract': (float(rdict.get('spend_actual',0)) / contracts) if contracts else None,
            }
            rows.append({
                'objective': rdict.get('objective'),
                'channel': rdict.get('channel'),
                'spend_actual': float(rdict.get('spend_actual') or 0),
                'impressions': int(rdict.get('impressions') or 0),
                'prospect_engagements': int(rdict.get('prospect_engagements') or 0),
                'adj_leads': adj_leads,
                'appt_made': appt_made,
                'appt_conducted': appt_conducted,
                'contracts': contracts,
                'rates': rates,
                'unit_costs': unit_costs,
                'benchmark_band': {}
            })
        totals = {'spend_actual': sum([r['spend_actual'] for r in rows]), 'adj_leads': sum([r['adj_leads'] for r in rows]), 'contracts': sum([r['contracts'] for r in rows])}
        return {'unit': {'unit_rsid': unit_rsid}, 'period': {'from': period_from, 'to': period_to}, 'rows': rows, 'totals': totals}
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.get('/roi/breakdown')
def roi_breakdown(by: str = 'UNIT_CHILD', unit_rsid: str = None, period_from: str = None, period_to: str = None):
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        if by == 'UNIT_CHILD' and unit_rsid:
            # simple breakdown: aggregate by child unit_rsid in funnel_event
            q = 'SELECT unit_rsid_child as unit_rsid, SUM(spend) as spend_actual, SUM(leads) as adj_leads, SUM(contracts) as contracts FROM funnel_event WHERE parent_unit_rsid = ?'
            params = [unit_rsid]
            if period_from:
                q += ' AND timestamp >= ?'
                params.append(period_from)
            if period_to:
                q += ' AND timestamp <= ?'
                params.append(period_to)
            q += ' GROUP BY unit_rsid_child'
            cur.execute(q, tuple(params))
            rows = []
            for r in cur.fetchall():
                rdict = dict(r)
                adj_leads = int(rdict.get('adj_leads') or 0)
                contracts = int(rdict.get('contracts') or 0)
                cpl = (float(rdict.get('spend_actual',0)) / adj_leads) if adj_leads else None
                rows.append({'unit_rsid': rdict.get('unit_rsid'), 'name': None, 'spend_actual': float(rdict.get('spend_actual') or 0), 'adj_leads': adj_leads, 'contracts': contracts, 'cpl': cpl, 'lead_to_contract': (contracts / adj_leads) if adj_leads else None})
            return {'by': by, 'rows': rows}
        # fallback: empty
        return {'by': by, 'rows': []}
    finally:
        try:
            conn.close()
        except Exception:
            pass
