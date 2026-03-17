"""AI LMS helpers: generate short explanations, doctrine mappings, and persistence helpers.
This module provides minimal, deterministic logic to create a concise explanation
and to persist/get annotations, decisions, and outcomes.
"""
from typing import Optional, List, Dict, Any
import json
from datetime import datetime


DOCTRINE_REFERENCES = {
    "UM 3-0": "Unified Maneuver doctrine overview (UM 3-0)",
    "UM 3-29": "Urban operations and related doctrine",
    "UM 3-30": "Small unit maneuver reference",
    "UM 3-31": "Force employment guidance",
    "UM 3-32": "Operational planning",
    "UR 10-1": "Recruiting guidance UR 10-1",
    "UR 27-4": "Outreach and engagement UR 27-4",
    "UR 350-1": "Training policy UR 350-1",
    "UR 350-13": "Advanced training UR 350-13",
    "UR 601-106": "Personnel admin UR 601-106",
    "UR 601-210": "Personnel readiness UR 601-210",
    "UR 601-73": "Recruiting procedures UR 601-73",
    "UTP 3-10.2": "Tactical employment UTP 3-10.2"
}


def _short_timestamp() -> str:
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def generate_explanation_from_recommendation(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Produce a short explanation and doctrine refs for a recommendation row.

    The implementation is intentionally conservative: it inspects available
    fields such as `recommendation_text`, `evidence_json`, `fusion_score`,
    and `unit_rsid` to produce a human-usable explanation.
    """
    # parse evidence payload when available
    evidence = None
    try:
        if rec.get('evidence_json'):
            evidence = json.loads(rec.get('evidence_json') or '{}')
    except Exception:
        evidence = None

    # helper: build 'what' and list-style 'why' items from available data
    what = rec.get('recommendation_text') or rec.get('action') or 'Suggested action'
    why: List[str] = []
    ev = evidence or {}
    # school-related reasons
    school = ev.get('school') if isinstance(ev, dict) else None
    if school and school.get('priority_score') is not None:
        why.append('School priority score supports targeting')
    if school and school.get('enrollment'):
        why.append(f"School population: {school.get('enrollment')}")
    # market-related reasons
    market = ev.get('market') if isinstance(ev, dict) else None
    if market and market.get('avg_share') is not None:
        why.append('Market share indicates opportunity')
    if market and market.get('examples'):
        why.append('Local market examples present')
    # mission-related reasons
    mission = ev.get('mission') if isinstance(ev, dict) else None
    if mission and mission.get('mission_total'):
        why.append('Mission allocation has capacity in this run')

    # evidence numeric bundle
    evidence_struct: Dict[str, Any] = {}
    score = rec.get('fusion_score') or rec.get('score')
    if score is not None:
        evidence_struct['fusion_score'] = float(score)
    if school and school.get('enrollment') is not None:
        evidence_struct['school_population'] = school.get('enrollment')
    if market and market.get('avg_share') is not None:
        evidence_struct['market_share'] = market.get('avg_share')

    # risk and expected effect
    risks: List[str] = []
    if school and school.get('confidence_score') is not None and school.get('confidence_score') < 0.5:
        risks.append('Low confidence in school data')
    if school and school.get('components') and school['components'].get('historical_production') == 0:
        risks.append('No historical production; conversion uncertain')
    if evidence_struct.get('fusion_score') and evidence_struct.get('fusion_score') < 0.2:
        risks.append('Low fusion score — prioritize cautiously')

    expected_effect = rec.get('expected_effect') or 'Increase engagement or contracts in target area'

    # confidence mapping: scale fusion_score -> [0.15, 0.95]
    try:
        f = float(score) if score is not None else 0.2
        confidence = round(min(0.95, max(0.15, f * 4.0)), 2)
    except Exception:
        confidence = 0.5

    assumptions = [
        'Market data is current',
        'School access remains unchanged'
    ]

    data_quality = 'medium'

    # determine doctrine refs via simple rule engine
    doctrine_refs = []
    rtype = (rec.get('recommendation_type') or '').lower()
    if 'school' in rtype or 'target' in rtype:
        doctrine_refs = ['UR 27-4', 'UR 601-210']
    elif 'mission' in rtype or 'allocation' in rtype:
        doctrine_refs = ['UR 350-1', 'UR 601-106']
    elif 'market' in rtype or 'analysis' in rtype:
        doctrine_refs = ['UM 3-0', 'UTP 3-10.2']
    else:
        doctrine_refs = ['UM 3-0']

    doctrine_summary = '; '.join([DOCTRINE_REFERENCES.get(k, k) for k in doctrine_refs])

    struct = {
        'what': what,
        'why': why,
        'evidence': evidence_struct,
        'risk': risks,
        'expected_effect': expected_effect,
        'confidence': confidence,
        'assumptions': assumptions,
        'data_quality': data_quality
    }

    return {
        'explanation': json.dumps(struct),
        'explanation_struct': struct,
        'doctrine_refs_json': json.dumps([{'ref': k, 'note': DOCTRINE_REFERENCES.get(k, '')} for k in doctrine_refs]),
        'doctrine_summary': doctrine_summary,
        'created_at': _short_timestamp()
    }


def persist_explanation(conn, recommendation_table: str, recommendation_id: int, rec_row: Dict[str, Any]):
    cur = conn.cursor()
    ann = generate_explanation_from_recommendation(rec_row)
    cur.execute('''INSERT INTO recommendation_explanations (recommendation_table, recommendation_id, explanation, doctrine_summary, doctrine_refs_json, created_at)
                   VALUES (?,?,?,?,?,?)''', (recommendation_table, recommendation_id, ann['explanation'], ann['doctrine_summary'], ann['doctrine_refs_json'], ann['created_at']))
    conn.commit()
    return cur.lastrowid


def fetch_recommendations_with_annotations(conn, recommendation_table: str = 'fusion_recommendations', limit: int = 100):
    cur = conn.cursor()
    # Fetch latest recommendations with optional annotations (left join)
    q = f"SELECT r.*, e.explanation, e.doctrine_summary, e.doctrine_refs_json FROM {recommendation_table} r LEFT JOIN recommendation_explanations e ON e.recommendation_table=? AND e.recommendation_id=r.id ORDER BY r.created_at DESC LIMIT ?"
    cur.execute(q, (recommendation_table, limit))
    rows = [dict(zip([c[0] for c in cur.description], row)) for row in cur.fetchall()]
    # normalize doctrine_refs_json into dict
    for r in rows:
        if r.get('doctrine_refs_json'):
            try:
                r['doctrine_refs'] = json.loads(r.get('doctrine_refs_json'))
            except Exception:
                r['doctrine_refs'] = []
        else:
            r['doctrine_refs'] = []
        # if explanation column contains JSON (structured explanation), parse it
        expl = r.get('explanation')
        if expl:
            try:
                r['explanation_struct'] = json.loads(expl)
            except Exception:
                # legacy free-text explanation — keep as-is
                r['explanation_struct'] = None
        else:
            r['explanation_struct'] = None
    return rows


def persist_user_decision(conn, recommendation_table: str, recommendation_id: int, action: str, notes: Optional[str], user_id: Optional[str]):
    cur = conn.cursor()
    cur.execute('''INSERT INTO user_decisions (recommendation_table, recommendation_id, action, notes, user_id, created_at)
                   VALUES (?,?,?,?,?,?)''', (recommendation_table, recommendation_id, action, notes, user_id, _short_timestamp()))
    conn.commit()
    return cur.lastrowid


def persist_outcome(conn, recommendation_table: str, recommendation_id: int, decision_id: Optional[int], outcome_type: str, outcome_value: str, observed_at: Optional[str], notes: Optional[str]):
    cur = conn.cursor()
    cur.execute('''INSERT INTO outcome_records (recommendation_table, recommendation_id, decision_id, outcome_type, outcome_value, observed_at, notes, created_at)
                   VALUES (?,?,?,?,?,?,?,?)''', (recommendation_table, recommendation_id, decision_id, outcome_type, outcome_value, observed_at, notes, _short_timestamp()))
    conn.commit()
    return cur.lastrowid
