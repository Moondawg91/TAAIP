from fastapi import APIRouter, Body
from typing import Any, List, Optional
from services.api.app.db import connect, row_to_dict
import uuid
from datetime import datetime
from services.api.app.services import targeting_workflow

router = APIRouter(prefix="/v2/targeting", tags=["v2-targeting"])


def _now_iso():
    return datetime.utcnow().isoformat()


@router.post('/cycles')
def create_cycle(unit_rsid: str = Body(...), cycle_id: Optional[str] = Body(None), cycle_name: Optional[str] = Body(None)):
    conn = connect(); cur = conn.cursor()
    tc = cycle_id or f"cycle_{uuid.uuid4().hex[:8]}"
    now = _now_iso()
    cur.execute('INSERT OR REPLACE INTO targeting_cycle_state (targeting_cycle, unit_rsid, cycle_name, status, current_stage, started_at, created_by, created_at) VALUES (?,?,?,?,?,?,?,?)', (tc, unit_rsid, cycle_name or tc, 'active', 'fusion', now, None, now))
    try:
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
    return {'status': 'ok', 'targeting_cycle': tc}


@router.get('/cycles')
def list_cycles(unit_rsid: Optional[str] = None) -> Any:
    conn = connect(); cur = conn.cursor()
    try:
        if unit_rsid:
            cur.execute('SELECT * FROM targeting_cycle_state WHERE unit_rsid = ? ORDER BY created_at DESC', (unit_rsid,))
        else:
            cur.execute('SELECT * FROM targeting_cycle_state ORDER BY created_at DESC')
        rows = [row_to_dict(cur, r) for r in cur.fetchall()]
        return {'status': 'ok', 'rows': rows}
    except Exception:
        return {'status': 'error', 'rows': []}


@router.post('/fusion')
def create_fusion(recommendation_json: dict = Body(...), unit_rsid: str = Body(...), targeting_cycle: str = Body(...), created_by: Optional[str] = Body(None), ai_generated: Optional[bool] = Body(False), ai_confidence: Optional[float] = Body(None)):
    conn = connect(); cur = conn.cursor()
    rid = f"fr_{uuid.uuid4().hex}"
    now = _now_iso()
    cur.execute('INSERT INTO fusion_recommendations (id, unit_rsid, targeting_cycle, recommendation_json, evidence_links, ai_generated, ai_confidence, created_by, created_at, source_system) VALUES (?,?,?,?,?,?,?,?,?,?)', (rid, unit_rsid, targeting_cycle, json_or_text(recommendation_json), None, 1 if ai_generated else 0, ai_confidence, created_by, now, 'TARGETING_ENGINE'))
    try:
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
    return {'status': 'ok', 'id': rid}


@router.get('/fusion')
def list_fusion(targeting_cycle: Optional[str] = None, unit_rsid: Optional[str] = None):
    conn = connect(); cur = conn.cursor()
    where = []
    params = []
    if targeting_cycle:
        where.append('targeting_cycle=?'); params.append(targeting_cycle)
    if unit_rsid:
        where.append('unit_rsid=?'); params.append(unit_rsid)
    where_sql = ' AND '.join(where) if where else '1=1'
    try:
        cur.execute(f'SELECT * FROM fusion_recommendations WHERE {where_sql} ORDER BY created_at DESC', params)
        rows = [row_to_dict(cur, r) for r in cur.fetchall()]
        return {'status': 'ok', 'rows': rows}
    except Exception:
        return {'status': 'error', 'rows': []}


@router.get('/log')
def query_log(targeting_cycle: Optional[str] = None, limit: Optional[int] = 200):
    """Return targeting_state_log entries newest-first. Supports filtering by targeting_cycle."""
    conn = connect(); cur = conn.cursor()
    try:
        params = []
        where = '1=1'
        if targeting_cycle:
            where = 'targeting_cycle = ?'
            params = [targeting_cycle]
        q = f"SELECT id, targeting_cycle, from_stage, to_stage, actor, actor_type, reason, evidence_links, created_at FROM targeting_state_log WHERE {where} ORDER BY created_at DESC LIMIT ?"
        params.append(limit or 200)
        cur.execute(q, params)
        rows = [row_to_dict(cur, r) for r in cur.fetchall()]
        # map to required shape and return newest-first
        out = []
        for r in rows:
            out.append({
                'id': r.get('id'),
                'targeting_cycle': r.get('targeting_cycle'),
                'from_stage': r.get('from_stage'),
                'to_stage': r.get('to_stage'),
                'actor': r.get('actor'),
                'actor_type': r.get('actor_type'),
                'reason': r.get('reason'),
                'evidence_links': r.get('evidence_links'),
                'created_at': r.get('created_at')
            })
        return {'status': 'ok', 'rows': out}
    except Exception:
        return {'status': 'error', 'rows': []}


@router.get('/dashboard/summary')
def dashboard_summary(unit_rsid: Optional[str] = None, recent_limit: Optional[int] = 5):
    conn = connect(); cur = conn.cursor()
    try:
        # current cycles for unit or overall
        if unit_rsid:
            cur.execute('SELECT targeting_cycle, unit_rsid, current_stage, status, started_at FROM targeting_cycle_state WHERE unit_rsid=? ORDER BY created_at DESC', (unit_rsid,))
        else:
            cur.execute('SELECT targeting_cycle, unit_rsid, current_stage, status, started_at FROM targeting_cycle_state ORDER BY created_at DESC')
        cycles = [row_to_dict(cur, r) for r in cur.fetchall()]

        # counts by stage
        cur.execute('SELECT current_stage, COUNT(1) FROM targeting_cycle_state GROUP BY current_stage')
        counts = {r[0]: r[1] for r in cur.fetchall()}

        # latest fusion/twg/board items
        cur.execute('SELECT id, unit_rsid, targeting_cycle, recommendation_json, created_at FROM fusion_recommendations ORDER BY created_at DESC LIMIT ?', (recent_limit,))
        fusion = [row_to_dict(cur, r) for r in cur.fetchall()]
        cur.execute('SELECT id, unit_rsid, targeting_cycle, nomination_json, approval_status, created_at FROM twg_nominations ORDER BY created_at DESC LIMIT ?', (recent_limit,))
        twg = [row_to_dict(cur, r) for r in cur.fetchall()]
        cur.execute('SELECT id, unit_rsid, targeting_cycle, decision_json, decision_status, created_at FROM tdb_decisions ORDER BY created_at DESC LIMIT ?', (recent_limit,))
        board = [row_to_dict(cur, r) for r in cur.fetchall()]

        return {'status': 'ok', 'cycles': cycles, 'counts_by_stage': counts, 'latest': {'fusion': fusion, 'twg': twg, 'board': board}}
    except Exception:
        return {'status': 'error', 'cycles': [], 'counts_by_stage': {}, 'latest': {'fusion': [], 'twg': [], 'board': []}}


@router.get('/dashboard/pending')
def dashboard_pending(limit: Optional[int] = 200):
    conn = connect(); cur = conn.cursor()
    try:
        # pending approvals from state log
        cur.execute("SELECT id, targeting_cycle, from_stage, to_stage, actor, actor_type, reason, evidence_links, created_at FROM targeting_state_log WHERE reason = 'pending_approval' ORDER BY created_at DESC LIMIT ?", (limit,))
        pending_logs = [row_to_dict(cur, r) for r in cur.fetchall()]
        # pending TWG nominations
        cur.execute("SELECT id, unit_rsid, targeting_cycle, nomination_json, approval_status, created_at FROM twg_nominations WHERE approval_status='pending' ORDER BY created_at DESC LIMIT ?", (limit,))
        pending_twg = [row_to_dict(cur, r) for r in cur.fetchall()]
        # pending decisions (human_approved false)
        cur.execute("SELECT id, unit_rsid, targeting_cycle, decision_json, decision_status, human_approved, created_at FROM tdb_decisions WHERE human_approved=0 ORDER BY created_at DESC LIMIT ?", (limit,))
        pending_decisions = [row_to_dict(cur, r) for r in cur.fetchall()]
        # scheduled sync actions
        cur.execute("SELECT id, unit_rsid, targeting_cycle, action_type, status, scheduled_at, created_at FROM targeting_sync_actions WHERE status='scheduled' ORDER BY created_at DESC LIMIT ?", (limit,))
        pending_actions = [row_to_dict(cur, r) for r in cur.fetchall()]

        return {'status': 'ok', 'pending_logs': pending_logs, 'pending_twg': pending_twg, 'pending_decisions': pending_decisions, 'pending_actions': pending_actions}
    except Exception:
        return {'status': 'error', 'pending_logs': [], 'pending_twg': [], 'pending_decisions': [], 'pending_actions': []}


@router.get('/dashboard/recent-changes')
def dashboard_recent_changes(limit: Optional[int] = 50):
    conn = connect(); cur = conn.cursor()
    try:
        cur.execute("SELECT id, targeting_cycle, from_stage, to_stage, actor, actor_type, reason, evidence_links, created_at FROM targeting_state_log ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = [row_to_dict(cur, r) for r in cur.fetchall()]
        return {'status': 'ok', 'rows': rows}
    except Exception:
        return {'status': 'error', 'rows': []}


def json_or_text(v):
    try:
        import json
        return json.dumps(v)
    except Exception:
        return str(v)


@router.post('/twg')
def create_twg(nomination_json: dict = Body(...), unit_rsid: str = Body(...), targeting_cycle: str = Body(...), nominated_by: Optional[str] = Body(None)):
    conn = connect(); cur = conn.cursor()
    rid = f"twg_{uuid.uuid4().hex}"
    now = _now_iso()
    cur.execute('INSERT INTO twg_nominations (id, unit_rsid, targeting_cycle, nomination_json, evidence_links, nominated_by, nominated_at, approval_status, created_at) VALUES (?,?,?,?,?,?,?,?,?)', (rid, unit_rsid, targeting_cycle, json_or_text(nomination_json), None, nominated_by, now, 'pending', now))
    try:
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
    return {'status': 'ok', 'id': rid}


@router.post('/decisions')
def create_decision(decision_json: dict = Body(...), unit_rsid: str = Body(...), targeting_cycle: str = Body(...), created_by: Optional[str] = Body(None), human_approved: Optional[bool] = Body(False)):
    conn = connect(); cur = conn.cursor()
    rid = f"tdb_{uuid.uuid4().hex}"
    now = _now_iso()
    cur.execute('INSERT INTO tdb_decisions (id, unit_rsid, targeting_cycle, decision_json, decision_status, approved_by, approved_at, human_approved, comments, evidence_links, created_at, created_by) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (rid, unit_rsid, targeting_cycle, json_or_text(decision_json), 'created', None, None, 1 if human_approved else 0, None, None, now, created_by))
    try:
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
    return {'status': 'ok', 'id': rid}


@router.post('/actions')
def create_action(action_type: str = Body(...), payload_json: dict = Body(...), unit_rsid: str = Body(...), targeting_cycle: str = Body(...), created_by: Optional[str] = Body(None)):
    conn = connect(); cur = conn.cursor()
    rid = f"act_{uuid.uuid4().hex}"
    now = _now_iso()
    cur.execute('INSERT INTO targeting_sync_actions (id, unit_rsid, targeting_cycle, action_type, payload_json, status, scheduled_at, created_at, created_by) VALUES (?,?,?,?,?,?,?,?,?)', (rid, unit_rsid, targeting_cycle, action_type, json_or_text(payload_json), 'scheduled', None, now, created_by))
    try:
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
    return {'status': 'ok', 'id': rid}


@router.post('/assessments')
def create_assessment(assessment_json: dict = Body(...), unit_rsid: str = Body(...), targeting_cycle: str = Body(...), assessed_by: Optional[str] = Body(None)):
    conn = connect(); cur = conn.cursor()
    rid = f"assess_{uuid.uuid4().hex}"
    now = _now_iso()
    cur.execute('INSERT INTO targeting_assessments (id, unit_rsid, targeting_cycle, assessment_json, assessed_by, assessed_at, score, outcome, notes, evidence_links, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)', (rid, unit_rsid, targeting_cycle, json_or_text(assessment_json), assessed_by, now, None, None, None, None, now))
    try:
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
    return {'status': 'ok', 'id': rid}


@router.post('/advance')
def advance_cycle(targeting_cycle: str = Body(...), actor: str = Body(...), actor_type: str = Body('human'), reason: Optional[str] = Body(None), evidence_links: Optional[str] = Body(None), force: Optional[bool] = Body(False)):
    ok, msg = targeting_workflow.advance_stage(targeting_cycle, actor, actor_type, reason, evidence_links, force=force)
    return {'status': 'ok' if ok else 'pending', 'result': msg}


@router.post('/approve')
def approve_cycle(targeting_cycle: str = Body(...), actor: str = Body(...), reason: Optional[str] = Body(None), evidence_links: Optional[str] = Body(None)):
    ok, msg = targeting_workflow.approve_pending_transition(targeting_cycle, actor, reason, evidence_links)
    return {'status': 'ok' if ok else 'error', 'result': msg}


@router.get('/guidance')
def get_guidance(unit_rsid: Optional[str] = None):
    """Return Commander Guidance / Must Keep / Must Win blocks for a unit. If no unit_rsid provided, returns empty list."""
    conn = connect(); cur = conn.cursor()
    try:
        if unit_rsid:
            cur.execute('SELECT id, unit_rsid, section, payload, created_at, updated_at FROM targeting_guidance WHERE unit_rsid = ? ORDER BY section', (unit_rsid,))
        else:
            cur.execute('SELECT id, unit_rsid, section, payload, created_at, updated_at FROM targeting_guidance ORDER BY unit_rsid, section')
        rows = [row_to_dict(cur, r) for r in cur.fetchall()]
        # Map payload JSON to objects when possible
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
def upsert_guidance(unit_rsid: str = Body(...), section: str = Body(...), payload: dict = Body(...), id: Optional[str] = Body(None)):
    """Create or update a guidance block. `section` should be one of 'commander_guidance','must_keep','must_win'."""
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
