"""Fusion Engine: simple rule-based fusion of mission, market, and school signals.

Produces fused recommendations persisted to `fusion_recommendations` and
supporting evidence in `fusion_evidence`.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import json, uuid

from ..db import connect


def _now_iso():
    return datetime.utcnow().isoformat()


def _norm_score(v: Optional[float], cap: float = 1.0) -> float:
    try:
        if v is None:
            return 0.0
        f = float(v)
        if f <= 0:
            return 0.0
        # simple normalization heuristic: assume input already roughly 0-1, else scale down
        if f > cap:
            return min(1.0, f / (cap if cap > 0 else f))
        return max(0.0, min(1.0, f))
    except Exception:
        return 0.0


def _compute_mission_pressure(cur, unit_rsid: Optional[str]) -> Dict[str, Any]:
    # pick latest mission_allocation_runs for unit or global
    params = []
    q = "SELECT run_id, unit_rsid, mission_total, created_at FROM mission_allocation_runs"
    if unit_rsid:
        q += " WHERE unit_rsid = ?"
        params = [unit_rsid]
    q += " ORDER BY created_at DESC LIMIT 1"
    try:
        cur.execute(q, params)
        r = cur.fetchone()
        if not r:
            return {'score': 0.0, 'source': None}
        run_id, ur, total, created_at = r[0], r[1], r[2], r[3]
        # normalize: assume reasonable mission_total scale; use 100 as soft-cap
        score = _norm_score(float(total or 0) / 100.0)
        return {'score': score, 'source': {'run_id': run_id, 'mission_total': total, 'created_at': created_at}}
    except Exception:
        return {'score': 0.0, 'source': None}


def _compute_market_opportunity(cur, unit_rsid: Optional[str], as_of_date: Optional[str]) -> Dict[str, Any]:
    # Use market_zip_fact where available; aggregate to unit-level by averaging key signals
    try:
        params = []
        q = "SELECT army_share, p2p, potential_remaining, zip5, rsid_prefix FROM market_zip_fact"
        if unit_rsid:
            q += " WHERE rsid_prefix = ?"
            params = [unit_rsid]
        q += " ORDER BY ingested_at DESC LIMIT 200"
        cur.execute(q, params)
        rows = cur.fetchall()
        if not rows:
            return {'score': 0.0, 'source': None}
        shares = []
        p2ps = []
        potentials = []
        examples = []
        for r in rows:
            try:
                army_share = r[0]
                p2p = r[1]
                pot = r[2]
                zip5 = r[3]
                rsid = r[4]
            except Exception:
                army_share = None; p2p = None; pot = None; zip5 = None; rsid = None
            if army_share is not None:
                try:
                    shares.append(float(army_share))
                except Exception:
                    pass
            if p2p is not None:
                try:
                    p2ps.append(float(p2p))
                except Exception:
                    pass
            if pot is not None:
                try:
                    potentials.append(float(pot))
                except Exception:
                    pass
            examples.append({'zip5': zip5, 'rsid': rsid})

        # compute normalized components
        avg_share = (sum(shares) / len(shares)) if shares else None
        avg_p2p = (sum(p2ps) / len(p2ps)) if p2ps else None
        avg_pot = (sum(potentials) / len(potentials)) if potentials else None

        # normalize: army_share typically 0-1, p2p 0-1, potential scaled by arbitrary counts
        s_share = _norm_score(avg_share if avg_share is not None else 0.0)
        s_p2p = _norm_score(avg_p2p if avg_p2p is not None else 0.0)
        # potential: map to 0-1 by dividing by soft cap 1000
        s_pot = _norm_score((avg_pot or 0.0) / 1000.0)

        # combine components heuristically
        score = 0.5 * s_share + 0.3 * s_p2p + 0.2 * s_pot
        return {'score': max(0.0, min(1.0, score)), 'source': {'examples': examples, 'avg_share': avg_share, 'avg_p2p': avg_p2p, 'avg_pot': avg_pot}}
    except Exception:
        return {'score': 0.0, 'source': None}


def _fetch_top_schools(cur, unit_rsid: Optional[str], limit: int = 20) -> List[Dict[str, Any]]:
    try:
        params = []
        q = 'SELECT school_id, priority_score, confidence_score, components_json, created_at FROM school_targeting_scores'
        if unit_rsid:
            q += ' WHERE unit_rsid = ?'
            params = [unit_rsid]
        q += ' ORDER BY priority_score DESC, confidence_score DESC LIMIT ?'
        params.append(limit)
        cur.execute(q, params)
        rows = cur.fetchall()
        out = []
        for r in rows:
            try:
                sid, pscore, conf, comp, created = r
            except Exception:
                sid = r[0]; pscore = r[1]; conf = r[2]; comp = r[3]; created = r[4] if len(r) > 4 else None
            try:
                compj = json.loads(comp) if comp else None
            except Exception:
                compj = None
            out.append({'school_id': sid, 'priority_score': float(pscore or 0.0), 'confidence_score': float(conf or 0.0), 'components': compj, 'created_at': created})
        return out
    except Exception:
        return []


def run_fusion(unit_rsid: Optional[str] = None, as_of_date: Optional[str] = None) -> Dict[str, Any]:
    """Run a single fusion compute, persist recommendations and evidence, and return a summary.

    Returns dict with `fusion_run_id`, `inserted` count and sample rows.
    """
    conn = connect()
    cur = conn.cursor()
    fusion_run_id = f"fus_{uuid.uuid4().hex}"
    created_at = _now_iso()

    # compute signals
    mission = _compute_mission_pressure(cur, unit_rsid)
    market = _compute_market_opportunity(cur, unit_rsid, as_of_date)
    schools = _fetch_top_schools(cur, unit_rsid, limit=20)

    inserted = 0
    persisted = []

    # If schools present, generate per-school recommendations
    if schools:
        for s in schools:
            school_score = _norm_score(s.get('priority_score'))
            # reduce confidence if school confidence low
            conf = s.get('confidence_score') or 0.0
            school_score = school_score * (0.8 + 0.4 * conf) if conf < 0.8 else school_score

            fusion_score = 0.4 * mission['score'] + 0.3 * market['score'] + 0.3 * school_score

            # decide recommendation type
            if fusion_score >= 0.75:
                rtype = 'prioritize_school_engagement'
                text = f"Increase engagement against School {s.get('school_id')} in Unit {unit_rsid or 'UNASSIGNED'} due to high school priority and mission pressure."
            elif mission['score'] > 0.6 and market['score'] < 0.4:
                rtype = 'review_mission_pressure'
                text = f"Unit {unit_rsid or 'UNASSIGNED'} shows mission pressure; investigate school-level access for {s.get('school_id')}."
            else:
                rtype = 'shift_targeting'
                text = f"Consider shifting targeting towards School {s.get('school_id')} in Unit {unit_rsid or 'UNASSIGNED'} (fusion_score={fusion_score:.2f})."

            evidence = {'mission': mission.get('source'), 'market': market.get('source'), 'school': s}

            try:
                cur.execute('''INSERT INTO fusion_recommendations (fusion_run_id, unit_rsid, school_id, market_key, zip5, mission_pressure_score, market_opportunity_score, school_priority_score, fusion_score, recommendation_type, recommendation_text, evidence_json, as_of_date, created_at)
                               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                    fusion_run_id,
                    unit_rsid,
                    s.get('school_id'),
                    None,
                    None,
                    mission['score'],
                    market['score'],
                    school_score,
                    fusion_score,
                    rtype,
                    text,
                    json.dumps(evidence),
                    as_of_date,
                    created_at
                ))
                rid = cur.lastrowid
                # persist evidence row
                cur.execute('''INSERT INTO fusion_evidence (fusion_run_id, source_type, source_ref, payload_json, created_at) VALUES (?,?,?,?,?)''', (
                    fusion_run_id,
                    'school_targeting',
                    s.get('school_id'),
                    json.dumps(s),
                    created_at
                ))
                inserted += 1
                persisted.append({'id': rid, 'fusion_run_id': fusion_run_id, 'unit_rsid': unit_rsid, 'school_id': s.get('school_id'), 'fusion_score': fusion_score, 'recommendation_type': rtype, 'recommendation_text': text})
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
                continue
    else:
        # No school-level data: create unit-level recommendations
        fusion_score = 0.4 * mission['score'] + 0.3 * market['score'] + 0.3 * 0.0
        if fusion_score >= 0.7:
            rtype = 'increase_market_focus'
            text = f"Review market focus for Unit {unit_rsid or 'UNASSIGNED'}; opportunity remains while mission pressure is elevated."
        elif mission['score'] > 0.6:
            rtype = 'review_mission_pressure'
            text = f"Unit {unit_rsid or 'UNASSIGNED'} shows elevated mission pressure without matching market/school signals; reassess allocation."
        else:
            rtype = 'investigate_low_opportunity'
            text = f"Unit {unit_rsid or 'UNASSIGNED'} shows low fusion score; consider rebalancing efforts."

        evidence = {'mission': mission.get('source'), 'market': market.get('source')}
        try:
            cur.execute('''INSERT INTO fusion_recommendations (fusion_run_id, unit_rsid, school_id, market_key, zip5, mission_pressure_score, market_opportunity_score, school_priority_score, fusion_score, recommendation_type, recommendation_text, evidence_json, as_of_date, created_at)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                fusion_run_id,
                unit_rsid,
                None,
                None,
                None,
                mission['score'],
                market['score'],
                None,
                fusion_score,
                rtype,
                text,
                json.dumps(evidence),
                as_of_date,
                created_at
            ))
            rid = cur.lastrowid
            cur.execute('''INSERT INTO fusion_evidence (fusion_run_id, source_type, source_ref, payload_json, created_at) VALUES (?,?,?,?,?)''', (
                fusion_run_id,
                'unit_summary',
                unit_rsid,
                json.dumps(evidence),
                created_at
            ))
            inserted += 1
            persisted.append({'id': rid, 'fusion_run_id': fusion_run_id, 'unit_rsid': unit_rsid, 'fusion_score': fusion_score, 'recommendation_type': rtype, 'recommendation_text': text})
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass

    try:
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass

    return {'fusion_run_id': fusion_run_id, 'inserted': inserted, 'rows': persisted}


def latest_recommendations(unit_rsid: Optional[str] = None, as_of_date: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    conn = connect()
    cur = conn.cursor()
    params = []
    q = 'SELECT id, fusion_run_id, unit_rsid, school_id, market_key, zip5, mission_pressure_score, market_opportunity_score, school_priority_score, fusion_score, recommendation_type, recommendation_text, evidence_json, as_of_date, created_at FROM fusion_recommendations'
    if unit_rsid:
        q += ' WHERE unit_rsid = ?'
        params = [unit_rsid]
    q += ' ORDER BY created_at DESC LIMIT ?'
    params.append(limit)
    try:
        cur.execute(q, params)
        rows = cur.fetchall()
        out = []
        for r in rows:
            rec = dict(r)
            try:
                rec['evidence_json'] = json.loads(rec.get('evidence_json') or '{}')
            except Exception:
                rec['evidence_json'] = rec.get('evidence_json')
            out.append(rec)
        return out
    except Exception:
        return []
