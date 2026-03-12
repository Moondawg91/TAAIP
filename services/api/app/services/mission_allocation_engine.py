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

    # For scaffold: do NOT compute allocations. Leave status as pending_compute.
    cur.execute('UPDATE mission_allocation_runs SET status=?, updated_at=? WHERE run_id=?', ('pending_compute', now, run_id))
    try:
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
    return False, 'compute-not-implemented'


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
