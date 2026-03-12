from fastapi import APIRouter, Body
from typing import Any, Optional
from services.api.app.services import mission_allocation_engine
from services.api.app.db import connect, row_to_dict
import uuid

router = APIRouter(prefix="/v2/mission-allocation", tags=["v2-mission-allocation"])


@router.post('/runs')
def create_run(unit_rsid: str = Body(...), mission_total: int = Body(...), notes: Optional[str] = Body(None), inputs: Optional[list] = Body(None)) -> Any:
    rid = mission_allocation_engine.create_run(unit_rsid, mission_total, notes)
    if inputs:
        mission_allocation_engine.add_inputs(rid, inputs)
    return {'status': 'ok', 'run_id': rid}


@router.get('/runs')
def list_runs(unit_rsid: Optional[str] = None) -> Any:
    rows = mission_allocation_engine.list_runs(unit_rsid)
    return {'status': 'ok', 'rows': rows}


@router.get('/runs/{run_id}')
def get_run(run_id: str) -> Any:
    r = mission_allocation_engine.get_run(run_id)
    if not r:
        return {'status': 'error', 'result': 'not_found'}
    inputs = mission_allocation_engine.get_inputs(run_id)
    return {'status': 'ok', 'run': r, 'inputs': inputs}


@router.post('/runs/{run_id}/compute')
def compute_run(run_id: str) -> Any:
    ok, msg = mission_allocation_engine.compute_run(run_id)
    return {'status': 'ok' if ok else 'pending', 'result': msg}


@router.get('/runs/{run_id}/results')
def get_results(run_id: str) -> Any:
    conn = connect(); cur = conn.cursor()
    # fetch scores and recommendations
    cur.execute('SELECT * FROM mission_allocation_company_scores WHERE run_id = ? ORDER BY id', (run_id,))
    scores = [row_to_dict(cur, r) for r in cur.fetchall()]
    cur.execute('SELECT * FROM mission_allocation_recommendations WHERE run_id = ? ORDER BY id', (run_id,))
    recs = [row_to_dict(cur, r) for r in cur.fetchall()]
    cur.execute('SELECT * FROM mission_allocation_evidence WHERE run_id = ? ORDER BY id', (run_id,))
    evidence = [row_to_dict(cur, r) for r in cur.fetchall()]
    return {'status': 'ok', 'scores': scores, 'recommendations': recs, 'evidence': evidence}
