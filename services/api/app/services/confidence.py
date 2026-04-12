from typing import Dict, Any, List


def _band_from_score(s: float) -> str:
    if s < 0.4:
        return 'low'
    if s < 0.6:
        return 'moderate'
    if s < 0.8:
        return 'medium-high'
    return 'high'


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def score_confidence(doctrine_eval: Dict[str, Any], evidence: Dict[str, Any], prior_fusion_score: float = None) -> Dict[str, Any]:
    """Compute an explainable confidence score from doctrine and evidence.

    Returns a dict with `score` in [0,1], `band`, and positive/negative factors.
    """
    # doctrine alignment (0-1) — engine provides `rule_alignment_score`
    doctrine_align = float(doctrine_eval.get('rule_alignment_score', 0.0))

    # data quality: heuristic completeness measure
    dq_points = 0
    dq_total = 0
    # market fields
    dq_total += 3
    market = evidence.get('market') or {}
    if market.get('median_age') is not None:
        dq_points += 1
    if market.get('avg_share') is not None:
        dq_points += 1
    if market.get('infrastructure_score') is not None:
        dq_points += 1
    # school fields
    dq_total += 3
    school = evidence.get('school') or {}
    if school.get('enrollment') is not None:
        dq_points += 1
    if school.get('components') and school['components'].get('historical_production') is not None:
        dq_points += 1
    if school.get('confidence_score') is not None:
        dq_points += 1
    # mission fields
    dq_total += 1
    mission = evidence.get('mission') or {}
    if mission.get('mission_total') is not None:
        dq_points += 1

    data_quality = float(dq_points) / float(dq_total) if dq_total > 0 else 0.0

    # rule support strength: sum weights of triggered rules normalized by number of rules
    triggered = doctrine_eval.get('triggered_rules') or []
    support_strength = 0.0
    try:
        total_w = sum([r.get('weight', 0.0) for r in doctrine_eval.get('triggered_rules')])
        # approximate normalization by capping at 1.0 when many rules
        support_strength = _clamp(total_w / 2.0)
    except Exception:
        support_strength = 0.0

    # conflict penalty: count any DataQuality/Constraints or CONFLICT id triggers
    conflict_count = 0
    conflict_reasons: List[str] = []
    for r in triggered:
        rid = r.get('id', '')
        cat = r.get('category', '')
        if rid.startswith('CONFLICT') or cat in ('Constraints', 'DataQuality'):
            conflict_count += 1
            conflict_reasons.append(r.get('explanation') or rid)

    conflict_factor = min(1.0, 0.15 * conflict_count)

    # combine with weights per spec
    base = 0.4 * doctrine_align + 0.25 * data_quality + 0.2 * support_strength
    raw_score = _clamp(base - conflict_factor)

    # factors for explanation
    positives = []
    negatives = []
    if doctrine_align >= 0.6:
        positives.append('Strong doctrine alignment')
    if support_strength >= 0.3:
        positives.append('Multiple supporting rules triggered')
    if data_quality >= 0.7:
        positives.append('High data completeness')
    if conflict_reasons:
        negatives.extend(conflict_reasons)
    if data_quality < 0.4:
        negatives.append('Incomplete evidence inputs')

    band = _band_from_score(raw_score)

    return {
        'score': round(raw_score, 2),
        'band': band,
        'factors_positive': positives,
        'factors_negative': negatives,
        'raw_components': {
            'doctrine_align': round(doctrine_align, 2),
            'data_quality': round(data_quality, 2),
            'support_strength': round(support_strength, 2),
            'conflict_factor': round(conflict_factor, 2)
        }
    }
