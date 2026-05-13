"""AI LMS helpers: generate short explanations, doctrine mappings, and persistence helpers.
This module provides minimal, deterministic logic to create a concise explanation
and to persist/get annotations, decisions, and outcomes.
"""
from typing import Optional, List, Dict, Any
import json
import sqlite3
from datetime import datetime
from .doctrine import ENGINE as DOCTRINE_ENGINE
from .confidence import score_confidence


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

    # legacy numeric confidence (kept for compatibility) is mapped from fusion_score
    try:
        f = float(score) if score is not None else 0.2
        legacy_confidence = round(min(0.95, max(0.15, f * 4.0)), 2)
    except Exception:
        legacy_confidence = 0.5

    assumptions = [
        'Market data is current',
        'School access remains unchanged'
    ]

    data_quality = 'medium'

    # evaluate doctrine rules using the DoctrineEngine
    context = {
        'recommendation': rec,
        'market': market or {},
        'school': school or {},
        'mission': mission or {},
        'evidence': ev,
        'data_quality': data_quality
    }
    doctrine_eval = DOCTRINE_ENGINE.evaluate(context)
    doctrine_refs = doctrine_eval.get('doctrine_refs', [])
    if not doctrine_refs:
        doctrine_refs = ['UM 3-0']
    doctrine_summary = '; '.join([DOCTRINE_REFERENCES.get(k, k) for k in doctrine_refs])

    struct = {
        'what': what,
        'why': why,
        'evidence': evidence_struct,
        'risk': risks,
        'expected_effect': expected_effect,
        'confidence': legacy_confidence,
        'assumptions': assumptions,
        'data_quality': data_quality
    }

    # include triggered rules and alignment score in the explanation struct
    struct['doctrine'] = {
        'refs': doctrine_refs,
        'triggered_rules': doctrine_eval.get('triggered_rules', []),
        'rationale': doctrine_eval.get('rationale', []),
        'rule_alignment_score': doctrine_eval.get('rule_alignment_score', 0.0)
    }

    # compute explainable confidence on top of doctrine + evidence
    try:
        conf_detail = score_confidence(doctrine_eval, ev or {}, prior_fusion_score=score)
        struct['confidence_detail'] = conf_detail
        # If there's no evidence and either no doctrine triggers or only heuristic
        # triggers derived from recommendation_type, prefer legacy fusion mapping
        trig = doctrine_eval.get('triggered_rules') or []
        only_heuristic = len(trig) > 0 and all(r.get('category') == 'Heuristic' for r in trig)
        if (not ev) and (not trig or only_heuristic):
            struct['confidence'] = legacy_confidence
        else:
            # keep compatibility numeric value mapped to [0.15,0.95]
            mapped = 0.15 + conf_detail.get('score', 0.0) * (0.95 - 0.15)
            struct['confidence'] = round(mapped, 2)
    except Exception:
        # on failure, leave legacy confidence
        struct['confidence_detail'] = {'score': 0.0, 'band': 'low'}

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
    try:
        cur.execute(q, (recommendation_table, limit))
    except sqlite3.OperationalError:
        # Missing recommendation tables should degrade gracefully to an empty list.
        return []
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


def fetch_decision_history(conn, unit_rsid: Optional[str] = None, limit: int = 50):
    cur = conn.cursor()
    # fetch latest decisions, optionally filter by unit_rsid contained in notes JSON
    q = "SELECT id, recommendation_table, recommendation_id, action, notes, user_id, created_at FROM user_decisions ORDER BY created_at DESC LIMIT ?"
    cur.execute(q, (limit,))
    rows = [dict(zip([c[0] for c in cur.description], row)) for row in cur.fetchall()]
    results = []
    for r in rows:
        rec = r.copy()
        # parse notes JSON if present
        try:
            rec_notes = json.loads(rec.get('notes') or '{}')
        except Exception:
            rec_notes = {}
        # if unit_rsid filter supplied, skip mismatches
        if unit_rsid and rec_notes.get('unit_rsid') and rec_notes.get('unit_rsid') != unit_rsid:
            continue
        # attach parsed fields
        rec['unit_rsid'] = rec_notes.get('unit_rsid')
        rec['coa_type'] = rec_notes.get('coa_type')
        rec['coa_title'] = rec_notes.get('coa_title')
        rec['fusion_target'] = rec_notes.get('fusion_target')
        rec['lead_line'] = rec_notes.get('lead_line')
        # fetch an outcome linked to this decision if present
        cur.execute('SELECT outcome_value, outcome_type, observed_at, notes, id FROM outcome_records WHERE decision_id=? ORDER BY created_at DESC LIMIT 1', (rec['id'],))
        orow = cur.fetchone()
        if orow:
            cols = [c[0] for c in cur.description]
            out = dict(zip(cols, orow))
            # try parse outcome_value
            try:
                out['outcome_parsed'] = json.loads(out.get('outcome_value') or '{}')
            except Exception:
                out['outcome_parsed'] = None
            rec['outcome'] = out
        else:
            rec['outcome'] = None
        results.append(rec)
    return results


def compute_decision_summary(conn, unit_rsid: Optional[str] = None):
    # Aggregate minimal LMS summary metrics from recent decisions/outcomes
    decisions = fetch_decision_history(conn, unit_rsid=unit_rsid, limit=500)
    summary = {
        'decision_count_by_type': {},
        'success_rate_by_type': {},
        'avg_contracts_by_type': {},
        'avg_variance_by_type': {},
        'most_used_targets': [],
        'recent_outcomes': []
    }
    counts = {}
    success = {}
    contracts_sum = {}
    variance_sum = {}
    target_counts = {}
    recent_outcomes = []
    for d in decisions:
        t = (d.get('coa_type') or 'UNKNOWN').upper()
        counts[t] = counts.get(t, 0) + 1
        # variance
        var = None
        try:
            var = float(d.get('lead_line', {}) and d.get('lead_line', {}).get('variance')) if d.get('lead_line') else None
        except Exception:
            var = None
        if var is not None:
            variance_sum[t] = variance_sum.get(t, 0.0) + var
        # outcome parsing
        out = d.get('outcome')
        achieved = 0
        if out and out.get('outcome_parsed'):
            try:
                achieved = int(out['outcome_parsed'].get('contracts_achieved') or 0)
            except Exception:
                achieved = 0
        contracts_sum[t] = contracts_sum.get(t, 0) + achieved
        success[t] = success.get(t, 0) + (1 if achieved > 0 else 0)
        # target counts
        tgt = d.get('fusion_target')
        if tgt:
            target_counts[tgt] = target_counts.get(tgt, 0) + 1
        # collect recent outcome row for feed
        if out:
            recent_outcomes.append({
                'decision_id': d.get('id'),
                'coa_type': t,
                'fusion_target': d.get('fusion_target'),
                'contracts_achieved': achieved,
                'observed_at': out.get('observed_at')
            })

    # compute metrics per type
    for t, cnt in counts.items():
        summary['decision_count_by_type'][t] = cnt
        success_count = success.get(t, 0)
        summary['success_rate_by_type'][t] = round((success_count / cnt) if cnt else 0.0, 2)
        summary['avg_contracts_by_type'][t] = round((contracts_sum.get(t, 0) / cnt) if cnt else 0.0, 2)
        summary['avg_variance_by_type'][t] = round((variance_sum.get(t, 0.0) / cnt) if cnt and variance_sum.get(t) is not None else 0.0, 2)

    # most used targets (top 5)
    most_used = sorted(target_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    summary['most_used_targets'] = [{'target': k, 'count': v} for k, v in most_used]
    # recent outcomes (last 10)
    summary['recent_outcomes'] = recent_outcomes[:10]
    return summary
