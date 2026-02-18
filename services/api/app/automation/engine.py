import json
from ..db import connect
from datetime import datetime


def now_iso():
    return datetime.utcnow().isoformat()


def simple_event_recommendation(event_id: int, created_by: str = 'automation') -> dict:
    """Generate deterministic recommendations for an event without external models.

    - staffing_estimate: use LOE (level of effort) if present, default heuristic
    - estimated_costs: sum of event_cost rows (if any)
    - roi_estimate: simple heuristic based on leads per LOE (placeholder)
    """
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id, org_unit_id, name, loe, start_dt, end_dt FROM event WHERE id=?', (event_id,))
        ev = cur.fetchone()
        if not ev:
            return {'error': 'event_not_found'}
        evd = dict(ev)
        loe = evd.get('loe') or 1
        staffing = max(1, int(float(loe) / 5))

        # sum costs
        cur.execute('SELECT SUM(amount) FROM event_cost WHERE event_id=?', (event_id,))
        row = cur.fetchone()
        total_cost = row[0] if row and row[0] is not None else 0

        # simple ROI heuristic
        roi = None
        if total_cost and loe:
            roi = round((loe * 1.0) / (total_cost + 1), 4)

        rec = {
            'event_id': event_id,
            'staffing_estimate': staffing,
            'estimated_cost': total_cost,
            'roi_estimate': roi,
            'generated_at': now_iso(),
            'method': 'simple_heuristic_v1'
        }

        # persist to ai_recommendation table
        cur.execute('INSERT INTO ai_recommendation(scope_type, scope_id, fy, qtr, prompt_hash, output_json, created_at) VALUES (?,?,?,?,?,?,?)', (
            'event', event_id, None, None, None, json.dumps(rec), now_iso()
        ))
        conn.commit()
        return rec
    finally:
        conn.close()


def run_automation_for(trigger: str, target_type: str = 'event', target_id: int = None, initiated_by: str = 'system'):
    """Run automation for a given target. Returns run summary.
    """
    conn = connect()
    try:
        cur = conn.cursor()
        started = now_iso()
        cur.execute('INSERT INTO automation_run_log(name,started_at,status) VALUES (?,?,?)', (f'{trigger}:{target_type}', started, 'running'))
        conn.commit()
        run_id = cur.lastrowid

        results = None
        if target_type == 'event' and target_id is not None:
            results = simple_event_recommendation(target_id, created_by=initiated_by)
        else:
            results = {'note': 'no-op for this trigger/target'}

        finished = now_iso()
        cur.execute('UPDATE automation_run_log SET finished_at=?, status=?, output_json=? WHERE id=?', (finished, 'completed', json.dumps(results), run_id))
        conn.commit()
        return {'run_id': run_id, 'status': 'completed', 'result': results}
    finally:
        conn.close()
