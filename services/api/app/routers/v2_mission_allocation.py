from fastapi import APIRouter, Body
from datetime import datetime
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
    # Check inputs first: if there are no company inputs, return a friendly
    # no-inputs response without invoking the engine compute path which has
    # historically raised in this edge case.
    inputs = mission_allocation_engine.get_inputs(run_id)
    if not inputs:
        conn = connect(); cur = conn.cursor()
        cur.execute('UPDATE mission_allocation_runs SET status=? WHERE run_id=?', ('no-inputs', run_id))
        try:
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
        return {'status': 'no_inputs', 'message': 'Mission allocation run has no company inputs. Add company input data before computing.', 'recommendations': []}

    # There are inputs — run the engine and forward its result (defensively).
    try:
        ok, msg = mission_allocation_engine.compute_run(run_id)
    except Exception as exc:
        return {'status': 'error', 'message': str(exc)}

    if not ok:
        try:
            m = str(msg)
        except Exception:
            m = 'error'
        return {'status': 'error', 'message': m}

    return {'status': 'ok', 'result': msg}


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
    # build canonical recommendations shape expected by callers
    scores_by_company = {s.get('company_id'): s for s in scores}
    evidence_by_company = {}
    for e in evidence:
        cid = e.get('company_id') or '__global'
        evidence_by_company.setdefault(cid, []).append({'type': e.get('evidence_type'), 'uri': e.get('evidence_uri'), 'description': e.get('description')})

    canonical_recs = []
    for r in recs:
        cid = r.get('company_id')
        score = scores_by_company.get(cid) or {}
        canonical_recs.append({
            'company': cid,
            'recommended_allocation': r.get('recommended_mission'),
            'supportability_score': score.get('supportability_score'),
            'risk_score': score.get('risk_score'),
            'confidence_score': r.get('confidence') if r.get('confidence') is not None else score.get('confidence_score'),
            'rationale': r.get('rationale'),
            'evidence_refs': evidence_by_company.get(cid, [])
        })

    return {'status': 'ok', 'scores': scores, 'recommendations': canonical_recs, 'evidence': evidence}


@router.get('/runs/{run_id}/details')
def get_supporting_details(run_id: str) -> Any:
    """Return supporting details derived from scores, inputs, and evidence.
    Produces briefing-friendly fields:
      - drivers: list of top drivers per company
      - limiting_factors: list of identified limiting factors per company
      - evidence: existing evidence rows
      - assumptions: inferred assumptions when inputs are sparse
    """
    conn = connect(); cur = conn.cursor()
    # fetch persisted scores, recommendations, inputs, and evidence
    cur.execute('SELECT * FROM mission_allocation_company_scores WHERE run_id = ? ORDER BY id', (run_id,))
    scores = [row_to_dict(cur, r) for r in cur.fetchall()]
    cur.execute('SELECT * FROM mission_allocation_recommendations WHERE run_id = ? ORDER BY id', (run_id,))
    recs = [row_to_dict(cur, r) for r in cur.fetchall()]
    cur.execute('SELECT * FROM mission_allocation_inputs WHERE run_id = ? ORDER BY id', (run_id,))
    inputs = [row_to_dict(cur, r) for r in cur.fetchall()]
    cur.execute('SELECT * FROM mission_allocation_evidence WHERE run_id = ? ORDER BY id', (run_id,))
    evidence_rows = [row_to_dict(cur, r) for r in cur.fetchall()]

    # map inputs and evidence by company
    inputs_by_company = {i.get('company_id'): i for i in inputs}
    evidence_by_company = {}
    for e in evidence_rows:
        cid = e.get('company_id') or '__global'
        evidence_by_company.setdefault(cid, []).append({'type': e.get('evidence_type'), 'uri': e.get('evidence_uri'), 'description': e.get('description')})

    # Enrich evidence rows with parsed Market Health details when present so
    # the frontend can present a briefing-friendly summary and structured fields.
    enriched_evidence = []
    for e in evidence_rows:
        er = dict(e)
        if er.get('evidence_type') == 'market_health':
            try:
                parsed = json.loads(er.get('description') or '{}')
            except Exception:
                parsed = {}

            # Some evidence descriptions contain a top-level 'market_health' object;
            # fall back to using the parsed object directly if that's the case.
            mh = parsed.get('market_health') if isinstance(parsed, dict) and 'market_health' in parsed else parsed

            compute_id = None
            support = None
            confidence = None
            burden = None
            risk = None

            if isinstance(mh, dict):
                compute_id = mh.get('compute_run_id') or parsed.get('compute_run_id')
                support = mh.get('supportability_score')
                confidence = mh.get('confidence_score')
                burden = mh.get('burden_index')
                risk = mh.get('risk_penalty')

            # Human-friendly summary used by UI table; keep numeric values concise.
            try:
                support_s = f"{support:.3f}" if support is not None else '—'
            except Exception:
                support_s = '—'
            try:
                confidence_s = f"{confidence:.3f}" if confidence is not None else '—'
            except Exception:
                confidence_s = '—'
            try:
                risk_s = f"{risk:.3f}" if risk is not None else '—'
            except Exception:
                risk_s = '—'

            er['mh_summary'] = f"Applied — run: {compute_id or 'unknown'}, support: {support_s}, confidence: {confidence_s}, risk: {risk_s}"
            er['mh'] = {
                'compute_run_id': compute_id,
                'supportability_score': support,
                'confidence_score': confidence,
                'burden_index': burden,
                'risk_penalty': risk,
            }
        else:
            er['mh_summary'] = None
            er['mh'] = None

        enriched_evidence.append(er)

    # replace evidence_rows with enriched versions for downstream rendering/return
    evidence_rows = enriched_evidence

    # weights mirroring engine's scoring (kept in sync)
    weights = {
        'recruiter_capacity': 0.25,
        'historical_production': 0.20,
        'funnel_health': 0.20,
        'market_supportability': 0.15,
        'school_access': 0.10,
        'risk_penalty': -0.10
    }

    drivers = []
    limiting_factors = []
    assumptions = []

    # helper thresholds
    LOW_RECRUITER = 0.5
    LOW_FUNNEL = 0.5
    LOW_SCHOOL = 0.45

    # iterate companies present in scores or recommendations
    companies = set([s.get('company_id') for s in scores] + [r.get('company_id') for r in recs])
    for cid in companies:
        score_row = next((s for s in scores if s.get('company_id') == cid), {})
        rec_row = next((r for r in recs if r.get('company_id') == cid), {})
        inp = inputs_by_company.get(cid, {})

        # parse score_payload if present, otherwise derive from inputs
        payload = {}
        if score_row and score_row.get('score_payload'):
            try:
                payload = json.loads(score_row.get('score_payload'))
            except Exception:
                payload = {}

        # if payload lacks driver fields, try to recompute from inputs (same logic as engine)
        if not any(k in payload for k in ('recruiter_score','historical_score','funnel_score','market_score','school_score')):
            # recompute using available inputs
            def _norm(v, vmax, vmin=0.0):
                try:
                    vmax = float(vmax)
                    v = float(v) if v is not None else 0.0
                    if vmax <= vmin:
                        return 0.0
                    return max(0.0, min(1.0, (v - vmin) / (vmax - vmin)))
                except Exception:
                    return 0.0

            max_school_pop = max([ (i.get('school_population') or 0) for i in inputs ]) or 1
            max_hist = max([ (i.get('historical_production') or 0) for i in inputs ]) or 1
            max_recruiters = max([ (i.get('recruiter_capacity') or 0) for i in inputs ]) or 1

            rc = inp.get('recruiter_capacity') or 0
            hp = inp.get('historical_production') or 0
            fh = float(inp.get('funnel_health') or 0.0)
            dl = float(inp.get('dep_loss') or 0)
            sa = float(inp.get('school_access') or 0.0)
            spop = int(inp.get('school_population') or 0)
            mkt = inp.get('market_intel')

            recruiter_score = _norm(rc, max_recruiters)
            historical_score = _norm(hp, max_hist)
            funnel_score = max(0.0, min(1.0, fh))
            market_score = 0.5 if mkt else 0.5
            school_score = 0.5 * _norm(spop, max_school_pop) + 0.5 * max(0.0, min(1.0, sa))

            payload.update({
                'recruiter_score': recruiter_score,
                'historical_score': historical_score,
                'funnel_score': funnel_score,
                'market_score': market_score,
                'school_score': school_score
            })

        # compute driver contributions
        contribs = []
        # map payload keys to human labels and engine weights
        mapping = [
            ('recruiter_score', 'Recruiter capacity', weights['recruiter_capacity']),
            ('historical_score', 'Historical production', weights['historical_production']),
            ('funnel_score', 'Funnel health', weights['funnel_health']),
            ('market_score', 'Market supportability', weights['market_supportability']),
            ('school_score', 'School access & population', weights['school_access']),
        ]
        for key, label, w in mapping:
            val = float(payload.get(key) or 0.0)
            contrib = round(w * val, 3)
            contribs.append((label, val, contrib))

        # sort descending by contribution
        contribs.sort(key=lambda x: x[2], reverse=True)
        top = [f"{lbl}: score {v:.2f} (contrib {c:.3f})" for lbl, v, c in contribs if v > 0]
        if not top:
            top = ["No driver signals available"]

        drivers.append({'company_id': cid, 'top_drivers': top})

        # limiting factors (readable bullets)
        limiters = []
        # DEP loss
        dep_loss = inp.get('dep_loss')
        if dep_loss is not None and float(dep_loss) > 0:
            limiters.append(f"DEP loss present (value={dep_loss}) — increases operational risk")

        # low recruiter strength
        r_score = float(payload.get('recruiter_score') or 0.0)
        if r_score < LOW_RECRUITER:
            limiters.append(f"Low recruiter strength (score {r_score:.2f})")

        # weak funnel
        f_score = float(payload.get('funnel_score') or 0.0)
        if f_score < LOW_FUNNEL:
            limiters.append(f"Weak funnel health (score {f_score:.2f})")

        # weak school access
        s_score = float(payload.get('school_score') or 0.0)
        if s_score < LOW_SCHOOL:
            limiters.append(f"Weak school access/population (score {s_score:.2f})")

        # market supportability (if low)
        m_score = float(payload.get('market_score') or 0.0)
        # engine sets market_score=0.5 when market_intel is absent; flag only when clearly low
        if m_score < 0.4:
            limiters.append(f"Low market supportability (score {m_score:.2f})")

        if not limiters:
            limiters = ["No immediate limiting factors identified"]

        limiting_factors.append({'company_id': cid, 'factors': limiters})

        # evidence refs (use existing evidence rows)
        evidence_refs = evidence_by_company.get(cid, [])

        # assumptions: infer missing or sparse inputs
        a = []
        expected_fields = ['recruiter_capacity','historical_production','funnel_health','school_access','school_population','market_intel']
        for f in expected_fields:
            if inp.get(f) is None:
                if f == 'market_intel':
                    a.append('Assumed default market supportability due to missing market intelligence')
                else:
                    a.append(f"Assumed default for {f} because input was not provided")

        # allocation assumption
        if rec_row and rec_row.get('recommended_mission') is not None:
            a.append('Allocations are proportional to computed final scores and rounded to integers')

        if not a:
            a = ['No explicit assumptions — inputs were sufficient']

        # attach derived compact object per company
        # We'll return per-company blocks in drivers/limiting_factors and a top-level assumptions list
    # top-level assumptions include any global evidence presence notes
    global_assumptions = ['Allocations assume proportional distribution based on computed final scores']
    return {'status': 'ok', 'drivers': drivers, 'limiting_factors': limiting_factors, 'evidence': evidence_rows, 'assumptions': global_assumptions}
