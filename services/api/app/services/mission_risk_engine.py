from typing import Any, Dict, List, Optional
from services.api.app.db import connect, row_to_dict
import uuid
import json
from datetime import datetime


def _now_iso():
    return datetime.utcnow().isoformat()


def _norm(v, vmax, vmin=0.0):
    try:
        vmax = float(vmax)
        v = float(v) if v is not None else 0.0
        if vmax <= vmin:
            return 0.0
        return max(0.0, min(1.0, (v - vmin) / (vmax - vmin)))
    except Exception:
        return 0.0


def compute_mission_risks(inputs: List[Dict[str, Any]], persist: bool = True, unit_rsid: Optional[str] = None, as_of_date: Optional[str] = None, compute_run_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Compute mission risk for a list of input rows.

    Each input dict may contain:
      - company_id
      - recruiter_capacity
      - mission_allocation_pressure (0..1)
      - funnel_health (0..1)
      - dep_loss (integer)
      - historical_production (integer)
      - market_intel: {market_type, market_id}
      - school_targeting_pressure (0..1)
      - data_quality_flags: {missing_fields: bool}

    Returns list of results with components and persisted rows when `persist`.
    """
    compute_run_id = compute_run_id or f"mr_{uuid.uuid4().hex}"
    now = as_of_date or _now_iso()

    # basic normalizers: compute maxima for normalization
    max_recruiters = max([ (i.get('recruiter_capacity') or 0) for i in inputs ]) or 1
    max_hist = max([ (i.get('historical_production') or 0) for i in inputs ]) or 1

    weights = {
        'allocation_pressure': 0.25,
        'recruiter_strain': 0.20,
        'funnel_weakness': 0.20,
        'dep_loss_pressure': 0.15,
        'market_health_weakness': 0.10,
        'school_targeting_weakness': 0.10
    }

    conn = None
    if persist:
        conn = connect(); cur = conn.cursor()

    results = []
    for inp in inputs:
        cid = inp.get('company_id')

        # allocation pressure: higher means more pressure -> more risk
        alloc = float(inp.get('mission_allocation_pressure') or inp.get('allocation_pressure') or 0.5)
        alloc = max(0.0, min(1.0, alloc))

        # recruiter strain: low capacity -> higher strain (risk)
        rc = inp.get('recruiter_capacity') or 0
        recruiter_strain = 1.0 - _norm(rc, max_recruiters)

        # funnel weakness: funnel_health high -> low risk
        fh = float(inp.get('funnel_health') or 0.5)
        funnel_weakness = 1.0 - max(0.0, min(1.0, fh))

        # dep loss pressure: normalized against historical production
        dep = float(inp.get('dep_loss') or 0)
        hist = float(inp.get('historical_production') or max_hist or 10)
        dep_pressure = min(1.0, dep / max(1.0, hist))

        # market health weakness: lookup latest market_health_scores if market_intel provided
        market_weakness = 0.5
        evidences = []
        mkt = inp.get('market_intel')
        try:
            mq = json.loads(mkt) if isinstance(mkt, str) else mkt
        except Exception:
            mq = mkt
        if isinstance(mq, dict) and mq.get('market_type') and mq.get('market_id'):
            try:
                cur.execute("SELECT * FROM market_health_scores WHERE market_type=? AND market_id=? ORDER BY created_at DESC LIMIT 1", (mq.get('market_type'), mq.get('market_id')))
                mrow = cur.fetchone()
                if mrow:
                    mhd = row_to_dict(cur, mrow)
                    ms = float(mhd.get('supportability_score') or 0.0)
                    market_weakness = 1.0 - max(0.0, min(1.0, ms))
                    evidences.append({'source_key': 'market_health', 'source_run_id': mhd.get('compute_run_id')})
            except Exception:
                market_weakness = 0.5

        # school targeting weakness: accept provided pressure or try to read latest school_targeting_scores if school_id present
        school_weakness = 0.5
        stp = inp.get('school_targeting_pressure')
        if stp is not None:
            try:
                school_weakness = 1.0 - max(0.0, min(1.0, float(stp)))
            except Exception:
                school_weakness = 0.5
        else:
            # try to look up by company->school mapping via 'school_id' field
            sid = inp.get('school_id')
            if sid:
                try:
                    cur.execute('SELECT * FROM school_targeting_scores WHERE school_id=? ORDER BY created_at DESC LIMIT 1', (sid,))
                    srow = cur.fetchone()
                    if srow:
                        sd = row_to_dict(cur, srow)
                        ps = float(sd.get('priority_score') or sd.get('score') or 0.0)
                        school_weakness = 1.0 - max(0.0, min(1.0, ps))
                        evidences.append({'source_key': 'school_targeting', 'source_run_id': sd.get('compute_run_id')})
                except Exception:
                    school_weakness = 0.5

        # assemble weighted risk (higher numbers => more risk)
        components = {
            'allocation_pressure': alloc,
            'recruiter_strain': recruiter_strain,
            'funnel_weakness': funnel_weakness,
            'dep_loss_pressure': dep_pressure,
            'market_health_weakness': market_weakness,
            'school_targeting_weakness': school_weakness
        }

        raw_score = sum([components[k] * weights.get(k, 0.0) for k in components.keys()])
        mission_risk_score = max(0.0, min(1.0, raw_score))

        # risk level mapping
        if mission_risk_score >= 0.75:
            risk_level = 'high'
        elif mission_risk_score >= 0.4:
            risk_level = 'monitor'
        else:
            risk_level = 'low'

        # confidence heuristic: based on available inputs
        available = sum([1 for k in ('recruiter_capacity','mission_allocation_pressure','funnel_health','dep_loss','market_intel','school_targeting_pressure') if inp.get(k) is not None])
        confidence = min(1.0, 0.3 + 0.12 * available)
        if inp.get('data_quality_flags') and inp.get('data_quality_flags').get('missing_fields'):
            confidence = min(1.0, confidence * 0.7)

        # top risk factors: sort components by contribution (weight*value)
        factors = []
        for k, v in components.items():
            contrib = v * weights.get(k, 0.0)
            factors.append({'name': k, 'value': round(float(v), 4), 'contribution': round(float(contrib), 4)})
        factors = sorted(factors, key=lambda x: x['contribution'], reverse=True)[:3]

        assumptions = [f"weights: {weights}"]

        result = {
            'compute_run_id': compute_run_id,
            'unit_rsid': unit_rsid,
            'company_id': cid,
            'market_type': mq.get('market_type') if isinstance(mq, dict) else None,
            'market_id': mq.get('market_id') if isinstance(mq, dict) else None,
            'as_of_date': now,
            'mission_risk_score': mission_risk_score,
            'risk_level': risk_level,
            'confidence_score': confidence,
            'top_risk_factors': factors,
            'assumptions': assumptions,
            'evidence_refs': evidences,
            'components_json': json.dumps(components),
            'created_at': _now_iso()
        }

        # persist
        if persist:
            try:
                cur.execute('''INSERT INTO mission_risk_scores (compute_run_id, unit_rsid, company_id, market_type, market_id, as_of_date, mission_risk_score, risk_level, confidence_score, components_json, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)''', (
                    result['compute_run_id'], result['unit_rsid'], result['company_id'], result['market_type'], result['market_id'], result['as_of_date'], result['mission_risk_score'], result['risk_level'], result['confidence_score'], result['components_json'], result['created_at']
                ))
                # persist evidence rows
                for e in evidences:
                    try:
                        cur.execute('INSERT INTO mission_risk_evidence (compute_run_id, unit_rsid, company_id, source_key, source_run_id, notes, created_at) VALUES (?,?,?,?,?,?,?)', (compute_run_id, unit_rsid, cid, e.get('source_key'), e.get('source_run_id'), None, _now_iso()))
                    except Exception:
                        pass
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass

        results.append(result)

    if persist and conn:
        try:
            conn.close()
        except Exception:
            pass

    return results
