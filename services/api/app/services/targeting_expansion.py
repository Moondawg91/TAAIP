from typing import Dict, List, Optional

from sqlalchemy import text

from services.api.app import models
from services.api.app import models_domain as domain
from services.api.app.services import market_engine
from services.api.app.services import funnel_engine
from services.api.app.services import targeting_engine
from services.api.app.services import school_access
from services.api.app.services.market_targeting import (
    enrich_reason_codes_with_market,
    get_market_targeting_overlays,
)

REASON_CODES = {
    "high_opportunity_low_output",
    "high_burden_low_capacity",
    "strong_market_underworked",
    "low_effort_high_opportunity",
    "poor_execution_in_good_market",
    "high_qma_low_output",
    "weak_market_high_burden",
    "market_supports_shift",
}


def _clamp01(v: Optional[float]) -> float:
    if v is None:
        return 0.0
    if v < 0:
        return 0.0
    if v > 1:
        return 1.0
    return float(v)


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


def _load_weights(db) -> Dict[str, float]:
    out = {}
    try:
        rows = db.query(models.MarketCategoryWeights).all()
        for r in rows:
            k = r.category.name if hasattr(r.category, "name") else str(r.category)
            out[k] = float(r.weight)
        if out:
            return out
    except Exception:
        pass

    # Fallback for test/mixed schemas that don't match full ORM columns.
    try:
        cols = {str(r.get("name")) for r in db.execute(text("PRAGMA table_info('market_category_weights')")).mappings().all()}
        if not {"category", "weight"}.issubset(cols):
            return out
        rows = db.execute(text("SELECT category, weight FROM market_category_weights")).mappings().all()
        for r in rows:
            k = str(r.get("category") or "")
            if not k:
                continue
            out[k] = float(r.get("weight") or 0.0)
    except Exception:
        return out
    return out


def _latest_burden_by_scope(db, prefixes: List[str]) -> Dict[str, float]:
    out = {}
    order_col = None
    try:
        col_rows = db.execute(text("PRAGMA table_info('burden_snapshots')")).mappings().all()
        cols = {str(r.get("name")) for r in col_rows}
        if "reporting_date" in cols:
            order_col = domain.BurdenSnapshot.reporting_date
        elif "created_at" in cols:
            order_col = domain.BurdenSnapshot.created_at
    except Exception:
        order_col = None

    for p in prefixes:
        if not p:
            continue
        # Try exact station, then fallback to prefix scopes.
        try:
            q = db.query(domain.BurdenSnapshot).filter(domain.BurdenSnapshot.scope_value == p)
            if order_col is not None:
                q = q.order_by(order_col.desc())
            row = q.first()
        except Exception:
            row = None
        if row and row.burden_ratio is not None:
            out[p] = float(row.burden_ratio)
            continue

        try:
            fq = db.query(domain.BurdenSnapshot).filter(domain.BurdenSnapshot.scope_value.like(f"{p[:3]}%"))
            if order_col is not None:
                fq = fq.order_by(order_col.desc())
            fallback = fq.first()
        except Exception:
            fallback = None
        if fallback and fallback.burden_ratio is not None:
            out[p] = float(fallback.burden_ratio)
    return out


def _safe_table_exists(db, table_name: str) -> bool:
    q = text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n")
    return bool(db.execute(q, {"n": table_name}).first())


def _load_production_signal(db) -> Dict[str, float]:
    if not _safe_table_exists(db, "fact_production"):
        return {}

    sql = text(
        """
        SELECT org_unit_id, SUM(COALESCE(metric_value, 0.0)) AS production_value
        FROM fact_production
        WHERE record_status IS NULL OR record_status = 'active'
        GROUP BY org_unit_id
        """
    )
    rows = db.execute(sql).mappings().all()
    raw = {str(r["org_unit_id"]): float(r["production_value"] or 0.0) for r in rows if r.get("org_unit_id")}
    if not raw:
        return {}
    max_v = max(raw.values()) if raw else 1.0
    if max_v <= 0:
        max_v = 1.0
    return {k: _clamp01(v / max_v) for k, v in raw.items()}


def _load_effort_signal(db) -> Dict[str, float]:
    if not _safe_table_exists(db, "fact_marketing"):
        return {}

    sql = text(
        """
        SELECT org_unit_id,
               SUM(COALESCE(engagements, 0.0) + COALESCE(clicks, 0.0) + COALESCE(conversions, 0.0)) AS effort_value
        FROM fact_marketing
        WHERE record_status IS NULL OR record_status = 'active'
        GROUP BY org_unit_id
        """
    )
    rows = db.execute(sql).mappings().all()
    raw = {str(r["org_unit_id"]): float(r["effort_value"] or 0.0) for r in rows if r.get("org_unit_id")}
    if not raw:
        return {}
    max_v = max(raw.values()) if raw else 1.0
    if max_v <= 0:
        max_v = 1.0
    return {k: _clamp01(v / max_v) for k, v in raw.items()}


def _warning_severity(db, station_rsid: str) -> float:
    if not _safe_table_exists(db, "home_alerts"):
        return 0.0
    col_rows = db.execute(text("PRAGMA table_info(home_alerts)")).mappings().all()
    cols = {str(r.get("name")) for r in col_rows}

    if "scope_value" in cols:
        row = db.execute(
            text(
                """
                SELECT COUNT(1) AS c
                FROM home_alerts
                WHERE (record_status = 'active' OR record_status IS NULL)
                  AND (
                      scope_value = :sv OR
                      scope_value LIKE :co OR
                      scope_value LIKE :bn OR
                      scope_value LIKE :bde
                  )
                """
            ),
            {
                "sv": station_rsid,
                "co": f"{station_rsid[:3]}%",
                "bn": f"{station_rsid[:2]}%",
                "bde": f"{station_rsid[:1]}%",
            },
        ).mappings().first()
    else:
        # Fallback for schemas where alerts are global and not scope-tagged.
        row = db.execute(
            text(
                """
                SELECT COUNT(1) AS c
                FROM home_alerts
                WHERE record_status = 'active' OR record_status IS NULL
                """
            )
        ).mappings().first()
    count = float((row or {}).get("c") or 0.0)
    # Saturates at 5+ alerts.
    return _clamp01(count / 5.0)


def _reason_codes(opportunity: float, burden: float, production: float, effort: float) -> List[str]:
    reasons = []
    if opportunity >= 0.65 and production <= 0.40:
        reasons.append("high_opportunity_low_output")
    if burden >= 0.60 and production <= 0.50:
        reasons.append("high_burden_low_capacity")
    if opportunity >= 0.60 and effort <= 0.40:
        reasons.append("strong_market_underworked")
    if effort <= 0.35 and opportunity >= 0.55:
        reasons.append("low_effort_high_opportunity")
    if opportunity >= 0.60 and production <= 0.35 and burden <= 0.50:
        reasons.append("poor_execution_in_good_market")
    return reasons


def _targeting_guidance(market_category: str, opportunity: float, effort_signal: float) -> Dict:
    mc = (market_category or "UNK").upper()
    persona = "senior_high_school"
    message = "service_opportunity_and_stability"
    channel = "school_engagement"
    frequency = "weekly"
    content_format = "face_to_face_brief"

    if mc in {"MK", "MW"} and opportunity >= 0.65:
        persona = "high_propensity_youth"
        message = "career_path_and_benefits"
        channel = "social_plus_school"
        frequency = "2x_week"
        content_format = "short_video_plus_recruiter_followup"
    elif mc in {"MO", "SU"}:
        persona = "market_development_segment"
        message = "awareness_and_trust_building"
        channel = "community_event_plus_referral"
        frequency = "weekly"
        content_format = "community_story_format"

    if effort_signal < 0.35:
        frequency = "3x_week"

    return {
        "d3ae": {
            "decide": "prioritize_high_gap_zip",
            "detect": "monitor_school_access_and_market_gap",
            "deliver": "execute_targeted_outreach_package",
            "assess": "review_conversion_and_stage_velocity_weekly",
            "evaluate": "re-rank_zip_priority_and_adjust_loe",
        },
        "f3a": {
            "find": "identify_high_opportunity_segments",
            "fix": "assign_station_owner_and_campaign_window",
            "finish": "close_contact_to_contract_pipeline",
            "analyze": "inspect_stalls_and_conversion_leaks",
        },
        "who_to_target": persona,
        "theme_message": message,
        "method_channel": channel,
        "frequency": frequency,
        "content_format": content_format,
    }


def _school_signal(station_status: str, penetration_rate: float, zip_status: str) -> str:
    z = (zip_status or "").lower()
    s = (station_status or "").lower()
    p = float(penetration_rate or 0.0)
    if z in {"access_constrained", "underpenetrated"} or s in {"access_constrained", "constrained", "red"} or p < 0.5:
        return "constrained"
    if z in {"accessing_market", "supportive"} or s in {"accessing_market", "supportive", "green"} or p >= 0.5:
        return "supportive"
    return "unknown"


def _load_school_access_maps(db, scope_type: str, scope_value: str) -> Dict[str, Dict]:
    payload = school_access.summarize_school_access(
        db,
        scope_type=scope_type,
        scope_value=scope_value,
        actor_scope_type=scope_type,
        actor_scope_value=scope_value,
        top_n=500,
    )
    if payload.get("status") != "ok":
        return {"by_station": {}, "by_zip": {}}

    access = payload.get("school_access") or {}
    by_station_rows = ((access.get("by_scope") or {}).get("station") or [])
    by_station = {
        str(r.get("station_rsid") or ""): {
            "penetration_rate": float(r.get("penetration_rate") or 0.0),
            "access_status": str(r.get("access_status") or "unknown"),
            "contacts_count": int(r.get("contacts_count") or 0),
        }
        for r in by_station_rows
        if str(r.get("station_rsid") or "")
    }

    by_zip = {}
    for r in (access.get("top_access_gaps") or []):
        stn = str(r.get("station_rsid") or "")
        zc = str(r.get("zip_code") or "")
        if not stn or not zc:
            continue
        by_zip[f"{stn}:{zc}"] = {
            "access_classification": str(r.get("access_classification") or "unknown"),
            "access_gap_score": float(r.get("access_gap_score") or 0.0),
            "contacts_count": int(r.get("contacts_count") or 0),
            "contracts_count": int(r.get("contracts_count") or 0),
        }

    return {"by_station": by_station, "by_zip": by_zip}


def recommendations_for_scope(db, scope_type: str, scope_value: str, top_n: int = 20) -> Dict:
    payload = targeting_engine.summarize_targeting_engine(
        db,
        scope_type=scope_type,
        scope_value=scope_value,
        actor_scope_type=scope_type,
        actor_scope_value=scope_value,
        top_n=top_n,
    )
    engine = payload.get("targeting_engine") or {}
    prioritized_targets = engine.get("prioritized_targets") or []

    recommendations = []
    for t in prioritized_targets:
        market_opportunity_band = str(t.get("opportunity_band") or "unknown")
        school_signal = t.get("school_signal") or {}
        funnel_signal = t.get("funnel_signal") or {}

        reason_codes = []
        if market_opportunity_band == "strong":
            reason_codes.append("market_supports_shift")
        if market_opportunity_band == "weak":
            reason_codes.append("high_qma_low_output")
        if bool(school_signal.get("gap")):
            reason_codes.append("access_constrained")
        if str(funnel_signal.get("status") or "") in {"critical", "watch"}:
            reason_codes.append("poor_execution_in_good_market")

        rec = {
            "entity_type": "zip",
            "station_rsid": str(t.get("station_rsid") or ""),
            "company_prefix": str(t.get("station_rsid") or "")[:3],
            "zip": str(t.get("zip") or ""),
            "zip_code": str(t.get("zip") or ""),
            "market_capability_score": float(t.get("market_capability_score") or 0.0),
            "market_potential_score": float(t.get("market_capability_score") or 0.0),
            "opportunity_band": market_opportunity_band,
            "market_opportunity_band": market_opportunity_band,
            "school_access_signal": {
                "status": str(school_signal.get("access_level") or "unknown"),
                "contacts_count": int(school_signal.get("contacts_count") or 0),
                "access_gap_score": 100.0 if bool(school_signal.get("gap")) else 0.0,
            },
            "funnel_signal": {
                "overall_funnel_status": str(funnel_signal.get("status") or "unknown"),
                "lead_to_contract_rate": float(funnel_signal.get("conversion_rate") or 0.0),
                "largest_dropoff_stage": funnel_signal.get("weak_stage"),
            },
            "priority_score": round(float(t.get("priority_score") or 0.0) * 100.0, 2),
            "rationale": str(t.get("rationale") or ""),
            "trace_id": str(t.get("trace_id") or ""),
            "reason_codes": reason_codes,
            "recommended_action": str(t.get("recommended_action") or "maintain_targeting_mix"),
            **_targeting_guidance("UNK", float(t.get("market_capability_score") or 0.0) / 100.0, 0.5),
        }
        recommendations.append(rec)

    recommendations.sort(
        key=lambda x: (
            -float(x.get("priority_score") or 0.0),
            str(x.get("station_rsid") or ""),
            str(x.get("zip_code") or ""),
        )
    )

    data_sources = engine.get("data_sources") or {}
    return {
        "scope_type": scope_type,
        "scope_value": scope_value,
        "source_dataset_name": data_sources.get("market"),
        "market_source_dataset_name": data_sources.get("market"),
        "funnel_source_dataset_name": data_sources.get("funnel"),
        "formula": {
            "priority_score": "100*(0.50*market_score + 0.30*(1-funnel_efficiency) + 0.20*school_gap_score)",
            "components": {
                "market_score": "normalized market capability from market_engine",
                "funnel_efficiency": "lead_to_contract_rate adjusted by funnel status/dropoff",
                "school_gap_score": "school access gap from school_access or contacts fallback",
            },
        },
        "targeting_board_summary": {
            "recommended_focus_count": len(recommendations),
            "top_coas": [
                {
                    "coa_name": "concentrate_on_high_gap_market_supportive_zip",
                    "expected_effect": "increase_access_and_conversion",
                    "selection_rationale": "market_opportunity_with_funnel_or_school_gap",
                },
                {
                    "coa_name": "school_access_and_funnel_recovery",
                    "expected_effect": "reduce_targeting_waste_and_improve_conversion",
                    "selection_rationale": "weak_school_or_funnel_signal",
                },
            ],
        },
        "recommendations": recommendations,
    }
