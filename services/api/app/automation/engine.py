import json
from ..db import connect
from datetime import datetime
from ..services import roi_engine as _roi_engine


def now_iso():
    return datetime.utcnow().isoformat()


def simple_event_recommendation(event_id: int, created_by: str = 'automation') -> dict:
    """Generate deterministic recommendations for an event.

    - staffing_estimate: use LOE (level of effort) if present, default heuristic
    - estimated_costs: sum from spend_fact (authoritative) with event_cost fallback
    - roi_score: authoritative deterministic score from roi_engine scoring formula
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

        # Cost: use spend_fact (authoritative) with event_cost as legacy fallback
        total_cost = 0.0
        try:
            cur.execute('SELECT IFNULL(SUM(amount),0) FROM spend_fact WHERE event_id=?', (str(event_id),))
            row = cur.fetchone()
            if row and row[0]:
                total_cost = float(row[0])
        except Exception:
            pass
        if total_cost == 0.0:
            try:
                cur.execute('SELECT IFNULL(SUM(amount),0) FROM event_cost WHERE event_id=?', (event_id,))
                row = cur.fetchone()
                if row and row[0]:
                    total_cost = float(row[0])
            except Exception:
                pass

        # Leads/contracts from lead_journey_fact
        leads_count = 0
        contracts_count = 0
        try:
            cur.execute(
                'SELECT COUNT(DISTINCT lead_id), '
                'SUM(CASE WHEN contract_flag=1 THEN 1 ELSE 0 END) '
                'FROM lead_journey_fact WHERE event_id=?',
                (str(event_id),)
            )
            row = cur.fetchone()
            if row:
                leads_count = int(row[0] or 0)
                contracts_count = int(row[1] or 0)
        except Exception:
            pass

        # Load thresholds from roi_thresholds table
        cpl_target = _roi_engine._CPL_TARGET_DEFAULT
        cpc_target = _roi_engine._CPC_TARGET_DEFAULT
        try:
            cur.execute('SELECT metric_key, value FROM roi_thresholds')
            for r in cur.fetchall():
                if r[0] == 'cpl_target':
                    cpl_target = float(r[1])
                elif r[0] == 'cpc_target':
                    cpc_target = float(r[1])
        except Exception:
            pass

        # Authoritative deterministic scoring via roi_engine formulas
        contract_s = _roi_engine.compute_contract_outcome_score(contracts_count, total_cost, cpc_target)
        lead_s = _roi_engine.compute_lead_outcome_score(leads_count, total_cost, cpl_target)
        cost_eff_s = _roi_engine.compute_cost_efficiency_score(leads_count, contracts_count)
        # market/targeting alignment not available via raw connection — use neutral 50
        roi_score = _roi_engine.compute_roi_score(contract_s, lead_s, cost_eff_s, 50.0, 50.0)

        rec = {
            'event_id': event_id,
            'staffing_estimate': staffing,
            'estimated_cost': total_cost,
            'leads_count': leads_count,
            'contracts_count': contracts_count,
            'contract_outcome_score': round(contract_s, 2),
            'lead_outcome_score': round(lead_s, 2),
            'cost_efficiency_score': round(cost_eff_s, 2),
            'roi_score': roi_score,
            'effectiveness_band': _roi_engine.effectiveness_band(roi_score),
            'generated_at': now_iso(),
            'method': 'roi_engine_v1',
        }

        # persist to ai_recommendation table
        try:
            cur.execute('INSERT INTO ai_recommendation(scope_type, scope_id, fy, qtr, prompt_hash, output_json, created_at) VALUES (?,?,?,?,?,?,?)', (
                'event', event_id, None, None, None, json.dumps(rec), now_iso()
            ))
            conn.commit()
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            return {'error': 'persist_failed', 'reason': str(e)}
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
        try:
            if target_type == 'event' and target_id is not None:
                results = simple_event_recommendation(target_id, created_by=initiated_by)
            else:
                results = {'note': 'no-op for this trigger/target'}
        except Exception as e:
            # mark run as failed and capture the error
            try:
                finished = now_iso()
                cur.execute('UPDATE automation_run_log SET finished_at=?, status=?, output_json=? WHERE id=?', (finished, 'failed', json.dumps({'error': str(e)}), run_id))
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
            finally:
                conn.close()
            return {'run_id': run_id, 'status': 'failed', 'result': {'error': str(e)}}

        finished = now_iso()
        status = 'completed'
        try:
            cur.execute('UPDATE automation_run_log SET finished_at=?, status=?, output_json=? WHERE id=?', (finished, status, json.dumps(results), run_id))
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
        return {'run_id': run_id, 'status': status, 'result': results}
    finally:
        conn.close()
