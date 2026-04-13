from datetime import datetime
from typing import Dict, List, Optional

from starlette.exceptions import HTTPException

from services.api.app.services import (
    accountability_engine,
    funnel_engine,
    loe_engine,
    market_engine,
    roi_engine,
    school_plan_engine,
    targeting_engine,
)

WEIGHT_MARKET_ISSUE = 0.25
WEIGHT_FUNNEL_ISSUE = 0.20
WEIGHT_TARGETING_ISSUE = 0.20
WEIGHT_SCHOOL_ISSUE = 0.15
WEIGHT_ROI_ISSUE = 0.10
WEIGHT_MISSION_RISK = 0.10

HIGH_PRIORITY_THRESHOLD = 70.0
MEDIUM_PRIORITY_THRESHOLD = 40.0


def _scope_prefix(scope_type: str, scope_value: str) -> str:
    st = (scope_type or "").upper().strip()
    sv = (scope_value or "").strip().upper()
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


def enforce_scope(
    actor_scope_type: str,
    actor_scope_value: str,
    request_scope_type: str,
    request_scope_value: str,
) -> None:
    a_type = (actor_scope_type or "USAREC").upper().strip()
    r_type = (request_scope_type or "USAREC").upper().strip()
    a_val = (actor_scope_value or "USAREC").strip().upper()
    r_val = (request_scope_value or "USAREC").strip().upper()

    if a_type == "USAREC":
        return
    if r_type == "USAREC":
        raise HTTPException(status_code=403, detail="requested scope outside user permissions")

    a_prefix = _scope_prefix(a_type, a_val)
    r_prefix = _scope_prefix(r_type, r_val)
    if a_prefix and not r_prefix.startswith(a_prefix):
        raise HTTPException(status_code=403, detail="requested scope outside user permissions")


def _clamp100(v: Optional[float]) -> float:
    if v is None:
        return 0.0
    try:
        f = float(v)
    except Exception:
        return 0.0
    if f < 0:
        return 0.0
    if f > 100:
        return 100.0
    return f


def _priority_score(
    market_issue_weight: float,
    funnel_issue_weight: float,
    targeting_issue_weight: float,
    school_issue_weight: float,
    roi_issue_weight: float,
    mission_risk_weight: float,
) -> float:
    return round(
        WEIGHT_MARKET_ISSUE * _clamp100(market_issue_weight)
        + WEIGHT_FUNNEL_ISSUE * _clamp100(funnel_issue_weight)
        + WEIGHT_TARGETING_ISSUE * _clamp100(targeting_issue_weight)
        + WEIGHT_SCHOOL_ISSUE * _clamp100(school_issue_weight)
        + WEIGHT_ROI_ISSUE * _clamp100(roi_issue_weight)
        + WEIGHT_MISSION_RISK * _clamp100(mission_risk_weight),
        4,
    )


def _priority_band(score: float) -> str:
    if score >= HIGH_PRIORITY_THRESHOLD:
        return "high"
    if score >= MEDIUM_PRIORITY_THRESHOLD:
        return "medium"
    return "low"


def _owner_level(scope_type: str, station_rsid: str = "") -> str:
    if station_rsid:
        return "STN"
    st = (scope_type or "").upper().strip()
    if st in {"USAREC", "BDE", "BN"}:
        return "BN"
    if st == "CO":
        return "CO"
    return "STN"


def _due_out_for_band(priority_band: str) -> str:
    if priority_band == "high":
        return "within 7 days"
    if priority_band == "medium":
        return "within 14 days"
    return "within 21 days"


def _board_elevation_recommended(
    priority_band: str,
    cross_signal_count: int,
    category: str,
    recommended_action: str,
) -> bool:
    if priority_band != "high":
        return False
    action = (recommended_action or "").lower()
    needs_tradeoff = any(k in action for k in ["reallocate", "shift", "stop", "pause", "resource"])
    if cross_signal_count >= 2 and (needs_tradeoff or category in {"mission", "roi"}):
        return True
    return False


def _overall_twg_status(high_count: int, medium_count: int, total_items: int) -> str:
    if total_items <= 0:
        return "unknown"
    if high_count >= 2:
        return "critical"
    if high_count >= 1 or medium_count >= 2:
        return "watch"
    return "stable"


def _engine_status(v: Dict) -> str:
    return str((v or {}).get("status") or "unknown")


def summarize_twg_engine(
    db,
    scope_type: str,
    scope_value: str,
    actor_scope_type: str = "USAREC",
    actor_scope_value: str = "USAREC",
    top_n: int = 12,
) -> Dict:
    enforce_scope(actor_scope_type, actor_scope_value, scope_type, scope_value)

    market = market_engine.summarize_market_engine(db, scope_type, scope_value, actor_scope_type, actor_scope_value, top_n=25)
    funnel = funnel_engine.summarize_funnel_engine(db, scope_type, scope_value, actor_scope_type, actor_scope_value, top_n=25)
    targeting = targeting_engine.summarize_targeting_engine(db, scope_type, scope_value, actor_scope_type, actor_scope_value, top_n=25)
    school_plan = school_plan_engine.summarize_school_plan_engine(db, scope_type, scope_value, actor_scope_type, actor_scope_value, top_n=25)
    roi = roi_engine.summarize_roi_engine(db, scope_type, scope_value, actor_scope_type, actor_scope_value, top_n=25)
    accountability = accountability_engine.classify_scope(db, scope_type, scope_value)
    loe = loe_engine.summarize_loes(db, scope_type, scope_value)

    data_sources = {
        "market": ((market.get("market_engine") or {}).get("source_dataset_name")),
        "funnel": ((funnel.get("funnel_engine") or {}).get("source_dataset_name")),
        "targeting": (((targeting.get("targeting_engine") or {}).get("data_sources") or {}).get("market")),
        "school_plan": ((school_plan.get("school_plan_engine") or {}).get("source_school_dataset")),
        "roi": "emm_event/spend_fact/lead_journey_fact",
        "mission_adjustment": "derived_from_accountability_and_loe",
    }

    invalid_statuses = {
        _engine_status(market),
        _engine_status(funnel),
        _engine_status(targeting),
        _engine_status(school_plan),
        _engine_status(roi),
    }

    items: List[Dict] = []

    def add_item(
        *,
        category: str,
        title: str,
        market_issue_weight: float,
        funnel_issue_weight: float,
        targeting_issue_weight: float,
        school_issue_weight: float,
        roi_issue_weight: float,
        mission_risk_weight: float,
        owner_level: str,
        recommended_action: str,
        expected_effect: str,
        rationale: str,
        source_engine: str,
        trace_id: str,
        cross_signal_count: int,
    ) -> None:
        score = _priority_score(
            market_issue_weight=market_issue_weight,
            funnel_issue_weight=funnel_issue_weight,
            targeting_issue_weight=targeting_issue_weight,
            school_issue_weight=school_issue_weight,
            roi_issue_weight=roi_issue_weight,
            mission_risk_weight=mission_risk_weight,
        )
        band = _priority_band(score)
        due_out = _due_out_for_band(band)
        board_flag = _board_elevation_recommended(band, cross_signal_count, category, recommended_action)
        item_id = f"twg-{category}-{len(items) + 1:03d}"

        items.append(
            {
                "item_id": item_id,
                "category": category,
                "title": title,
                "priority_score": score,
                "priority_band": band,
                "owner_level": owner_level,
                "recommended_action": recommended_action,
                "due_out": due_out,
                "expected_effect": expected_effect,
                "board_elevation_recommended": board_flag,
                "rationale": rationale,
                "source_engine": source_engine,
                "trace_id": trace_id,
            }
        )

    market_summary = ((market.get("market_engine") or {}).get("summary") or {})
    market_gaps = ((market.get("market_engine") or {}).get("top_market_gaps") or [])
    funnel_summary = ((funnel.get("funnel_engine") or {}).get("summary") or {})
    funnel_gaps = ((funnel.get("funnel_engine") or {}).get("prioritized_funnel_gaps") or [])
    targeting_summary = ((targeting.get("targeting_engine") or {}).get("summary") or {})
    targeting_rows = ((targeting.get("targeting_engine") or {}).get("prioritized_targets") or [])
    school_summary = ((school_plan.get("school_plan_engine") or {}).get("summary") or {})
    school_rows = ((school_plan.get("school_plan_engine") or {}).get("prioritized_schools") or [])
    roi_summary = ((roi.get("roi_engine") or {}).get("summary") or {})
    roi_rows = ((roi.get("roi_engine") or {}).get("prioritized_events") or [])

    # Market issue
    if _engine_status(market) == "ok" and (market_gaps or str(market_summary.get("overall_market_status") or "") in {"weak", "market_constrained"}):
        top_gap = market_gaps[0] if market_gaps else {}
        weak_count = int(market_summary.get("weak_opportunity_zip_count") or 0)
        top_station = str(top_gap.get("station_rsid") or "")
        add_item(
            category="market",
            title=f"Weak market support in priority area {str(top_gap.get('zip') or 'unknown')}",
            market_issue_weight=min(100.0, 55.0 + weak_count * 8.0),
            funnel_issue_weight=30.0 if str(funnel_summary.get("overall_funnel_status") or "") in {"watch", "critical"} else 10.0,
            targeting_issue_weight=35.0 if int(targeting_summary.get("high_priority_count") or 0) > 0 else 15.0,
            school_issue_weight=20.0,
            roi_issue_weight=10.0,
            mission_risk_weight=25.0,
            owner_level=_owner_level(scope_type, top_station),
            recommended_action="CO shift recruiter effort to top market-opportunity ZIP cluster within 14 days.",
            expected_effect="Improves coverage in addressable market terrain and reduces opportunity loss.",
            rationale=(
                f"overall_market_status={market_summary.get('overall_market_status')}, "
                f"weak_opportunity_zip_count={weak_count}, gap_zip={top_gap.get('zip')}"
            ),
            source_engine="market_engine",
            trace_id=str(top_gap.get("trace_id") or "twg:market"),
            cross_signal_count=2,
        )

    # Funnel issue
    if _engine_status(funnel) == "ok" and funnel_gaps:
        top_gap = funnel_gaps[0]
        stn = str(top_gap.get("station_rsid") or "")
        add_item(
            category="funnel",
            title=f"Severe funnel dropoff at stage {str(top_gap.get('stage') or 'unknown')}",
            market_issue_weight=55.0,
            funnel_issue_weight=min(100.0, 70.0 + float(top_gap.get("priority_score") or 0.0) * 0.3),
            targeting_issue_weight=75.0,
            school_issue_weight=60.0,
            roi_issue_weight=55.0,
            mission_risk_weight=80.0,
            owner_level=_owner_level(scope_type, stn),
            recommended_action="BN validate weak funnel stage at top 3 stations within 7 days.",
            expected_effect="Improves lead-to-contract conversion and protects mission attainment.",
            rationale=(
                f"overall_funnel_status={funnel_summary.get('overall_funnel_status')}, "
                f"stage={top_gap.get('stage')}, dropoff_count={top_gap.get('dropoff_count')}"
            ),
            source_engine="funnel_engine",
            trace_id=str(top_gap.get("trace_id") or f"twg:funnel:{stn}"),
            cross_signal_count=3,
        )

    # Targeting issue
    if _engine_status(targeting) == "ok" and targeting_rows:
        top = targeting_rows[0]
        stn = str(top.get("station_rsid") or "")
        zc = str(top.get("zip") or "unknown")
        priority_raw = float(top.get("priority_score") or 0.0) * 100.0
        add_item(
            category="targeting",
            title=f"High-priority ZIP {zc} lacks aligned effort",
            market_issue_weight=30.0,
            funnel_issue_weight=30.0,
            targeting_issue_weight=max(45.0, min(100.0, priority_raw)),
            school_issue_weight=25.0,
            roi_issue_weight=20.0,
            mission_risk_weight=30.0,
            owner_level=_owner_level(scope_type, stn),
            recommended_action="CO shift recruiter effort to top-priority ZIP cluster within 14 days.",
            expected_effect="Improves targeting coverage in highest-yield ZIP terrain.",
            rationale=(
                f"high_priority_count={targeting_summary.get('high_priority_count')}, "
                f"top_station={stn}, zip={zc}, priority_score={round(priority_raw, 2)}"
            ),
            source_engine="targeting_engine",
            trace_id=str(top.get("trace_id") or f"twg:targeting:{stn}:{zc}"),
            cross_signal_count=2,
        )

    # School issue
    if _engine_status(school_plan) == "ok" and school_rows:
        top = school_rows[0]
        stn = str(top.get("station_rsid") or "")
        school_priority = float(top.get("priority_score") or 0.0)
        underengaged = int(school_summary.get("underengaged_school_count") or 0)
        add_item(
            category="school",
            title=f"Underengaged high-opportunity school {str(top.get('school_name') or top.get('school_id') or 'unknown')}",
            market_issue_weight=25.0,
            funnel_issue_weight=25.0,
            targeting_issue_weight=20.0,
            school_issue_weight=max(45.0, min(100.0, school_priority)),
            roi_issue_weight=10.0,
            mission_risk_weight=25.0,
            owner_level=_owner_level(scope_type, stn),
            recommended_action="STN increase school engagement cadence at underpenetrated priority schools within 10 days.",
            expected_effect="Raises school engagement depth and supports funnel replenishment.",
            rationale=(
                f"underengaged_school_count={underengaged}, top_priority_score={round(school_priority,2)}, "
                f"station={stn}"
            ),
            source_engine="school_plan_engine",
            trace_id=str(top.get("trace_id") or f"twg:school:{stn}"),
            cross_signal_count=2,
        )

    # ROI issue
    if _engine_status(roi) == "ok" and int(roi_summary.get("total_events_scored") or 0) > 0:
        low_count = int(roi_summary.get("low_effectiveness_count") or 0)
        total_events = int(roi_summary.get("total_events_scored") or 1)
        if low_count > 0:
            low_rows = [r for r in roi_rows if str(r.get("effectiveness_band") or "") == "low"]
            target = sorted(low_rows, key=lambda x: (float(x.get("roi_score") or 0.0), str(x.get("event_id") or "")))[0] if low_rows else roi_rows[-1]
            stn = str(target.get("unit_rsid") or "")
            roi_ratio = 100.0 * float(low_count) / float(max(1, total_events))
            add_item(
                category="roi",
                title=f"Low-value event format consuming effort: {str(target.get('event_name') or target.get('event_id') or 'unknown')}",
                market_issue_weight=65.0,
                funnel_issue_weight=85.0,
                targeting_issue_weight=70.0,
                school_issue_weight=60.0,
                roi_issue_weight=max(70.0, min(100.0, roi_ratio + 35.0)),
                mission_risk_weight=85.0,
                owner_level=_owner_level(scope_type, stn),
                recommended_action="BN review low-ROI event formats and stop ineffective event types before next cycle.",
                expected_effect="Reduces wasted effort and reallocates capacity to higher-yield actions.",
                rationale=(
                    f"low_effectiveness_count={low_count}, total_events_scored={total_events}, "
                    f"event_roi_score={target.get('roi_score')}"
                ),
                source_engine="roi_engine",
                trace_id=str(target.get("trace_id") or f"twg:roi:{stn}"),
                cross_signal_count=3,
            )

    # Mission risk issue from accountability + LOE
    loe_counts = (loe.get("status_counts") or {}) if isinstance(loe, dict) else {}
    loe_total = int(loe.get("total_metrics") or 0) if isinstance(loe, dict) else 0
    loe_risk_ratio = 0.0
    if loe_total > 0:
        loe_risk_ratio = float(int(loe_counts.get("at_risk") or 0) + int(loe_counts.get("not_met") or 0)) / float(loe_total)

    acc_class = str((accountability or {}).get("classification") or "insufficient_data")
    if acc_class in {"execution_failure", "effort_misaligned", "access_constrained", "market_constrained"} or loe_risk_ratio >= 0.40:
        add_item(
            category="mission",
            title="Mission feasibility risk requires coordinated corrective action",
            market_issue_weight=60.0 if acc_class in {"market_constrained"} else 45.0,
            funnel_issue_weight=80.0,
            targeting_issue_weight=70.0,
            school_issue_weight=60.0,
            roi_issue_weight=70.0,
            mission_risk_weight=max(80.0, min(100.0, loe_risk_ratio * 100.0 + 30.0)),
            owner_level=_owner_level(scope_type),
            recommended_action="BN review mission risk concentration and approve cross-station corrective due-outs within 7 days.",
            expected_effect="Reduces mission degradation risk through synchronized corrective actions.",
            rationale=(
                f"accountability_classification={acc_class}, "
                f"loe_at_risk_ratio={round(loe_risk_ratio, 4)}"
            ),
            source_engine="accountability_engine",
            trace_id=f"twg:mission:{scope_type}:{scope_value}",
            cross_signal_count=3,
        )

    if not items:
        if "invalid" in invalid_statuses or "invalid_dataset_schema" in invalid_statuses:
            return {
                "status": "invalid",
                "twg_engine": {
                    "summary": {
                        "total_items": 0,
                        "high_priority_count": 0,
                        "medium_priority_count": 0,
                        "low_priority_count": 0,
                        "board_elevation_count": 0,
                        "overall_twg_status": "unknown",
                    },
                    "prioritized_items": [],
                    "twg_agenda": [],
                    "due_outs": [],
                    "board_candidates": [],
                    "data_sources": data_sources,
                },
            }
        return {
            "status": "no_data",
            "twg_engine": {
                "summary": {
                    "total_items": 0,
                    "high_priority_count": 0,
                    "medium_priority_count": 0,
                    "low_priority_count": 0,
                    "board_elevation_count": 0,
                    "overall_twg_status": "unknown",
                },
                "prioritized_items": [],
                "twg_agenda": [],
                "due_outs": [],
                "board_candidates": [],
                "data_sources": data_sources,
            },
        }

    items.sort(
        key=lambda x: (
            -float(x.get("priority_score") or 0.0),
            str(x.get("category") or ""),
            str(x.get("title") or ""),
            str(x.get("item_id") or ""),
        )
    )
    prioritized_items = items[:top_n]

    twg_agenda = [
        {
            "sequence": idx + 1,
            "title": str(i.get("title") or ""),
            "category": str(i.get("category") or ""),
            "owner_level": str(i.get("owner_level") or ""),
            "decision_required": str(i.get("recommended_action") or ""),
            "rationale": str(i.get("rationale") or ""),
            "trace_id": str(i.get("trace_id") or ""),
        }
        for idx, i in enumerate(prioritized_items)
    ]

    due_outs = [
        {
            "item_id": str(i.get("item_id") or ""),
            "owner_level": str(i.get("owner_level") or ""),
            "action": str(i.get("recommended_action") or ""),
            "due_out": str(i.get("due_out") or ""),
            "expected_effect": str(i.get("expected_effect") or ""),
            "trace_id": str(i.get("trace_id") or ""),
        }
        for i in prioritized_items
    ]

    board_candidates = [
        {
            "item_id": str(i.get("item_id") or ""),
            "category": str(i.get("category") or ""),
            "title": str(i.get("title") or ""),
            "priority_score": float(i.get("priority_score") or 0.0),
            "owner_level": str(i.get("owner_level") or ""),
            "recommended_action": str(i.get("recommended_action") or ""),
            "rationale": str(i.get("rationale") or ""),
            "source_engine": str(i.get("source_engine") or ""),
            "trace_id": str(i.get("trace_id") or ""),
        }
        for i in prioritized_items
        if bool(i.get("board_elevation_recommended"))
    ]

    high_count = sum(1 for i in prioritized_items if str(i.get("priority_band") or "") == "high")
    medium_count = sum(1 for i in prioritized_items if str(i.get("priority_band") or "") == "medium")
    low_count = sum(1 for i in prioritized_items if str(i.get("priority_band") or "") == "low")

    return {
        "status": "ok",
        "twg_engine": {
            "summary": {
                "total_items": len(prioritized_items),
                "high_priority_count": high_count,
                "medium_priority_count": medium_count,
                "low_priority_count": low_count,
                "board_elevation_count": len(board_candidates),
                "overall_twg_status": _overall_twg_status(high_count, medium_count, len(prioritized_items)),
            },
            "prioritized_items": prioritized_items,
            "twg_agenda": twg_agenda,
            "due_outs": due_outs,
            "board_candidates": board_candidates,
            "data_sources": data_sources,
            "data_as_of": datetime.utcnow().isoformat() + "Z",
        },
    }
