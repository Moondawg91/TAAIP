"""Market Health Engine skeleton and helper functions.

This module provides a computation skeleton for market-level health scores.
It intentionally keeps logic simple and well-documented so it can be
extended without breaking audit or storage contracts.
"""
from typing import Dict, Any, Optional
import uuid
import json
from datetime import datetime
from services.api.app.db import connect


def _now_iso():
    return datetime.utcnow().isoformat()


def normalize_signals(raw: Dict[str, Any]) -> Dict[str, float]:
    """Coerce raw inputs into canonical 0..1 signals and return a dict of signals.

    Missing values default to 0.5 (neutral). Values are clipped to 0..1.
    """
    def clip01(v):
        try:
            f = float(v)
        except Exception:
            return 0.5
        if f != f:
            return 0.5
        if f < 0:
            return 0.0
        if f > 1:
            return 1.0
        return f

    signals = {}
    signals['historical_trend'] = clip01(raw.get('historical_trend', 0.5))
    signals['recruiter_ratio'] = clip01(raw.get('recruiter_ratio', 0.5))
    # market_load is expected as ratio current_load/market_capacity; keep 0..1
    signals['market_load'] = clip01(raw.get('market_load', 0.5))
    signals['activity_signal'] = clip01(raw.get('activity_signal', 0.5))
    signals['demographic_signal'] = clip01(raw.get('demographic_signal', 0.5))
    signals['penetration_signal'] = clip01(raw.get('penetration_signal', 0.5))
    # risk_penalty is 0..1 but cap logic handled later
    signals['risk_penalty'] = clip01(raw.get('risk_penalty', 0.0))
    # market_size_index is not normalized here; store raw numeric or None
    try:
        msi = raw.get('market_size_index')
        signals['market_size_index'] = float(msi) if msi is not None else None
    except Exception:
        signals['market_size_index'] = None
    return signals


def calculate_supportability(signals: Dict[str, float]) -> float:
    """Calculate supportability S per adjusted weighting and risk adjustment.

    Formula:
    S = 0.20*recruiter_ratio + 0.20*(1 - market_load) + 0.20*historical_trend
        + 0.15*activity_signal + 0.15*demographic_signal + 0.10*penetration_signal

    Apply risk_penalty: S_adj = S * (1 - min(risk_penalty, 0.35))
    Return value in 0..1
    """
    r = signals
    recruiter_ratio = r.get('recruiter_ratio', 0.5)
    market_load = r.get('market_load', 0.5)
    historical_trend = r.get('historical_trend', 0.5)
    activity_signal = r.get('activity_signal', 0.5)
    demographic_signal = r.get('demographic_signal', 0.5)
    penetration_signal = r.get('penetration_signal', 0.5)
    risk_penalty = r.get('risk_penalty', 0.0)

    S = (
        0.20 * recruiter_ratio
        + 0.20 * (1.0 - market_load)
        + 0.20 * historical_trend
        + 0.15 * activity_signal
        + 0.15 * demographic_signal
        + 0.10 * penetration_signal
    )
    # cap risk penalty to 0.35
    rp = min(risk_penalty, 0.35)
    S_adj = S * (1.0 - rp)
    # ensure 0..1
    if S_adj < 0:
        S_adj = 0.0
    if S_adj > 1:
        S_adj = 1.0
    return S_adj


def calculate_confidence(raw: Dict[str, Any]) -> float:
    """Simple confidence heuristic based on data_quality_flags.

    Accepts raw['data_quality_flags'] as dict of booleans/numeric penalties.
    Returns 0..1 where 1 is fully confident.
    """
    dq = raw.get('data_quality_flags') or {}
    # start at 1.0 and subtract penalties
    conf = 1.0
    # missing_fields penalty
    if dq.get('missing_fields'):
        conf -= 0.25
    # stale_date penalty
    if dq.get('stale_date'):
        conf -= 0.25
    # source_confidence expected numeric 0..1 (higher better)
    sc = dq.get('source_confidence')
    try:
        if sc is not None:
            conf *= float(sc)
    except Exception:
        pass
    # clamp
    if conf < 0.0:
        conf = 0.0
    if conf > 1.0:
        conf = 1.0
    return conf


def compute_market_health(payload: Dict[str, Any], persist: bool = True) -> Dict[str, Any]:
    """Compute market health for a single market and optionally persist results.

    Expected payload keys: market_type, market_id, unit_rsid, as_of_date (ISO),
    and raw signals (historical_trend, recruiter_ratio, market_load, activity_signal,
    demographic_signal, penetration_signal, risk_penalty, market_size_index,
    data_quality_flags).
    """
    conn = None
    try:
        # prepare compute_run_id
        compute_run_id = payload.get('compute_run_id') or f"mhr_{uuid.uuid4().hex}"

        # normalize signals
        signals = normalize_signals(payload)

        # compute supportability
        supportability = calculate_supportability(signals)

        # compute confidence
        confidence = calculate_confidence(payload)

        # burden index: simple heuristic = market_load * (1 - recruiter_ratio)
        burden = signals.get('market_load', 0.5) * (1.0 - signals.get('recruiter_ratio', 0.5))
        if burden < 0:
            burden = 0.0
        if burden > 1:
            burden = 1.0

        adjusted_score = supportability * confidence

        result = {
            'compute_run_id': compute_run_id,
            'market_type': payload.get('market_type'),
            'market_id': payload.get('market_id'),
            'unit_rsid': payload.get('unit_rsid'),
            'as_of_date': payload.get('as_of_date') or _now_iso(),
            'supportability_score': adjusted_score,
            'confidence_score': confidence,
            'burden_index': burden,
            'risk_penalty': signals.get('risk_penalty', 0.0),
            'historical_trend': signals.get('historical_trend'),
            'recruiter_ratio': signals.get('recruiter_ratio'),
            'market_load': signals.get('market_load'),
            'activity_signal': signals.get('activity_signal'),
            'demographic_signal': signals.get('demographic_signal'),
            'penetration_signal': signals.get('penetration_signal'),
            'market_size_index': signals.get('market_size_index'),
            'components_json': json.dumps({'signals': signals}),
            'created_at': _now_iso()
        }

        if persist:
            conn = connect()
            cur = conn.cursor()
            cur.execute('''INSERT INTO market_health_scores (compute_run_id, market_type, market_id, unit_rsid, as_of_date, supportability_score, confidence_score, burden_index, risk_penalty, historical_trend, recruiter_ratio, market_load, activity_signal, demographic_signal, penetration_signal, market_size_index, components_json, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                result['compute_run_id'], result['market_type'], result['market_id'], result['unit_rsid'], result['as_of_date'], result['supportability_score'], result['confidence_score'], result['burden_index'], result['risk_penalty'], result['historical_trend'], result['recruiter_ratio'], result['market_load'], result['activity_signal'], result['demographic_signal'], result['penetration_signal'], result['market_size_index'], result['components_json'], result['created_at']
            ))
            conn.commit()
            # attach inserted id
            try:
                result['id'] = cur.lastrowid
            except Exception:
                result['id'] = None

        return result
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass
