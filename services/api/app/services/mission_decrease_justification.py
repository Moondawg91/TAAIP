from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from threading import Lock
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from sqlalchemy import text

from services.api.app.services import (
    accountability_engine,
    execution_quality,
    loe_engine,
    market_qma,
    school_access,
    targeting_expansion,
)

WEIGHTS = {
    "impact_magnitude": 0.55,
    "recency": 0.20,
    "cross_signal_agreement": 0.25,
}

CONFIDENCE_BANDS = {
    "high": 0.75,
    "medium": 0.50,
}

REQUEST_CACHE_MAX = 200
_REQUEST_CACHE: Dict[str, Dict] = {}
_REQUEST_CACHE_ORDER: List[str] = []
_REQUEST_CACHE_LOCK = Lock()


class DecisionOutputError(Exception):
    def __init__(self, code: str, message: str, details: Optional[Dict] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_payload(self) -> Dict:
        return {
            "status": "error",
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            },
        }


@dataclass
class MissionPeriodTotals:
    start: date
    end: date
    total: Optional[float]
    sample_count: int
    source: str


def _scope_prefix(scope_type: str, scope_value: str) -> str:
    st = (scope_type or "").upper().strip()
    sv = (scope_value or "").strip()
    if st == "USAREC":
        return ""
    if st == "BDE":
        return sv[:1]
    if st == "BN":
        return sv[:2]
    if st == "CO":
        return sv[:3]
    if st == "STN":
        return sv[:4]
    return sv


def _infer_scope(org_id: str) -> Tuple[str, str]:
    oid = (org_id or "").strip().upper()
    if not oid:
        raise DecisionOutputError("invalid_request", "org_id is required")
    if oid == "USAREC":
        return "USAREC", "USAREC"
    if len(oid) == 1:
        return "BDE", oid
    if len(oid) == 2:
        return "BN", oid
    if len(oid) == 3:
        return "CO", oid
    return "STN", oid[:4]


def _default_baseline_window(period_start: date, period_end: date) -> Tuple[date, date]:
    window_days = max(1, (period_end - period_start).days + 1)
    baseline_end = period_start - timedelta(days=1)
    baseline_start = baseline_end - timedelta(days=window_days - 1)
    return baseline_start, baseline_end


def _table_exists(db, table_name: str) -> bool:
    q = text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n")
    return bool(db.execute(q, {"n": table_name}).first())


def _table_columns(db, table_name: str) -> List[str]:
    rows = db.execute(text(f"PRAGMA table_info('{table_name}')")).mappings().all()
    return [str(r.get("name")) for r in rows]


def _compute_mission_total(
    db,
    scope_type: str,
    scope_value: str,
    period_start: date,
    period_end: date,
) -> MissionPeriodTotals:
    if not _table_exists(db, "fact_production"):
        return MissionPeriodTotals(period_start, period_end, None, 0, "fact_production_missing")

    cols = set(_table_columns(db, "fact_production"))
    date_col = "date_key" if "date_key" in cols else ("reporting_date" if "reporting_date" in cols else None)
    if date_col is None:
        return MissionPeriodTotals(period_start, period_end, None, 0, "fact_production_no_date_column")

    where_parts = ["(record_status IS NULL OR record_status='active')"]
    params = {
        "start": period_start.isoformat(),
        "end": period_end.isoformat(),
    }

    if scope_type != "USAREC":
        prefix = _scope_prefix(scope_type, scope_value)
        where_parts.append("org_unit_id LIKE :org_prefix")
        params["org_prefix"] = f"{prefix}%"

    where_sql = " AND ".join(where_parts)
    sql = text(
        f"""
        SELECT
            COUNT(1) AS c,
            SUM(COALESCE(metric_value, 0.0)) AS mission_total
        FROM fact_production
        WHERE {where_sql}
          AND {date_col} >= :start
          AND {date_col} <= :end
        """
    )
    row = db.execute(sql, params).mappings().first() or {}
    count = int(row.get("c") or 0)
    total = row.get("mission_total")
    return MissionPeriodTotals(
        start=period_start,
        end=period_end,
        total=float(total) if total is not None else None,
        sample_count=count,
        source=f"fact_production.{date_col}",
    )


def _safe_summary(output: Dict, top_key: str, summary_key: str) -> Dict:
    if not isinstance(output, dict):
        return {}
    return ((output.get(top_key) or {}).get(summary_key) or {}) if output.get("status") == "ok" else {}


def _safe_timestamp(output: Dict, top_key: str) -> Optional[str]:
    if not isinstance(output, dict):
        return None
    return (output.get(top_key) or {}).get("data_as_of")


def _collect_signal_summaries(db, scope_type: str, scope_value: str) -> Dict:
    market = market_qma.summarize_market_qma(db, scope_type, scope_value, scope_type, scope_value, top_n=15)
    access = school_access.summarize_school_access(db, scope_type, scope_value, scope_type, scope_value, top_n=15)
    execution = execution_quality.summarize_execution_quality(db, scope_type, scope_value, scope_type, scope_value)
    accountability = accountability_engine.classify_scope(db, scope_type, scope_value)
    loe = loe_engine.summarize_loes(db, scope_type, scope_value)
    targeting = targeting_expansion.recommendations_for_scope(db, scope_type, scope_value, top_n=15)

    return {
        "market": {
            "raw": market,
            "summary": _safe_summary(market, "market_qma", "summary"),
            "data_as_of": _safe_timestamp(market, "market_qma"),
        },
        "access": {
            "raw": access,
            "summary": _safe_summary(access, "school_access", "summary"),
            "data_as_of": _safe_timestamp(access, "school_access"),
        },
        "execution": {
            "raw": execution,
            "summary": _safe_summary(execution, "execution_quality", "summary"),
            "data_as_of": _safe_timestamp(execution, "execution_quality"),
        },
        "accountability": {
            "raw": accountability,
            "summary": accountability,
            "data_as_of": datetime.utcnow().isoformat() + "Z",
        },
        "loe": {
            "raw": loe,
            "summary": loe,
            "data_as_of": datetime.utcnow().isoformat() + "Z",
        },
        "targeting": {
            "raw": targeting,
            "summary": {
                "recommendations_count": len(targeting.get("recommendations") or []),
            },
            "data_as_of": datetime.utcnow().isoformat() + "Z",
        },
    }


def _compute_factor_candidates(
    mission_delta_pct: float,
    signals: Dict,
) -> List[Dict]:
    market_summary = signals["market"]["summary"]
    access_summary = signals["access"]["summary"]
    exec_summary = signals["execution"]["summary"]
    acc_summary = signals["accountability"]["summary"]
    loe_summary = signals["loe"]["summary"]

    loe_counts = loe_summary.get("status_counts") or {}
    loe_total = float(loe_summary.get("total_metrics") or 0.0)
    loe_at_risk_ratio = 0.0
    if loe_total > 0:
        loe_at_risk_ratio = (float(loe_counts.get("at_risk") or 0) + float(loe_counts.get("not_met") or 0)) / loe_total

    factors = [
        {
            "factor_id": "mission_delta",
            "label": "Mission output change",
            "impact": mission_delta_pct,
            "source": "fact_production",
            "signal_key": "mission",
            "recency_score": 1.0,
            "agreement_tokens": ["mission_decrease"] if mission_delta_pct < 0 else ["mission_stable"],
            "rationale": "Current mission output compared to baseline window.",
        },
        {
            "factor_id": "market_capability",
            "label": "Market capability",
            "impact": float(market_summary.get("market_capability_score") or 0.0) - 0.5,
            "source": "market_qma",
            "signal_key": "market",
            "recency_score": 1.0 if signals["market"].get("data_as_of") else 0.4,
            "agreement_tokens": ["market_decrease_risk"] if str(market_summary.get("overall_market_status")) == "market_constrained" else ["market_supportive"],
            "rationale": f"overall_market_status={market_summary.get('overall_market_status', 'unknown')}",
        },
        {
            "factor_id": "school_access",
            "label": "School access penetration",
            "impact": float(access_summary.get("penetration_rate") or 0.0) - 0.5,
            "source": "school_access",
            "signal_key": "access",
            "recency_score": 1.0 if signals["access"].get("data_as_of") else 0.4,
            "agreement_tokens": ["access_decrease_risk"] if str(access_summary.get("overall_access_status")) == "access_constrained" else ["access_supportive"],
            "rationale": f"penetration_rate={access_summary.get('penetration_rate', 0.0)}",
        },
        {
            "factor_id": "execution_stalls",
            "label": "Execution stalls",
            "impact": -1.0 * min(1.0, float(exec_summary.get("stall_count") or 0.0) / 10.0),
            "source": "execution_quality",
            "signal_key": "execution",
            "recency_score": 1.0 if signals["execution"].get("data_as_of") else 0.4,
            "agreement_tokens": ["execution_decrease_risk"] if str(exec_summary.get("overall_execution_status")) == "execution_degraded" else ["execution_supportive"],
            "rationale": f"stall_count={exec_summary.get('stall_count', 0)}",
        },
        {
            "factor_id": "loe_health",
            "label": "LOE health",
            "impact": 0.5 - loe_at_risk_ratio,
            "source": "loe",
            "signal_key": "loe",
            "recency_score": 0.8,
            "agreement_tokens": ["loe_decrease_risk"] if loe_at_risk_ratio >= 0.5 else ["loe_supportive"],
            "rationale": f"at_risk_ratio={round(loe_at_risk_ratio, 4)}",
        },
        {
            "factor_id": "accountability_classification",
            "label": "Accountability classification",
            "impact": -0.35 if acc_summary.get("classification") in {"execution_failure", "effort_misaligned", "access_constrained", "market_constrained"} else 0.2,
            "source": "accountability",
            "signal_key": "accountability",
            "recency_score": 0.9,
            "agreement_tokens": ["accountability_decrease_risk"] if acc_summary.get("classification") != "balanced" else ["accountability_supportive"],
            "rationale": f"classification={acc_summary.get('classification', 'unknown')}",
        },
    ]
    return factors


def _agreement_score(tokens: List[str], all_tokens: List[str]) -> float:
    if not tokens:
        return 0.0
    overlap = 0
    for token in tokens:
        overlap += sum(1 for t in all_tokens if t == token)
    # normalize to 0..1 where >=3 confirmations saturate confidence
    return min(1.0, overlap / 3.0)


def rank_causal_factors(candidates: List[Dict]) -> List[Dict]:
    all_tokens: List[str] = []
    for c in candidates:
        all_tokens.extend(list(c.get("agreement_tokens") or []))

    ranked: List[Dict] = []
    for c in candidates:
        impact = float(c.get("impact") or 0.0)
        recency = float(c.get("recency_score") or 0.0)
        agreement = _agreement_score(list(c.get("agreement_tokens") or []), all_tokens)
        weighted = (
            WEIGHTS["impact_magnitude"] * abs(impact)
            + WEIGHTS["recency"] * recency
            + WEIGHTS["cross_signal_agreement"] * agreement
        )
        ranked.append(
            {
                **c,
                "weighted_score": round(weighted, 6),
                "agreement_score": round(agreement, 6),
            }
        )

    ranked.sort(key=lambda x: (-float(x.get("weighted_score") or 0.0), str(x.get("factor_id") or "")))
    return ranked


def derive_confidence_band(score: float) -> str:
    if score >= CONFIDENCE_BANDS["high"]:
        return "high"
    if score >= CONFIDENCE_BANDS["medium"]:
        return "medium"
    return "low"


def _compute_confidence(ranked_factors: List[Dict], signals: Dict, mission_has_data: bool) -> Dict:
    completeness_checks = [
        bool(signals["market"]["summary"]),
        bool(signals["access"]["summary"]),
        bool(signals["execution"]["summary"]),
        bool(signals["accountability"]["summary"]),
        bool(signals["loe"]["summary"]),
        bool(signals["targeting"]["raw"].get("recommendations")),
        mission_has_data,
    ]
    completeness = sum(1 for x in completeness_checks if x) / float(len(completeness_checks))

    top_scores = [float(x.get("weighted_score") or 0.0) for x in ranked_factors[:3]]
    impact_signal = sum(top_scores) / float(len(top_scores)) if top_scores else 0.0

    agreement_signal = sum(float(x.get("agreement_score") or 0.0) for x in ranked_factors[:3]) / float(max(1, len(ranked_factors[:3])))

    confidence_score = min(1.0, 0.45 * completeness + 0.35 * impact_signal + 0.20 * agreement_signal)
    return {
        "score": round(confidence_score, 4),
        "band": derive_confidence_band(confidence_score),
        "completeness": round(completeness, 4),
        "agreement": round(agreement_signal, 4),
    }


def _targeting_shift_recommendation(signals: Dict) -> Dict:
    recs = list((signals["targeting"]["raw"].get("recommendations") or []))
    if not recs:
        return {
            "type": "targeting_shift",
            "priority": 3,
            "title": "No targeting rows available",
            "rationale": "Targeting recommendation engine returned no eligible rows for this scope.",
            "actions": ["Validate StationZipCoverage and market weighting data."],
            "evidence_refs": ["ev-targeting-empty"],
        }

    recs_sorted = sorted(
        recs,
        key=lambda x: (
            -float(x.get("priority_score") or 0.0),
            str(x.get("station_rsid") or ""),
            str(x.get("zip_code") or ""),
        ),
    )
    top = recs_sorted[0]
    return {
        "type": "targeting_shift",
        "priority": 1,
        "title": f"Shift effort to station {top.get('station_rsid', 'unknown')} zip {top.get('zip_code', 'unknown')}",
        "rationale": (
            f"Top priority_score={round(float(top.get('priority_score') or 0.0), 2)} with "
            f"warning_severity={round(float(top.get('warning_severity') or 0.0), 3)}"
        ),
        "actions": [
            "Re-allocate recruiter effort blocks for next 14 days.",
            "Align outreach cadence with F3A cycle.",
            "Review conversion movement at weekly command sync.",
        ],
        "evidence_refs": [f"ev-targeting-{top.get('station_rsid', 'na')}-{top.get('zip_code', 'na')}"] ,
    }


def _build_accountability_brief(scope_type: str, scope_value: str, signals: Dict) -> Dict:
    acc = signals["accountability"]["summary"] or {}
    cls = str(acc.get("classification") or "insufficient_data")

    owners = [
        {"role": "BN S3", "owner_id": f"{scope_value[:2]}-s3"},
        {"role": "CO Commander", "owner_id": f"{scope_value[:3]}-cmd"},
    ]
    overdue = []
    blockers = []

    if cls in {"execution_failure", "effort_misaligned"}:
        overdue.append("Processing bottleneck recovery plan update")
    if cls in {"access_constrained", "market_constrained"}:
        overdue.append("School access campaign refresh")
    if cls == "insufficient_data":
        blockers.append("Insufficient combined signals to classify accountability confidently")

    return {
        "classification": cls,
        "confidence": acc.get("confidence") or "low",
        "owners": owners,
        "overdue_items": sorted(overdue),
        "blockers": sorted(blockers),
        "scope": {"scope_type": scope_type, "scope_value": scope_value},
    }


def _build_loe_summary(signals: Dict) -> Dict:
    loe = signals["loe"]["summary"] or {}
    counts = loe.get("status_counts") or {}
    at_risk = int(counts.get("at_risk") or 0)
    not_met = int(counts.get("not_met") or 0)
    total = int(loe.get("total_metrics") or 0)

    rag = "green"
    rationale = "LOE metrics are stable for the period."
    if total == 0:
        rag = "amber"
        rationale = "No LOE metrics available for this scope."
    elif at_risk + not_met >= max(2, int(0.3 * total)):
        rag = "red"
        rationale = "LOE metrics show material at-risk/not-met concentration."
    elif at_risk > 0:
        rag = "amber"
        rationale = "Some LOE metrics are at risk and require monitoring."

    return {
        "rag": rag,
        "rationale": rationale,
        "status_counts": {
            "met": int(counts.get("met") or 0),
            "at_risk": at_risk,
            "not_met": not_met,
            "unknown": int(counts.get("unknown") or 0),
        },
        "total_metrics": total,
    }


def _generate_executive_summary(mission_delta_pct: float, factors: List[Dict], loe_summary: Dict, confidence: Dict) -> List[str]:
    top_labels = ", ".join([str(f.get("label") or "") for f in factors[:3]]) or "insufficient factor coverage"
    mission_phrase = f"Mission output changed {round(mission_delta_pct * 100.0, 2)}% versus baseline."
    loe_phrase = f"LOE status is {loe_summary.get('rag', 'amber').upper()} with rationale: {loe_summary.get('rationale')}"
    conf_phrase = f"Confidence is {confidence.get('band', 'low').upper()} ({confidence.get('score')})."

    bullets = [
        mission_phrase,
        f"Top causal factors: {top_labels}.",
        loe_phrase,
        conf_phrase,
    ]
    return bullets[:6]


def generate_commander_narrative(
    mission_delta_pct: float,
    factors: List[Dict],
    recommendation: Dict,
    accountability_brief: Dict,
) -> str:
    if not factors:
        return (
            "Signal coverage is limited for this scope and period. Command should verify ingestion freshness, "
            "then re-run decision output before committing to a mission shift."
        )

    direction = "decrease pressure" if mission_delta_pct < 0 else "stable/improving output"
    top_factor = factors[0]
    return (
        f"The period shows {direction}. The strongest contributor is {top_factor.get('label', 'unknown factor')} "
        f"({top_factor.get('rationale', 'no rationale')}). Recommended action is to {recommendation.get('title', 'hold current posture')}. "
        f"Accountability classification is {accountability_brief.get('classification', 'unknown')} with "
        f"{len(accountability_brief.get('overdue_items') or [])} overdue item(s)."
    )


def _build_one_slide_payload(
    mission_delta_summary: Dict,
    factors: List[Dict],
    recommendation: Dict,
    accountability_brief: Dict,
    loe_summary: Dict,
    confidence: Dict,
) -> Dict:
    return {
        "title": "Mission Decrease Justification",
        "mission_delta": mission_delta_summary,
        "causal_factors": [
            {
                "label": f.get("label"),
                "impact": f.get("impact"),
                "weighted_score": f.get("weighted_score"),
                "rationale": f.get("rationale"),
            }
            for f in factors[:5]
        ],
        "recommended_shift": recommendation,
        "accountability": accountability_brief,
        "loe": loe_summary,
        "confidence": confidence,
    }


def _build_evidence_list(request_id: str, signals: Dict, mission_current: MissionPeriodTotals, mission_baseline: MissionPeriodTotals, include_evidence: bool) -> List[Dict]:
    if not include_evidence:
        return []

    evidence = [
        {
            "evidence_id": "ev-mission-current",
            "trace_id": f"{request_id}:mission:current",
            "source": mission_current.source,
            "fields": {
                "start": mission_current.start.isoformat(),
                "end": mission_current.end.isoformat(),
                "total": mission_current.total,
                "sample_count": mission_current.sample_count,
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
        {
            "evidence_id": "ev-mission-baseline",
            "trace_id": f"{request_id}:mission:baseline",
            "source": mission_baseline.source,
            "fields": {
                "start": mission_baseline.start.isoformat(),
                "end": mission_baseline.end.isoformat(),
                "total": mission_baseline.total,
                "sample_count": mission_baseline.sample_count,
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    ]

    for key in ("market", "access", "execution", "accountability", "loe", "targeting"):
        evidence.append(
            {
                "evidence_id": f"ev-{key}",
                "trace_id": f"{request_id}:{key}",
                "source": key,
                "fields": signals[key].get("summary") or {},
                "timestamp": signals[key].get("data_as_of") or datetime.utcnow().isoformat() + "Z",
            }
        )

    if not (signals["targeting"]["raw"].get("recommendations") or []):
        evidence.append(
            {
                "evidence_id": "ev-targeting-empty",
                "trace_id": f"{request_id}:targeting:empty",
                "source": "targeting",
                "fields": {"message": "No targeting recommendations available"},
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        )

    return evidence


def _cache_put(request_id: str, payload: Dict) -> None:
    with _REQUEST_CACHE_LOCK:
        _REQUEST_CACHE[request_id] = payload
        _REQUEST_CACHE_ORDER.append(request_id)
        if len(_REQUEST_CACHE_ORDER) > REQUEST_CACHE_MAX:
            old = _REQUEST_CACHE_ORDER.pop(0)
            _REQUEST_CACHE.pop(old, None)


def get_cached_justification(request_id: str) -> Optional[Dict]:
    with _REQUEST_CACHE_LOCK:
        return _REQUEST_CACHE.get(request_id)


def generate_mission_decrease_justification(
    db,
    org_id: str,
    period_start: date,
    period_end: date,
    baseline_start: Optional[date] = None,
    baseline_end: Optional[date] = None,
    include_evidence: bool = True,
    force_refresh: bool = False,
) -> Dict:
    if period_start > period_end:
        raise DecisionOutputError("invalid_request", "period_start must be <= period_end")

    scope_type, scope_value = _infer_scope(org_id)

    if baseline_start is None or baseline_end is None:
        baseline_start, baseline_end = _default_baseline_window(period_start, period_end)
    if baseline_start > baseline_end:
        raise DecisionOutputError("invalid_request", "baseline_start must be <= baseline_end")

    request_id = f"mdj-{uuid4().hex[:16]}"

    mission_current = _compute_mission_total(db, scope_type, scope_value, period_start, period_end)
    mission_baseline = _compute_mission_total(db, scope_type, scope_value, baseline_start, baseline_end)

    current_total = mission_current.total if mission_current.total is not None else 0.0
    baseline_total = mission_baseline.total if mission_baseline.total is not None else 0.0
    if baseline_total == 0:
        mission_delta_pct = 0.0
    else:
        mission_delta_pct = (current_total - baseline_total) / baseline_total

    signals = _collect_signal_summaries(db, scope_type, scope_value)

    candidates = _compute_factor_candidates(mission_delta_pct, signals)
    ranked_factors = rank_causal_factors(candidates)

    targeting_recommendation = _targeting_shift_recommendation(signals)
    accountability_brief = _build_accountability_brief(scope_type, scope_value, signals)
    loe_summary = _build_loe_summary(signals)
    confidence = _compute_confidence(
        ranked_factors,
        signals,
        mission_has_data=(mission_current.total is not None and mission_baseline.total is not None),
    )

    mission_delta_summary = {
        "current_period": {
            "start": period_start.isoformat(),
            "end": period_end.isoformat(),
            "mission_total": mission_current.total,
            "sample_count": mission_current.sample_count,
        },
        "baseline_period": {
            "start": baseline_start.isoformat(),
            "end": baseline_end.isoformat(),
            "mission_total": mission_baseline.total,
            "sample_count": mission_baseline.sample_count,
        },
        "delta": round((current_total - baseline_total), 4),
        "delta_pct": round(mission_delta_pct, 6),
    }

    executive_summary = _generate_executive_summary(mission_delta_pct, ranked_factors, loe_summary, confidence)
    commander_narrative = generate_commander_narrative(mission_delta_pct, ranked_factors, targeting_recommendation, accountability_brief)

    evidence = _build_evidence_list(request_id, signals, mission_current, mission_baseline, include_evidence)

    recommendations = [
        {
            **targeting_recommendation,
            "recommendation_id": f"rec-{request_id}-targeting",
            "trace_id": f"{request_id}:recommendation:targeting",
            "kind": "targeting_shift",
        },
        {
            "recommendation_id": f"rec-{request_id}-accountability",
            "trace_id": f"{request_id}:recommendation:accountability",
            "kind": "accountability_action",
            "priority": 2,
            "title": "Execute accountability recovery actions",
            "rationale": (
                f"classification={accountability_brief.get('classification')} "
                f"overdue={len(accountability_brief.get('overdue_items') or [])}"
            ),
            "actions": accountability_brief.get("overdue_items") or ["Validate accountability inputs and owners."],
            "evidence_refs": ["ev-accountability"],
        },
    ]

    output = {
        "request_id": request_id,
        "traceability_id": f"trace-{request_id}",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "scope": {"scope_type": scope_type, "scope_value": scope_value},
        "mission_delta_summary": mission_delta_summary,
        "causal_factors": [
            {
                "factor_id": f"cf-{request_id}-{idx + 1}",
                "trace_id": f"{request_id}:factor:{idx + 1}",
                "code": f.get("factor_id"),
                "label": f.get("label"),
                "impact": round(float(f.get("impact") or 0.0), 6),
                "weighted_score": float(f.get("weighted_score") or 0.0),
                "agreement_score": float(f.get("agreement_score") or 0.0),
                "source": f.get("source"),
                "rationale": f.get("rationale"),
            }
            for idx, f in enumerate(ranked_factors)
        ],
        "recommendations": recommendations,
        "accountability_brief": accountability_brief,
        "loe_summary": loe_summary,
        "confidence": confidence,
        "executive_summary": executive_summary,
        "commander_narrative": commander_narrative,
        "one_slide_payload": _build_one_slide_payload(
            mission_delta_summary,
            ranked_factors,
            recommendations[0],
            accountability_brief,
            loe_summary,
            confidence,
        ),
        "assumptions_and_limits": [
            "Mission delta is derived from fact_production totals for the requested and baseline windows.",
            "Signals without active datasets are treated as neutral and surfaced in evidence.",
            "Causal factors are synthesized from existing engines and do not represent a causal proof model.",
            "Deterministic sorting uses weighted_score desc then factor code asc.",
        ],
        "evidence": evidence,
        "force_refresh_used": bool(force_refresh),
    }

    _cache_put(request_id, output)
    return output
