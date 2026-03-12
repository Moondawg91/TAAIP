from typing import Any, Dict, List, Optional, Tuple
from services.api.app.db import connect, row_to_dict
import uuid
from datetime import datetime
import json


def _now_iso():
    return datetime.utcnow().isoformat()


def create_run(unit_rsid: str, mission_total: int, notes: Optional[str] = None) -> str:
    conn = connect(); cur = conn.cursor()
    rid = f"mal_{uuid.uuid4().hex}"
    now = _now_iso()
    cur.execute('INSERT INTO mission_allocation_runs (run_id, unit_rsid, mission_total, status, notes, created_at) VALUES (?,?,?,?,?,?)', (rid, unit_rsid, mission_total, 'created', notes, now))
    try:
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
    return rid


def add_inputs(run_id: str, inputs: List[Dict[str, Any]]) -> int:
    conn = connect(); cur = conn.cursor()
    now = _now_iso()
    count = 0
    for inp in inputs:
        cur.execute('''INSERT INTO mission_allocation_inputs (run_id, company_id, recruiter_capacity, historical_production, funnel_health, dep_loss, school_access, school_population, ascope, pmesii, market_intel, extra_json, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
            run_id,
            inp.get('company_id'),
            inp.get('recruiter_capacity'),
            inp.get('historical_production'),
            inp.get('funnel_health'),
            inp.get('dep_loss'),
            inp.get('school_access'),
            inp.get('school_population'),
            json.dumps(inp.get('ascope')) if inp.get('ascope') is not None else None,
            json.dumps(inp.get('pmesii')) if inp.get('pmesii') is not None else None,
            json.dumps(inp.get('market_intel')) if inp.get('market_intel') is not None else None,
            json.dumps(inp.get('extra')) if inp.get('extra') is not None else None,
            now
        ))
        count += 1
    try:
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
    return count


def list_runs(unit_rsid: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = connect(); cur = conn.cursor()
    if unit_rsid:
        cur.execute('SELECT * FROM mission_allocation_runs WHERE unit_rsid=? ORDER BY created_at DESC', (unit_rsid,))
    else:
        cur.execute('SELECT * FROM mission_allocation_runs ORDER BY created_at DESC')
    return [row_to_dict(cur, r) for r in cur.fetchall()]


def get_run(run_id: str) -> Optional[Dict[str, Any]]:
    conn = connect(); cur = conn.cursor()
    cur.execute('SELECT * FROM mission_allocation_runs WHERE run_id = ? LIMIT 1', (run_id,))
    r = cur.fetchone()
    if not r:
        return None
    return row_to_dict(cur, r)


def get_inputs(run_id: str) -> List[Dict[str, Any]]:
    conn = connect(); cur = conn.cursor()
    cur.execute('SELECT * FROM mission_allocation_inputs WHERE run_id = ? ORDER BY id', (run_id,))
    return [row_to_dict(cur, r) for r in cur.fetchall()]


def compute_run(run_id: str) -> Tuple[bool, str]:
    """
    Placeholder compute function. This scaffolding records that a compute was requested,
    but does not emit final allocations. Implement scoring math in a later pass.

    Returns (ok, message)
    """
    # mark run as running
    conn = connect(); cur = conn.cursor()
    now = _now_iso()
    cur.execute('UPDATE mission_allocation_runs SET status=?, started_at=? WHERE run_id=?', ('running', now, run_id))
    try:
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass

    # Implement scoring skeleton: compute per-company scores and proportional recommendations.
    # Load run and inputs
    cur.execute('SELECT mission_total, unit_rsid FROM mission_allocation_runs WHERE run_id=? LIMIT 1', (run_id,))
    r = cur.fetchone()
    # sqlite3.Row does not implement .get(); use mapping access
    mission_total = (r['mission_total'] if r and 'mission_total' in r.keys() else (r[0] if r else None))

    inputs = get_inputs(run_id)
    if not inputs:
        # nothing to compute — mark run as no-inputs (avoid using missing
        # updated_at column in older DB versions)
        cur.execute('UPDATE mission_allocation_runs SET status=? WHERE run_id=?', ('no-inputs', run_id))
        try:
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
        return False, 'no-inputs'

    # scoring helper functions
    def _norm(v, vmax, vmin=0.0):
        try:
            vmax = float(vmax)
            v = float(v) if v is not None else 0.0
            if vmax <= vmin:
                return 0.0
            return max(0.0, min(1.0, (v - vmin) / (vmax - vmin)))
        except Exception:
            return 0.0

    # derive population max for normalization
    max_school_pop = max([ (i.get('school_population') or 0) for i in inputs ]) or 1
    max_hist = max([ (i.get('historical_production') or 0) for i in inputs ]) or 1
    max_recruiters = max([ (i.get('recruiter_capacity') or 0) for i in inputs ]) or 1

    # weights (tunable)
    weights = {
        'recruiter_capacity': 0.25,
        'historical_production': 0.20,
        'funnel_health': 0.20,
        'market_supportability': 0.15,
        'school_access': 0.10,
        'risk_penalty': -0.10
    }

    # compute intermediate scores per company
    scores = []
    for inp in inputs:
        cid = inp.get('company_id')
        rc = inp.get('recruiter_capacity') or 0
        hp = inp.get('historical_production') or 0
        fh = float(inp.get('funnel_health') or 0.0)
        dl = float(inp.get('dep_loss') or 0)
        sa = float(inp.get('school_access') or 0.0)
        spop = int(inp.get('school_population') or 0)
        # market_intel may be structured; for scaffold use presence as signal
        mkt = inp.get('market_intel')

        recruiter_score = _norm(rc, max_recruiters)
        historical_score = _norm(hp, max_hist)
        funnel_score = max(0.0, min(1.0, fh))
        market_score = 0.5 if mkt else 0.5
        school_score = 0.5 * _norm(spop, max_school_pop) + 0.5 * max(0.0, min(1.0, sa))
        # risk penalty increases with dep_loss and low funnel
        risk_penalty = min(1.0, (dl / max(1.0, hp)) if hp>0 else min(1.0, dl/10.0))

        # weighted supportability (higher is better)
        supportability = (
            weights['recruiter_capacity'] * recruiter_score
            + weights['historical_production'] * historical_score
            + weights['funnel_health'] * funnel_score
            + weights['market_supportability'] * market_score
            + weights['school_access'] * school_score
        )

        # apply risk as penalty
        risk = risk_penalty
        final_score = max(0.0, min(1.0, supportability + weights['risk_penalty'] * risk))

        # confidence heuristic: based on available inputs
        available_fields = sum([1 for k in ('recruiter_capacity','historical_production','funnel_health','dep_loss','school_access','school_population','market_intel') if inp.get(k) is not None])
        confidence = min(1.0, 0.3 + 0.12 * available_fields)

        scores.append({
            'company_id': cid,
            'recruiter_score': recruiter_score,
            'historical_score': historical_score,
            'funnel_score': funnel_score,
            'market_score': market_score,
            'school_score': school_score,
            'supportability_score': supportability,
            'risk_score': risk,
            'final_score': final_score,
            'confidence': confidence
        })

    # persist scores
    for s in scores:
        save_company_score(run_id, s['company_id'], s['supportability_score'], s['risk_score'], s['confidence'], payload=s)

    # allocate proportionally to final_score if mission_total provided
    total_score = sum([s['final_score'] for s in scores])
    recs = []
    for s in scores:
        alloc = None
        if mission_total and total_score > 0:
            alloc = int(round((s['final_score'] / total_score) * float(mission_total)))
        rationale = f"Weighted score based on recruiter capacity, historical production, funnel health, market supportability, school access; risk penalty applied."
        # save recommendation (alloc may be None)
        save_recommendation(run_id, s['company_id'], alloc, rationale, s['confidence'])
        recs.append({
            'company': s['company_id'],
            'recommended_allocation': alloc,
            'supportability_score': s['supportability_score'],
            'risk_score': s['risk_score'],
            'confidence_score': s['confidence'],
            'rationale': rationale,
            'evidence_refs': []
        })

    # mark run completed
    cur.execute('UPDATE mission_allocation_runs SET status=?, completed_at=? WHERE run_id=?', ('computed', _now_iso(), run_id))
    try:
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass

    return True, json.dumps({'results': recs})


def save_company_score(run_id: str, company_id: str, supportability: Optional[float], risk: Optional[float], confidence: Optional[float], payload: Optional[Dict[str, Any]] = None):
    conn = connect(); cur = conn.cursor()
    now = _now_iso()
    cur.execute('INSERT INTO mission_allocation_company_scores (run_id, company_id, supportability_score, risk_score, confidence_score, score_payload, created_at) VALUES (?,?,?,?,?,?,?)', (run_id, company_id, supportability, risk, confidence, json.dumps(payload) if payload else None, now))
    try:
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass


def save_recommendation(run_id: str, company_id: str, recommended_mission: Optional[int], rationale: Optional[str], confidence: Optional[float]):
    conn = connect(); cur = conn.cursor()
    now = _now_iso()
    cur.execute('INSERT INTO mission_allocation_recommendations (run_id, company_id, recommended_mission, rationale, confidence, created_at) VALUES (?,?,?,?,?,?)', (run_id, company_id, recommended_mission, rationale, confidence, now))
    try:
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass


def add_evidence(run_id: str, company_id: Optional[str], evidence_type: str, evidence_uri: Optional[str], description: Optional[str]):
    conn = connect(); cur = conn.cursor()
    now = _now_iso()
    cur.execute('INSERT INTO mission_allocation_evidence (run_id, company_id, evidence_type, evidence_uri, description, created_at) VALUES (?,?,?,?,?,?)', (run_id, company_id, evidence_type, evidence_uri, description, now))
    try:
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
