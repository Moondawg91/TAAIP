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
    funnel_engine,
    loe_engine,
    market_engine,
    roi_engine,
    school_access,
    school_plan_engine,
    targeting_engine,
    twg_engine,
    targeting_board_engine,
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
    market = market_engine.summarize_market_engine(db, scope_type, scope_value, scope_type, scope_value, top_n=15)
    access = school_access.summarize_school_access(db, scope_type, scope_value, scope_type, scope_value, top_n=15)
    execution = execution_quality.summarize_execution_quality(db, scope_type, scope_value, scope_type, scope_value)
    funnel = funnel_engine.summarize_funnel_engine(db, scope_type, scope_value, scope_type, scope_value, top_n=15)
    accountability = accountability_engine.classify_scope(db, scope_type, scope_value)
    loe = loe_engine.summarize_loes(db, scope_type, scope_value)
    targeting = targeting_engine.summarize_targeting_engine(db, scope_type, scope_value, scope_type, scope_value, top_n=15)
    school_plan = school_plan_engine.summarize_school_plan_engine(db, scope_type, scope_value, scope_type, scope_value, top_n=15)
    roi = roi_engine.summarize_roi_engine(db, scope_type, scope_value, scope_type, scope_value, top_n=15)
    twg = twg_engine.summarize_twg_engine(db, scope_type, scope_value, scope_type, scope_value, top_n=15)
    board = targeting_board_engine.summarize_targeting_board_engine(db, scope_type, scope_value, scope_type, scope_value, top_n=15)

    return {
        "market": {
            "raw": market,
            "summary": _safe_summary(market, "market_engine", "summary"),
            "data_as_of": _safe_timestamp(market, "market_engine"),
            "source_dataset_name": (market.get("market_engine") or {}).get("source_dataset_name"),
            "rows_used": len(((market.get("market_engine") or {}).get("prioritized_market_zip") or [])),
        },
        "access": {
            "raw": access,
            "summary": _safe_summary(access, "school_access", "summary"),
            "data_as_of": _safe_timestamp(access, "school_access"),
            "source_dataset_name": (access.get("school_access") or {}).get("source_dataset_name"),
            "rows_used": len(((access.get("school_access") or {}).get("top_access_gaps") or [])),
        },
        "execution": {
            "raw": execution,
            "summary": _safe_summary(execution, "execution_quality", "summary"),
            "data_as_of": _safe_timestamp(execution, "execution_quality"),
        },
        "funnel": {
            "raw": funnel,
            "summary": _safe_summary(funnel, "funnel_engine", "summary"),
            "data_as_of": _safe_timestamp(funnel, "funnel_engine"),
            "source_dataset_name": (funnel.get("funnel_engine") or {}).get("source_dataset_name"),
            "rows_used": len(((funnel.get("funnel_engine") or {}).get("prioritized_funnel_gaps") or [])),
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
                "recommendations_count": len(((targeting.get("targeting_engine") or {}).get("prioritized_targets") or [])),
                "high_priority_count": int((((targeting.get("targeting_engine") or {}).get("summary") or {}).get("high_priority_count") or 0)),
            },
            "data_as_of": datetime.utcnow().isoformat() + "Z",
            "source_dataset_name": ((targeting.get("targeting_engine") or {}).get("data_sources") or {}).get("market"),
            "rows_used": len(((targeting.get("targeting_engine") or {}).get("prioritized_targets") or [])),
        },
        "school_plan": {
            "raw": school_plan,
            "summary": _safe_summary(school_plan, "school_plan_engine", "summary"),
            "data_as_of": _safe_timestamp(school_plan, "school_plan_engine"),
            "source_dataset_name": (school_plan.get("school_plan_engine") or {}).get("source_school_dataset"),
            "rows_used": len(((school_plan.get("school_plan_engine") or {}).get("prioritized_schools") or [])),
        },
        "roi": {
            "raw": roi,
            "summary": _safe_summary(roi, "roi_engine", "summary"),
            "data_as_of": _safe_timestamp(roi, "roi_engine"),
            "rows_used": len(((roi.get("roi_engine") or {}).get("prioritized_events") or [])),
        },
        "twg": {
            "raw": twg,
            "summary": _safe_summary(twg, "twg_engine", "summary"),
            "data_as_of": _safe_timestamp(twg, "twg_engine"),
            "rows_used": len(((twg.get("twg_engine") or {}).get("prioritized_items") or [])),
        },
        "board": {
            "raw": board,
            "summary": _safe_summary(board, "targeting_board_engine", "summary"),
            "data_as_of": _safe_timestamp(board, "targeting_board_engine"),
            "rows_used": len(((board.get("targeting_board_engine") or {}).get("prioritized_board_items") or [])),
        },
    }


def _compute_factor_candidates(
    mission_delta_pct: float,
    signals: Dict,
) -> List[Dict]:
    market_summary = signals["market"]["summary"]
    access_summary = signals["access"]["summary"]
    exec_summary = signals["execution"]["summary"]
    funnel_summary = signals["funnel"]["summary"]
    school_plan_summary = signals["school_plan"]["summary"]
    acc_summary = signals["accountability"]["summary"]
    loe_summary = signals["loe"]["summary"]
    roi_summary = signals.get("roi", {}).get("summary") or {}
    twg_summary = signals.get("twg", {}).get("summary") or {}

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
            "agreement_tokens": ["mission_increase"] if mission_delta_pct > 0 else (["mission_decrease"] if mission_delta_pct < 0 else ["mission_stable"]),
            "rationale": "Current mission output compared to baseline window.",
        },
        {
            "factor_id": "market_capability",
            "label": "Market capability",
            "impact": float(market_summary.get("market_capability_score") or 0.0) - 0.5,
            "source": "market_engine",
            "signal_key": "market",
            "recency_score": 1.0 if signals["market"].get("data_as_of") else 0.4,
            "agreement_tokens": ["market_decrease_risk"] if str(market_summary.get("overall_market_status")) in {"weak", "market_constrained"} else ["market_supportive"],
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
            "factor_id": "funnel_health",
            "label": "Funnel conversion health",
            "impact": float(funnel_summary.get("lead_to_contract_rate") or 0.0) - 0.15,
            "source": "funnel_engine",
            "signal_key": "funnel",
            "recency_score": 1.0 if signals["funnel"].get("data_as_of") else 0.4,
            "agreement_tokens": ["funnel_decrease_risk"] if str(funnel_summary.get("overall_funnel_status")) in {"critical", "watch"} else ["funnel_supportive"],
            "rationale": (
                f"overall_funnel_status={funnel_summary.get('overall_funnel_status', 'unknown')}, "
                f"lead_to_contract_rate={funnel_summary.get('lead_to_contract_rate', 0.0)}"
            ),
        },
        {
            "factor_id": "school_plan_gap",
            "label": "School plan under-engagement pressure",
            "impact": -1.0 * (
                (float(school_plan_summary.get("underengaged_school_count") or 0.0) / float(max(1, school_plan_summary.get("total_schools") or 0)))
            ),
            "source": "school_plan_engine",
            "signal_key": "school_plan",
            "recency_score": 1.0 if signals["school_plan"].get("data_as_of") else 0.4,
            "agreement_tokens": ["school_plan_decrease_risk"] if int(school_plan_summary.get("priority_school_count") or 0) > 0 else ["school_plan_supportive"],
            "rationale": (
                f"underengaged_school_count={school_plan_summary.get('underengaged_school_count', 0)}, "
                f"priority_school_count={school_plan_summary.get('priority_school_count', 0)}"
            ),
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
        {
            "factor_id": "roi_effectiveness",
            "label": "Event ROI effectiveness",
            "impact": -1.0 * (
                float(roi_summary.get("low_effectiveness_count") or 0)
                / float(max(1, roi_summary.get("total_events_scored") or 1))
            ),
            "source": "roi_engine",
            "signal_key": "roi",
            "recency_score": 1.0 if signals.get("roi", {}).get("data_as_of") else 0.4,
            "agreement_tokens": ["roi_decrease_risk"] if int(roi_summary.get("low_effectiveness_count") or 0) > 0 else ["roi_supportive"],
            "rationale": (
                f"low_effectiveness_count={roi_summary.get('low_effectiveness_count', 0)}, "
                f"total_events_scored={roi_summary.get('total_events_scored', 0)}, "
                f"avg_roi_score={roi_summary.get('avg_roi_score')}"
            ),
        },
        {
            "factor_id": "twg_issue_concentration",
            "label": "TWG issue concentration",
            "impact": -1.0 * (
                float(twg_summary.get("high_priority_count") or 0)
                / float(max(1, twg_summary.get("total_items") or 1))
            ),
            "source": "twg_engine",
            "signal_key": "twg",
            "recency_score": 1.0 if signals.get("twg", {}).get("data_as_of") else 0.4,
            "agreement_tokens": ["twg_decrease_risk"] if int(twg_summary.get("high_priority_count") or 0) > 0 else ["twg_supportive"],
            "rationale": (
                f"high_priority_count={twg_summary.get('high_priority_count', 0)}, "
                f"total_items={twg_summary.get('total_items', 0)}, "
                f"overall_twg_status={twg_summary.get('overall_twg_status', 'unknown')}"
            ),
        },
        {
            "factor_id": "board_decision_approval",
            "label": "Board decision approval rate",
            "impact": (
                float(signals.get("board", {}).get("summary", {}).get("approved_count") or 0)
                / float(max(1, signals.get("board", {}).get("summary", {}).get("total_items") or 1))
                - 0.5
            ),
            "source": "targeting_board_engine",
            "signal_key": "board",
            "recency_score": 1.0 if signals.get("board", {}).get("data_as_of") else 0.4,
            "agreement_tokens": ["board_executed"] if float(signals.get("board", {}).get("summary", {}).get("approved_count") or 0) > 0 else ["board_pending"],
            "rationale": (
                f"approved_count={signals.get('board', {}).get('summary', {}).get('approved_count', 0)}, "
                f"total_items={signals.get('board', {}).get('summary', {}).get('total_items', 0)}, "
                f"posture={signals.get('board', {}).get('summary', {}).get('overall_board_posture', 'unknown')}"
            ),
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


def _compute_confidence(ranked_factors: List[Dict], signals: Dict, mission_has_data: bool) -> Tuple[Dict, float]:
    completeness_checks = [
        bool(signals["market"]["summary"]),
        bool(signals["access"]["summary"]),
        bool(signals["execution"]["summary"]),
        bool(signals["funnel"]["summary"]),
        bool(signals["accountability"]["summary"]),
        bool(signals["loe"]["summary"]),
        bool(((signals["targeting"]["raw"].get("targeting_engine") or {}).get("prioritized_targets") or [])),
        bool(signals["school_plan"]["summary"]),
        bool((signals.get("roi", {}).get("raw", {}).get("roi_engine") or {}).get("prioritized_events")),
        bool((signals.get("twg", {}).get("raw", {}).get("twg_engine") or {}).get("prioritized_items")),
        mission_has_data,
    ]
    completeness = sum(1 for x in completeness_checks if x) / float(len(completeness_checks))

    top_scores = [float(x.get("weighted_score") or 0.0) for x in ranked_factors[:3]]
    impact_signal = sum(top_scores) / float(len(top_scores)) if top_scores else 0.0

    agreement_signal = sum(float(x.get("agreement_score") or 0.0) for x in ranked_factors[:3]) / float(max(1, len(ranked_factors[:3])))

    recency_checks = [
        bool(signals["market"].get("data_as_of")),
        bool(signals["access"].get("data_as_of")),
        bool(signals["execution"].get("data_as_of")),
        bool(signals["funnel"].get("data_as_of")),
        bool(signals["accountability"].get("data_as_of")),
        bool(signals["loe"].get("data_as_of")),
        bool(signals["targeting"].get("data_as_of")),
        bool(signals["school_plan"].get("data_as_of")),
        bool(signals.get("roi", {}).get("data_as_of")),
        bool(signals.get("twg", {}).get("data_as_of")),
    ]
    recency_signal = sum(1 for x in recency_checks if x) / float(len(recency_checks))

    confidence_score = min(
        1.0,
        0.35 * completeness + 0.25 * impact_signal + 0.20 * agreement_signal + 0.20 * recency_signal,
    )
    return {
        "score": round(confidence_score, 4),
        "band": derive_confidence_band(confidence_score),
        "completeness": round(completeness, 4),
        "agreement": round(agreement_signal, 4),
    }, round(recency_signal, 4)


def _access_is_strong(access_summary: Dict) -> bool:
    penetration = float(access_summary.get("penetration_rate") or 0.0)
    status = str(access_summary.get("overall_access_status") or "").lower()
    return penetration >= 0.5 or status in {"access_supportive", "supportive", "green"}


def _access_is_weak(access_summary: Dict) -> bool:
    penetration = float(access_summary.get("penetration_rate") or 0.0)
    status = str(access_summary.get("overall_access_status") or "").lower()
    return penetration <= 0.35 or status in {"access_constrained", "constrained", "red"}


def _count_degraded_causal_factors(ranked_factors: List[Dict]) -> int:
    return sum(1 for f in ranked_factors[:5] if float(f.get("impact") or 0.0) < 0)


def _count_major_degraded_factors(ranked_factors: List[Dict]) -> int:
    return sum(1 for f in ranked_factors[:5] if float(f.get("impact") or 0.0) <= -0.35)


def _is_strong_amber(loe_summary: Dict) -> bool:
    if str(loe_summary.get("rag") or "").lower() != "amber":
        return False
    counts = loe_summary.get("status_counts") or {}
    total = int(loe_summary.get("total_metrics") or 0)
    if total <= 0:
        return False
    not_met = int(counts.get("not_met") or 0)
    at_risk = int(counts.get("at_risk") or 0)
    return not_met == 0 and (at_risk / float(total)) <= 0.2


def _loe_supports_increase(loe_summary: Dict) -> bool:
    rag = str(loe_summary.get("rag") or "amber").lower()
    return rag == "green" or _is_strong_amber(loe_summary)


def _loe_supports_decrease(loe_summary: Dict) -> bool:
    rag = str(loe_summary.get("rag") or "amber").lower()
    return rag in {"amber", "red"}


def _has_access_market_failure_signals(signals: Dict) -> bool:
    access_summary = (signals.get("access") or {}).get("summary") or {}
    market_summary = (signals.get("market") or {}).get("summary") or {}
    market_status = str(market_summary.get("overall_market_status") or "unknown").lower()
    return _access_is_weak(access_summary) or market_status in {"market_constrained", "constrained", "failure", "degraded", "weak"}


def _magnitude_from_delta(
    delta_pct: float,
    confidence_score: float,
    loe_summary: Dict,
    degraded_factor_count: int,
    agreement_score: float,
    action_type: str,
) -> str:
    abs_delta = abs(float(delta_pct or 0.0))

    # Magnitude hardening rules:
    # - minor: |delta| <= 5% OR confidence < 0.5
    # - moderate: |delta| in (5%, 15%] AND LOE aligned with action direction
    # - significant: |delta| > 15% AND strong agreement AND confidence >= 0.7
    # - never significant when confidence < 0.6
    if abs_delta <= 0.05 or float(confidence_score or 0.0) < 0.5:
        return "minor"

    loe_aligned = False
    if action_type == "increase":
        loe_aligned = _loe_supports_increase(loe_summary)
    elif action_type == "decrease":
        loe_aligned = _loe_supports_decrease(loe_summary)

    if abs_delta > 0.15:
        if float(confidence_score or 0.0) < 0.6:
            return "moderate" if loe_aligned else "minor"
        if float(confidence_score or 0.0) >= 0.7 and float(agreement_score or 0.0) >= 0.67 and degraded_factor_count >= 2:
            return "significant"
        return "moderate" if loe_aligned else "minor"

    if 0.05 < abs_delta <= 0.15 and loe_aligned:
        return "moderate"

    return "minor"


def _infer_owner_level(scope_type: str) -> str:
    st = str(scope_type or "").upper()
    if st in {"USAREC", "BDE", "BN"}:
        return "BN"
    if st == "CO":
        return "CO"
    return "STN"


def _build_confidence_explanation(confidence: Dict, recency_signal: float, degraded_factor_count: int) -> str:
    band = str(confidence.get("band") or "low").lower()
    completeness = float(confidence.get("completeness") or 0.0)
    agreement = float(confidence.get("agreement") or 0.0)

    if band == "high":
        return (
            f"Confidence is high because completeness ({completeness:.0%}), agreement ({agreement:.0%}), and recency ({recency_signal:.0%}) are strong across key signals."
        )
    if band == "medium":
        return (
            f"Confidence is medium because completeness ({completeness:.0%}), agreement ({agreement:.0%}), and recency ({recency_signal:.0%}) are mixed with {degraded_factor_count} degraded drivers."
        )
    return (
        f"Confidence is low because completeness ({completeness:.0%}), agreement ({agreement:.0%}), and recency ({recency_signal:.0%}) are insufficient for a stronger adjustment decision."
    )


def _derive_recommended_action(
    mission_delta_pct: float,
    loe_summary: Dict,
    signals: Dict,
    confidence: Dict,
    ranked_factors: List[Dict],
) -> Dict:
    """
    Deterministic mission adjustment rule set.

    Rules:
    1) Increase: performance above baseline + strong LOE + strong access + confidence floor.
    2) Decrease: performance below baseline + degraded LOE + weak access + confidence floor.
    3) Otherwise: hold.
    """
    delta = float(mission_delta_pct or 0.0)
    conf_score = float(confidence.get("score") or 0.0)
    loe_rag = str(loe_summary.get("rag") or "amber").lower()
    access_summary = (signals.get("access") or {}).get("summary") or {}

    strong_loe = _loe_supports_increase(loe_summary)
    degraded_loe = _loe_supports_decrease(loe_summary)
    strong_access = _access_is_strong(access_summary)
    weak_access = _access_is_weak(access_summary)
    degraded_factor_count = _count_degraded_causal_factors(ranked_factors)
    major_degraded_factor_count = _count_major_degraded_factors(ranked_factors)
    market_status = str(((signals.get("market") or {}).get("summary") or {}).get("overall_market_status") or "unknown").lower()
    loe_missing = int(loe_summary.get("total_metrics") or 0) == 0
    targeting_missing = len(((((signals.get("targeting") or {}).get("raw") or {}).get("targeting_engine") or {}).get("prioritized_targets") or [])) == 0
    uncertain = loe_missing or market_status == "unknown" or targeting_missing

    action_type = "hold"
    if (
        delta > 0
        and strong_loe
        and strong_access
        and conf_score >= 0.6
        and major_degraded_factor_count == 0
        and not uncertain
    ):
        action_type = "increase"
    elif (
        delta < 0
        and degraded_loe
        and (
            degraded_factor_count >= 2
            or weak_access
            or _has_access_market_failure_signals(signals)
        )
    ):
        action_type = "decrease"

    magnitude = _magnitude_from_delta(
        delta_pct=delta,
        confidence_score=conf_score,
        loe_summary=loe_summary,
        degraded_factor_count=degraded_factor_count,
        agreement_score=float(confidence.get("agreement") or 0.0),
        action_type=action_type,
    )
    top_labels = [str(f.get("label") or "") for f in ranked_factors[:3] if str(f.get("label") or "").strip()]
    driver_text = ", ".join(top_labels[:2]) if top_labels else "cross-signal conditions"

    if action_type == "increase":
        rationale = (
            f"Performance is above baseline with supportive LOE and access conditions; {driver_text} support an increase posture."
        )
    elif action_type == "decrease":
        rationale = (
            f"Performance is below baseline with degraded LOE and constrained access; {driver_text} indicate sustained downside risk."
        )
    else:
        rationale = "Conditions do not support adjustment due to insufficient confidence or conflicting signals."

    return {
        "type": action_type,
        "magnitude": magnitude,
        "confidence": round(conf_score, 4),
        "rationale": rationale,
    }


def _decision_summary(recommended_action: Dict, mission_delta_summary: Dict, confidence: Dict, loe_summary: Dict) -> Dict:
    return {
        "recommended_action": str(recommended_action.get("type") or "hold"),
        "mission_delta": float(mission_delta_summary.get("delta") or 0.0),
        "confidence_score": float(confidence.get("score") or 0.0),
        "loe_rag": str(loe_summary.get("rag") or "amber").lower(),
    }


def _validate_and_correct_output(
    recommended_action: Dict,
    recommendations: List[Dict],
    mission_delta_summary: Dict,
    confidence: Dict,
    commander_narrative: str,
    loe_summary: Dict,
    signals: Dict,
    ranked_factors: List[Dict],
) -> Tuple[Dict, List[Dict], str]:
    corrected = dict(recommended_action)
    delta_pct = float(mission_delta_summary.get("delta_pct") or 0.0)
    score = float(confidence.get("score") or 0.0)

    expected_band = derive_confidence_band(score)
    if str(confidence.get("band") or "") != expected_band:
        confidence["band"] = expected_band

    expected_magnitude = _magnitude_from_delta(
        delta_pct=delta_pct,
        confidence_score=score,
        loe_summary=loe_summary,
        degraded_factor_count=_count_degraded_causal_factors(ranked_factors),
        agreement_score=float(confidence.get("agreement") or 0.0),
        action_type=str(corrected.get("type") or "hold"),
    )
    corrected["magnitude"] = expected_magnitude

    action_type = str(corrected.get("type") or "hold")
    if action_type == "increase" and delta_pct <= 0:
        corrected["type"] = "hold"
    elif action_type == "decrease" and delta_pct >= 0:
        corrected["type"] = "hold"

    # Ensure recommendation language does not contradict HOLD.
    corrected_recs: List[Dict] = []
    for rec in recommendations:
        n = dict(rec)
        if str(corrected.get("type") or "hold") == "hold" and "increase" in str(n.get("title") or "").lower():
            n["title"] = n["title"].replace("increase", "stabilize")
        corrected_recs.append(n)

    if f"Recommendation: {corrected.get('type', 'hold')}" not in commander_narrative:
        commander_narrative = generate_commander_narrative(
            mission_delta_pct=delta_pct,
            factors=ranked_factors,
            recommended_action=corrected,
            loe_summary=loe_summary,
            confidence=confidence,
            accountability_brief={"classification": "insufficient_data"},
        )

    return corrected, corrected_recs, commander_narrative


def _targeting_shift_recommendation(signals: Dict, owner_level: str) -> Dict:
    targeting_raw = signals["targeting"]["raw"] or {}
    recs = list((targeting_raw.get("recommendations") or []))
    if not recs:
        recs = [
            {
                "station_rsid": x.get("station_rsid"),
                "zip_code": x.get("zip"),
                "priority_score": round(float(x.get("priority_score") or 0.0) * 100.0, 2),
                "warning_severity": 0.0,
            }
            for x in ((targeting_raw.get("targeting_engine") or {}).get("prioritized_targets") or [])
        ]
    if not recs:
        return {
            "type": "targeting_shift",
            "priority": 2,
            "title": f"{owner_level} establish priority targeting coverage",
            "owner_level": owner_level,
            "action": "Establish targeting coverage for the top five priority schools within the area of operations.",
            "expected_effect": "Improves access depth and enables higher-confidence mission adjustments in the next cycle.",
            "time_horizon": "next 14 days",
            "rationale": "Current targeting coverage is insufficient to support a high-confidence mission adjustment.",
            "linked_factors": ["school_access", "market_capability"],
            "source": "targeting_expansion",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "actions": [
                "Assign ownership for school outreach by station and company.",
                "Publish weekly targeting coverage updates in command sync.",
            ],
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
        "title": f"{owner_level} shift effort to station {top.get('station_rsid', 'unknown')} ZIP {top.get('zip_code', 'unknown')}",
        "owner_level": owner_level,
        "action": f"Reallocate prospecting and school engagement effort to station {top.get('station_rsid', 'unknown')} in ZIP {top.get('zip_code', 'unknown')} for the next 14 days.",
        "expected_effect": "Increases high-yield targeting coverage and improves conversion opportunity over the next reporting window.",
        "time_horizon": "next 14 days",
        "rationale": (
            f"Top priority_score={round(float(top.get('priority_score') or 0.0), 2)} with "
            f"warning_severity={round(float(top.get('warning_severity') or 0.0), 3)}"
        ),
        "linked_factors": ["school_access", "market_capability", "execution_stalls"],
        "source": "targeting_expansion",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "actions": [
            "Re-allocate recruiter effort blocks for next 14 days.",
            "Align outreach cadence with F3A cycle.",
            "Review conversion movement at weekly command sync.",
        ],
        "evidence_refs": [f"ev-targeting-{top.get('station_rsid', 'na')}-{top.get('zip_code', 'na')}"] ,
    }


def _school_plan_recommendation(signals: Dict, owner_level: str) -> Dict:
    raw = signals["school_plan"]["raw"] or {}
    plan = ((raw.get("school_plan_engine") or {}).get("school_recruiting_plan") or [])
    if not plan:
        return {
            "type": "school_plan_action",
            "priority": 3,
            "title": f"{owner_level} confirm school recruiting action owners",
            "owner_level": owner_level,
            "action": "No school plan actions are currently available. Validate school and contact data for this scope.",
            "expected_effect": "Restores reliable school planning signals for next mission cycle.",
            "time_horizon": "next command cycle",
            "rationale": "school_plan_engine returned no actionable rows for this scope.",
            "linked_factors": ["school_plan_gap", "school_access"],
            "source": "school_plan_engine",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "actions": [
                "Validate schools dataset mapping for the scope.",
                "Confirm active school contacts ingestion for all stations.",
            ],
            "evidence_refs": ["ev-school_plan"],
        }

    top = plan[0]
    return {
        "type": "school_plan_action",
        "priority": 2,
        "title": f"{owner_level} execute top school recruiting action",
        "owner_level": owner_level,
        "action": top.get("action"),
        "expected_effect": top.get("expected_effect"),
        "time_horizon": top.get("time_horizon") or "next 14 days",
        "rationale": top.get("rationale") or "Top prioritized school action from school_plan_engine.",
        "linked_factors": ["school_plan_gap", "funnel_health", "school_access"],
        "source": "school_plan_engine",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "actions": [top.get("action")],
        "evidence_refs": ["ev-school_plan", top.get("trace_id") or "ev-school_plan-top"],
    }


def _roi_recommendation(signals: Dict, owner_level: str) -> Dict:
    raw = signals.get("roi", {}).get("raw") or {}
    roi_recs = ((raw.get("roi_engine") or {}).get("roi_recommendations") or [])
    roi_sum = (signals.get("roi", {}).get("summary")) or {}
    low_count = int(roi_sum.get("low_effectiveness_count") or 0)
    total = int(roi_sum.get("total_events_scored") or 0)

    if not roi_recs or total == 0:
        return {
            "type": "roi_action",
            "priority": 3,
            "title": f"{owner_level} ensure event cost and lead data linkage",
            "owner_level": owner_level,
            "action": "No ROI-scored events available. Ensure spend_fact and lead_journey_fact rows are linked by event_id.",
            "expected_effect": "Enables ROI effectiveness analysis for all events.",
            "time_horizon": "next command cycle",
            "rationale": "roi_engine returned no scored events for this scope.",
            "linked_factors": ["roi_effectiveness"],
            "source": "roi_engine",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "actions": [
                "Link event costs to spend_fact.event_id.",
                "Link leads and contracts to lead_journey_fact.event_id.",
            ],
            "evidence_refs": ["ev-roi"],
        }

    top = roi_recs[0]
    return {
        "type": "roi_action",
        "priority": 2,
        "title": f"{owner_level} execute top ROI effectiveness action",
        "owner_level": owner_level,
        "action": top.get("action"),
        "expected_effect": top.get("expected_effect"),
        "time_horizon": top.get("time_horizon") or "next 30 days",
        "rationale": top.get("rationale") or (
            f"{low_count} of {total} events scored low ROI effectiveness."
        ),
        "linked_factors": ["roi_effectiveness", "funnel_health"],
        "source": "roi_engine",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "actions": [top.get("action")],
        "evidence_refs": ["ev-roi", top.get("trace_id") or "ev-roi-top"],
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
    recommended_action: Dict,
    loe_summary: Dict,
    confidence: Dict,
    accountability_brief: Dict,
) -> str:
    top_labels = [str(f.get("label") or "") for f in factors[:3] if str(f.get("label") or "").strip()]
    while len(top_labels) < 3:
        top_labels.append("cross-signal conditions")

    delta = float(mission_delta_pct or 0.0)
    loe_rag = str(loe_summary.get("rag") or "amber").upper()
    action_type = str(recommended_action.get("type") or "hold")
    confidence_band = str(confidence.get("band") or "low").upper()
    accountability_class = str(accountability_brief.get("classification") or "insufficient_data").replace("_", " ")

    if delta > 0.05:
        s1 = "Current mission performance is running above baseline in the current operating window."
    elif delta < -0.05:
        s1 = "Current mission performance is running below baseline in the current operating window."
    else:
        s1 = "Current mission performance is near baseline and operating within a narrow variance band."

    s2 = f"Primary drivers are {top_labels[0]}, {top_labels[1]}, and {top_labels[2]}."
    s3 = f"Current risk to sustained mission and next-cycle production is {loe_rag.lower()} with accountability assessed as {accountability_class}."
    s4 = f"Recommendation: {action_type} mission output at {recommended_action.get('magnitude', 'minor')} magnitude with {confidence_band.lower()} confidence."

    sentences = [s1, s2, s3, s4]
    if action_type == "hold":
        sentences.append("If access and execution indicators improve over the next cycle, reassess for a controlled increase.")

    return " ".join(sentences[:5])


def _build_one_slide_payload(
    decision_summary: Dict,
    executive_summary: List[str],
    commander_narrative: str,
    confidence_explanation: str,
    mission_delta_summary: Dict,
    factors: List[Dict],
    recommendations: List[Dict],
    accountability_brief: Dict,
    loe_summary: Dict,
    confidence: Dict,
    assumptions_and_limits: List[str],
) -> Dict:
    return {
        "title": "Mission Adjustment Justification",
        "decision_summary": decision_summary,
        "executive_summary": executive_summary,
        "commander_narrative": commander_narrative,
        "mission_delta": mission_delta_summary,
        "causal_factors": [
            {
                "label": f.get("label"),
                "code": f.get("factor_id"),
                "impact": f.get("impact"),
                "weighted_score": f.get("weighted_score"),
                "rationale": f.get("rationale"),
            }
            for f in factors[:5]
        ],
        "recommendations": recommendations,
        "accountability_brief": accountability_brief,
        "loe_summary": loe_summary,
        "confidence": confidence,
        "confidence_explanation": confidence_explanation,
        "assumptions_and_limits": assumptions_and_limits,
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

    for key in ("market", "access", "execution", "funnel", "accountability", "loe", "targeting", "school_plan", "roi", "twg"):
        sig = signals.get(key) or {}
        evidence.append(
            {
                "evidence_id": f"ev-{key}",
                "trace_id": f"{request_id}:{key}",
                "source": key,
                "fields": sig.get("summary") or {},
                "timestamp": sig.get("data_as_of") or datetime.utcnow().isoformat() + "Z",
            }
        )

    if not ((((signals["targeting"]["raw"] or {}).get("targeting_engine") or {}).get("prioritized_targets") or [])):
        evidence.append(
            {
                "evidence_id": "ev-targeting-empty",
                "trace_id": f"{request_id}:targeting:empty",
                "source": "targeting",
                "fields": {"message": "Targeting coverage dataset is currently sparse"},
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

    owner_level = _infer_owner_level(scope_type)
    targeting_recommendation = _targeting_shift_recommendation(signals, owner_level)
    school_plan_recommendation = _school_plan_recommendation(signals, owner_level)
    roi_recommendation = _roi_recommendation(signals, owner_level)
    accountability_brief = _build_accountability_brief(scope_type, scope_value, signals)
    loe_summary = _build_loe_summary(signals)
    confidence, recency_signal = _compute_confidence(
        ranked_factors,
        signals,
        mission_has_data=(mission_current.total is not None and mission_baseline.total is not None),
    )
    degraded_factor_count = _count_degraded_causal_factors(ranked_factors)
    confidence_explanation = _build_confidence_explanation(confidence, recency_signal, degraded_factor_count)

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

    recommended_action = _derive_recommended_action(
        mission_delta_pct=mission_delta_pct,
        loe_summary=loe_summary,
        signals=signals,
        confidence=confidence,
        ranked_factors=ranked_factors,
    )
    decision_summary = _decision_summary(recommended_action, mission_delta_summary, confidence, loe_summary)

    executive_summary = _generate_executive_summary(mission_delta_pct, ranked_factors, loe_summary, confidence)
    executive_summary.append(
        f"Recommended action: {recommended_action.get('type', 'hold').upper()} ({recommended_action.get('magnitude', 'minor')})."
    )
    commander_narrative = generate_commander_narrative(
        mission_delta_pct=mission_delta_pct,
        factors=ranked_factors,
        recommended_action=recommended_action,
        loe_summary=loe_summary,
        confidence=confidence,
        accountability_brief=accountability_brief,
    )

    evidence = _build_evidence_list(request_id, signals, mission_current, mission_baseline, include_evidence)

    recommendations = [
        {
            **targeting_recommendation,
            "recommendation_id": f"rec-{request_id}-targeting",
            "trace_id": f"{request_id}:recommendation:targeting",
            "kind": "targeting_shift",
        },
        {
            **school_plan_recommendation,
            "recommendation_id": f"rec-{request_id}-school-plan",
            "trace_id": f"{request_id}:recommendation:school-plan",
            "kind": "school_plan_action",
        },
        {
            **roi_recommendation,
            "recommendation_id": f"rec-{request_id}-roi",
            "trace_id": f"{request_id}:recommendation:roi",
            "kind": "roi_action",
        },
        {
            "recommendation_id": f"rec-{request_id}-accountability",
            "trace_id": f"{request_id}:recommendation:accountability",
            "kind": "accountability_action",
            "priority": 2,
            "title": f"{owner_level} execute accountability recovery actions",
            "owner_level": owner_level,
            "action": "Assign owners to overdue accountability actions and close execution gaps in the next command cycle.",
            "expected_effect": "Reduces execution risk and improves accountability signal quality for the next mission adjustment decision.",
            "time_horizon": "next command cycle",
            "rationale": (
                f"classification={accountability_brief.get('classification')} "
                f"overdue={len(accountability_brief.get('overdue_items') or [])}"
            ),
            "linked_factors": ["accountability_classification", "execution_stalls"],
            "source": "accountability_engine",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "actions": accountability_brief.get("overdue_items") or ["Validate accountability inputs and owners."],
            "evidence_refs": ["ev-accountability"],
        },
    ]

    recommended_action, recommendations, commander_narrative = _validate_and_correct_output(
        recommended_action=recommended_action,
        recommendations=recommendations,
        mission_delta_summary=mission_delta_summary,
        confidence=confidence,
        commander_narrative=commander_narrative,
        loe_summary=loe_summary,
        signals=signals,
        ranked_factors=ranked_factors,
    )

    assumptions_and_limits = [
        "Mission delta is derived from fact_production totals for the requested and baseline windows.",
        "Signals without active datasets are treated as neutral and surfaced in evidence.",
        "Causal factors are synthesized from existing engines and do not represent a causal proof model.",
        "Deterministic sorting uses weighted_score desc then factor code asc.",
    ]

    output = {
        "request_id": request_id,
        "traceability_id": f"trace-{request_id}",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "decision_output_name": "mission_adjustment_justification",
        "mission_adjustment_type": "mission_adjustment",
        "scope": {"scope_type": scope_type, "scope_value": scope_value},
        "mission_delta_summary": mission_delta_summary,
        "decision_summary": decision_summary,
        "recommended_action": recommended_action,
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
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            for idx, f in enumerate(ranked_factors)
        ],
        "recommendations": recommendations,
        "accountability_brief": accountability_brief,
        "loe_summary": loe_summary,
        "confidence": confidence,
        "confidence_explanation": confidence_explanation,
        "executive_summary": executive_summary,
        "commander_narrative": commander_narrative,
        "one_slide_payload": _build_one_slide_payload(
            decision_summary,
            executive_summary,
            commander_narrative,
            confidence_explanation,
            mission_delta_summary,
            ranked_factors,
            recommendations,
            accountability_brief,
            loe_summary,
            confidence,
            assumptions_and_limits,
        ),
        "assumptions_and_limits": assumptions_and_limits,
        "signal_summaries": {
            "market": {
                "status": signals.get("market", {}).get("raw", {}).get("status"),
                "source_dataset_name": signals.get("market", {}).get("source_dataset_name"),
                "rows_used": signals.get("market", {}).get("rows_used"),
                "summary": signals.get("market", {}).get("summary") or {},
            },
            "school_access": {
                "status": signals.get("access", {}).get("raw", {}).get("status"),
                "source_dataset_name": signals.get("access", {}).get("source_dataset_name"),
                "rows_used": signals.get("access", {}).get("rows_used"),
                "summary": signals.get("access", {}).get("summary") or {},
            },
            "funnel": {
                "status": signals.get("funnel", {}).get("raw", {}).get("status"),
                "source_dataset_name": signals.get("funnel", {}).get("source_dataset_name"),
                "rows_used": signals.get("funnel", {}).get("rows_used"),
                "summary": signals.get("funnel", {}).get("summary") or {},
            },
            "targeting": {
                "status": "ok",
                "source_dataset_name": signals.get("targeting", {}).get("source_dataset_name"),
                "rows_used": signals.get("targeting", {}).get("rows_used"),
                "summary": signals.get("targeting", {}).get("summary") or {},
            },
            "school_plan": {
                "status": signals.get("school_plan", {}).get("raw", {}).get("status"),
                "source_dataset_name": signals.get("school_plan", {}).get("source_dataset_name"),
                "rows_used": signals.get("school_plan", {}).get("rows_used"),
                "summary": signals.get("school_plan", {}).get("summary") or {},
            },
            "roi": {
                "status": signals.get("roi", {}).get("raw", {}).get("status"),
                "rows_used": signals.get("roi", {}).get("rows_used"),
                "summary": signals.get("roi", {}).get("summary") or {},
            },
            "twg": {
                "status": signals.get("twg", {}).get("raw", {}).get("status"),
                "rows_used": signals.get("twg", {}).get("rows_used"),
                "summary": signals.get("twg", {}).get("summary") or {},
            },
        },
        "evidence": evidence,
        "force_refresh_used": bool(force_refresh),
    }

    _cache_put(request_id, output)
    return output


def generate_mission_adjustment_justification(
    db,
    org_id: str,
    period_start: date,
    period_end: date,
    baseline_start: Optional[date] = None,
    baseline_end: Optional[date] = None,
    include_evidence: bool = True,
    force_refresh: bool = False,
) -> Dict:
    # Compatibility wrapper: route and legacy callers can continue to use the
    # mission-decrease function while output semantics are generalized.
    return generate_mission_decrease_justification(
        db=db,
        org_id=org_id,
        period_start=period_start,
        period_end=period_end,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
        include_evidence=include_evidence,
        force_refresh=force_refresh,
    )
