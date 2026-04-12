"""Simple rule-based COA engine that creates 3 COAs per run based on
available evidence: fusion_recommendations, mission_allocation_recommendations,
school_targeting_scores, and market_health_scores.
"""
from typing import List, Dict, Any, Optional
import uuid
import json
from datetime import datetime
from services.api.app import db as dbmod


def _now_iso():
    return datetime.utcnow().isoformat()


def _fetch_top_fusion(conn, unit_rsid: str, limit: int = 3):
    cur = conn.cursor()
    cur.execute(
        'SELECT fusion_run_id, school_id, market_key, zip5, fusion_score, evidence_json FROM fusion_recommendations WHERE unit_rsid=? ORDER BY fusion_score DESC LIMIT ?',
        (unit_rsid, limit),
    )
    rows = cur.fetchall()
    res = []
    for r in rows:
        res.append({
            'fusion_run_id': r['fusion_run_id'],
            'school_id': r['school_id'],
            'market_key': r['market_key'],
            'zip5': r['zip5'],
            'fusion_score': r['fusion_score'],
            'evidence_json': json.loads(r['evidence_json']) if r['evidence_json'] else None,
        })
    return res


def _fetch_best_fusion(conn, unit_rsid: str):
    cur = conn.cursor()
    cur.execute(
        'SELECT fusion_run_id, school_id, market_key, zip5, fusion_score, evidence_json FROM fusion_recommendations WHERE unit_rsid=? ORDER BY fusion_score DESC LIMIT 1',
        (unit_rsid,)
    )
    r = cur.fetchone()
    if not r:
        return None
    return {
        'fusion_run_id': r['fusion_run_id'],
        'school_id': r['school_id'],
        'market_key': r['market_key'],
        'zip5': r['zip5'],
        'fusion_score': r['fusion_score'],
        'evidence_json': json.loads(r['evidence_json']) if r['evidence_json'] else None,
    }


def _fetch_mission_allocations(conn, run_id: Optional[str], unit_rsid: str):
    cur = conn.cursor()
    if run_id:
        cur.execute('SELECT company_id, recommended_mission, rationale, confidence FROM mission_allocation_recommendations WHERE run_id=?', (run_id,))
    else:
        cur.execute('SELECT company_id, recommended_mission, rationale, confidence FROM mission_allocation_recommendations WHERE run_id IN (SELECT run_id FROM mission_allocation_runs WHERE unit_rsid=? ORDER BY created_at DESC LIMIT 1)', (unit_rsid,))
    rows = cur.fetchall()
    return [dict(r) for r in rows]


def _evidence_summary(top_fusions: List[Dict[str, Any]], mal_recs: List[Dict[str, Any]]):
    ev = []
    for f in top_fusions:
        ev.append({'type': 'fusion', 'score': f.get('fusion_score'), 'payload': f})
    for m in mal_recs:
        ev.append({'type': 'mission_alloc', 'payload': m})
    return ev


def _derive_primary(unit_rsid: str, fusion_row: Optional[Dict[str, Any]], mal_recs: List[Dict[str, Any]], lead_line: Optional[Dict[str, Any]] = None):
    # Build a command-level PRIMARY COA tied to lead-line variance and fusion score
    target = fusion_row or {}
    school_id = target.get('school_id')
    fusion_score = target.get('fusion_score', 0)

    variance = lead_line.get('variance', 0) if lead_line else 0
    status = lead_line.get('status') if lead_line else None

    contracts_to_recover = abs(int(round(variance)))

    # Resource logic
    if contracts_to_recover >= 3:
        recruiters = 2
    elif contracts_to_recover == 2:
        recruiters = 2
    else:
        recruiters = 1

    # Timeline
    timeline_days = 14 if contracts_to_recover <= 3 else 30

    urgency_tag = 'URGENT' if status == 'BEHIND' else 'PRIORITY'

    title = f"{urgency_tag}: Recover {contracts_to_recover} Contracts via {school_id or 'target'}"

    summary = (
        f"{urgency_tag}: Unit is {status} (variance={variance}). "
        f"Execute targeted operations at {school_id or 'target'} to recover {contracts_to_recover} contracts."
    )

    recommended_actions = {
        "task_organization": {
            "recruiters_assigned": recruiters,
            "unit": unit_rsid
        },
        "operations": [
            f"Conduct 5 engagements at {school_id or 'target'} within {timeline_days} days",
            f"Execute daily follow-ups for all {school_id or 'target'} leads",
            "Prioritize processing and contracting pipeline"
        ],
        "timeline_days": timeline_days,
        "objective": {
            "contracts_to_recover": contracts_to_recover,
            "target_completion_window_days": 30
        }
    }

    objective = {
        "contracts_to_recover": contracts_to_recover,
        "target_completion_window_days": 30
    }

    expected_effect = (
        f"+{contracts_to_recover} contracts; return to lead-line pacing; "
        f"increased penetration at {school_id or 'target'}"
    )

    risk = 'MEDIUM'

    assumptions = {
        "school_access": True,
        "lead_quality": "HIGH" if fusion_score >= 0.8 else "MODERATE"
    }

    doctrine_refs = ["UM 3-0", "UR 27-4", "UR 601-210"]

    return {
        'coa_type': 'PRIMARY',
        'coa_title': title,
        'coa_summary': summary,
        'recommended_actions_json': recommended_actions,
        'objective_json': objective,
        'expected_benefit': expected_effect,
        'risk_level': risk,
        'assumptions_json': assumptions,
        'doctrine_refs_json': doctrine_refs,
    }


def _derive_alternate(unit_rsid: str, top_fusions: List[Dict[str, Any]], mal_recs: List[Dict[str, Any]], lead_line: Optional[Dict[str, Any]] = None):
    # Alternate COA: lower-risk, slower recovery (contrast to PRIMARY)
    target = top_fusions[1] if len(top_fusions) > 1 else (top_fusions[0] if top_fusions else {})
    school_id = target.get('school_id') if isinstance(target, dict) else None
    fusion_score = target.get('fusion_score', 0) if isinstance(target, dict) else 0

    # derive primary params from lead_line and fusion_score
    try:
        primary_recruiters = max(1, abs(int(round((lead_line.get('variance', 0))))) and (2 if abs(int(round(lead_line.get('variance', 0)))) >= 3 else (2 if abs(int(round(lead_line.get('variance', 0)))) == 2 else 1)))
    except Exception:
        primary_recruiters = 1
    # alternate reduces recruiters by 1 (min 1)
    recruiters = max(1, primary_recruiters - 1)

    # base timeline from primary: compute contracts_to_recover similarly
    contracts_to_recover = abs(int(round(lead_line.get('variance', 0)))) if lead_line else 0
    primary_timeline = 14 if contracts_to_recover <= 3 else 30
    timeline_days = primary_timeline + 14

    engagements = 3

    title = f"STABILIZE: Stabilize pipeline at {school_id or 'target'} over {timeline_days} days"
    summary = f"Stabilize pipeline at {school_id or 'target'} with lower tempo and deliberate engagement to recover {contracts_to_recover} contracts over {timeline_days} days."

    recommended_actions = {
        "task_organization": {"recruiters_assigned": recruiters, "unit": unit_rsid},
        "operations": [
            f"Conduct {engagements} engagements at {school_id or 'target'} within {timeline_days} days",
            f"Focus on quality conversations and conversion optimization",
            "Maintain consistent follow-ups with measured cadence"
        ],
        "timeline_days": timeline_days,
        "objective": {"contracts_to_recover": contracts_to_recover, "target_completion_window_days": timeline_days}
    }

    expected_benefit = "Steady recovery with reduced operational risk; improved lead quality and conversion over time."
    risk = 'LOW'
    assumptions = {'school_access': True, 'lead_quality': 'MODERATE' if fusion_score < 0.8 else 'HIGH'}
    doctrine = ['UM 3-0', 'UR 27-4']

    return {
        'coa_type': 'ALTERNATE',
        'coa_title': title,
        'coa_summary': summary,
        'recommended_actions_json': recommended_actions,
        'objective_json': recommended_actions.get('objective'),
        'expected_benefit': expected_benefit,
        'risk_level': risk,
        'assumptions_json': assumptions,
        'doctrine_refs_json': doctrine,
    }


def _derive_aggressive(unit_rsid: str, top_fusions: List[Dict[str, Any]], mal_recs: List[Dict[str, Any]], lead_line: Optional[Dict[str, Any]] = None):
    # Aggressive COA: higher tempo, higher resource demand
    target = top_fusions[0] if top_fusions else {}
    school_id = target.get('school_id')
    fusion_score = target.get('fusion_score', 0)

    contracts_to_recover = abs(int(round(lead_line.get('variance', 0)))) if lead_line else 0
    # derive primary timeline
    primary_timeline = 14 if contracts_to_recover <= 3 else 30
    # aggressive increases recruiters by 1 and shortens timeline
    try:
        primary_recruiters = 2 if contracts_to_recover >= 3 else (2 if contracts_to_recover == 2 else 1)
    except Exception:
        primary_recruiters = 1
    recruiters = primary_recruiters + 1
    timeline_days = max(7, primary_timeline - 14)
    engagements = 7

    title = f"SURGE: Rapidly recover {contracts_to_recover} Contracts via {school_id or 'target'}"
    summary = f"Surge operations at {school_id or 'target'} to rapidly recover {contracts_to_recover} contracts within {timeline_days} days; higher resource demand and risk."

    recommended_actions = {
        "task_organization": {"recruiters_assigned": recruiters, "unit": unit_rsid},
        "operations": [
            f"Conduct {engagements} high-intensity engagements at {school_id or 'target'} within {timeline_days} days",
            f"Execute twice-daily follow-ups and rapid processing for target leads",
            "Deploy incentives and surge events to accelerate conversions"
        ],
        "timeline_days": timeline_days,
        "objective": {"contracts_to_recover": contracts_to_recover, "target_completion_window_days": timeline_days}
    }

    expected_benefit = "Rapid recovery potential; high conversion if lead quality holds."
    risk = 'HIGH'
    assumptions = {'school_access': True, 'lead_quality': 'HIGH' if fusion_score >= 0.8 else 'MODERATE'}
    doctrine = ['UM 3-0', 'Doctrinal Guidance 5.3']

    return {
        'coa_type': 'AGGRESSIVE',
        'coa_title': title,
        'coa_summary': summary,
        'recommended_actions_json': recommended_actions,
        'objective_json': recommended_actions.get('objective'),
        'expected_benefit': expected_benefit,
        'risk_level': risk,
        'assumptions_json': assumptions,
        'doctrine_refs_json': doctrine,
    }


def run_coa_generation(unit_rsid: str, fusion_run_id: Optional[str] = None, mission_run_id: Optional[str] = None) -> Dict[str, Any]:
    """Generate COAs for a unit and persist them into `coa_recommendations`.

    Returns a dict with `coa_run_id` and `created` count.
    """
    conn = dbmod.connect()
    try:
        top_fusions = _fetch_top_fusion(conn, unit_rsid, limit=3)
        mal_recs = _fetch_mission_allocations(conn, mission_run_id, unit_rsid)
        # compute lead-line for unit to inform COA derivation
        try:
            from . import lead_line as lead_line_mod
            # determine annual mission from latest mission_allocation_runs
            cur = conn.cursor()
            cur.execute('SELECT mission_total FROM mission_allocation_runs WHERE unit_rsid=? ORDER BY created_at DESC LIMIT 1', (unit_rsid,))
            row = cur.fetchone()
            annual = int(row['mission_total']) if row and row['mission_total'] is not None else 0
            # compute actual YTD from fact_lead_journey
            from datetime import date
            start_of_year = date(date.today().year, 1, 1).isoformat()
            if unit_rsid:
                cur.execute('SELECT COUNT(*) as cnt FROM fact_lead_journey WHERE unit_rsid=? AND contract_flag=1 AND created_dt>=?', (unit_rsid, start_of_year))
            else:
                cur.execute('SELECT COUNT(*) as cnt FROM fact_lead_journey WHERE contract_flag=1 AND created_dt>=?', (start_of_year,))
            cnt = cur.fetchone()
            actual = int(cnt['cnt']) if cnt and cnt['cnt'] is not None else 0
            lead_line = lead_line_mod.calculate_lead_line(actual, annual)
        except Exception:
            lead_line = None
        evid = _evidence_summary(top_fusions, mal_recs)

        coa_run_id = f"coa_{uuid.uuid4().hex[:8]}"
        now = _now_iso()
        coas = []
        # pick the single best fusion row (if available) and pass it to primary builder
        best_fusion = _fetch_best_fusion(conn, unit_rsid)
        coas.append(_derive_primary(unit_rsid, best_fusion, mal_recs, lead_line))
        coas.append(_derive_alternate(unit_rsid, top_fusions, mal_recs, lead_line))
        coas.append(_derive_aggressive(unit_rsid, top_fusions, mal_recs, lead_line))

        cur = conn.cursor()
        created = 0
        for c in coas:
            # support both new field names (expected_effect, risk, assumptions, doctrine_refs)
            expected_benefit = c.get('expected_benefit') or c.get('expected_effect')
            risk_level = c.get('risk_level') or c.get('risk')
            assumptions_json = c.get('assumptions_json') if c.get('assumptions_json') is not None else c.get('assumptions')
            doctrine_refs_json = c.get('doctrine_refs_json') if c.get('doctrine_refs_json') is not None else c.get('doctrine_refs')
            cur.execute('''INSERT INTO coa_recommendations (coa_run_id, unit_rsid, coa_type, coa_title, coa_summary, recommended_actions_json, expected_benefit, risk_level, assumptions_json, doctrine_refs_json, supporting_evidence_json, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', (
                coa_run_id,
                unit_rsid,
                c['coa_type'],
                c['coa_title'],
                c.get('coa_summary'),
                json.dumps(c.get('recommended_actions_json')),
                expected_benefit,
                risk_level,
                json.dumps(assumptions_json) if assumptions_json is not None else None,
                json.dumps(doctrine_refs_json) if doctrine_refs_json is not None else None,
                json.dumps(evid),
                now
            ))
            created += 1
        conn.commit()
        return {'coa_run_id': coa_run_id, 'created': created}
    finally:
        try:
            conn.close()
        except Exception:
            pass


def fetch_latest_for_unit(unit_rsid: str, limit: int = 10):
    conn = dbmod.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id, coa_run_id, unit_rsid, coa_type, coa_title, coa_summary, recommended_actions_json, expected_benefit, risk_level, assumptions_json, doctrine_refs_json, supporting_evidence_json, created_at FROM coa_recommendations WHERE unit_rsid=? ORDER BY created_at DESC LIMIT ?', (unit_rsid, limit))
        rows = cur.fetchall()
        out = []
        for r in rows:
            rec_actions = json.loads(r['recommended_actions_json']) if r['recommended_actions_json'] else None
            objective = None
            try:
                if isinstance(rec_actions, dict):
                    objective = rec_actions.get('objective')
            except Exception:
                objective = None
            out.append({
                'id': r['id'],
                'coa_run_id': r['coa_run_id'],
                'unit_rsid': r['unit_rsid'],
                'coa_type': r['coa_type'],
                'coa_title': r['coa_title'],
                'coa_summary': r['coa_summary'],
                'recommended_actions_json': rec_actions,
                'objective_json': objective,
                'expected_benefit': r['expected_benefit'],
                'expected_effect': r['expected_benefit'],
                'risk_level': r['risk_level'],
                'risk': r['risk_level'],
                'assumptions_json': json.loads(r['assumptions_json']) if r['assumptions_json'] else None,
                'assumptions': json.loads(r['assumptions_json']) if r['assumptions_json'] else None,
                'doctrine_refs_json': json.loads(r['doctrine_refs_json']) if r['doctrine_refs_json'] else None,
                'doctrine_refs': json.loads(r['doctrine_refs_json']) if r['doctrine_refs_json'] else None,
                'supporting_evidence_json': json.loads(r['supporting_evidence_json']) if r['supporting_evidence_json'] else None,
                'created_at': r['created_at']
            })
        return out
    finally:
        try:
            conn.close()
        except Exception:
            pass
