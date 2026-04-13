from typing import Dict, List, Optional

from sqlalchemy import text

from services.api.app import models
from services.api.app import models_domain as domain
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


def recommendations_for_scope(db, scope_type: str, scope_value: str, top_n: int = 20) -> Dict:
    prefix = _scope_prefix(scope_type, scope_value)
    market_overlays = get_market_targeting_overlays(
        db,
        scope_type=scope_type,
        scope_value=scope_value,
        actor_scope_type=scope_type,
        actor_scope_value=scope_value,
    )

    q = db.query(models.StationZipCoverage)
    if prefix:
        q = q.filter(models.StationZipCoverage.station_rsid.like(f"{prefix}%"))
    rows = q.all()

    if not rows:
        return {
            "scope_type": scope_type,
            "scope_value": scope_value,
            "formula": {
                "priority_score": "100*(0.30*market_category_weight + 0.25*market_potential + 0.15*warning_severity + 0.15*production_gap + 0.10*effort_gap + 0.05*burden_pressure)",
            },
            "recommendations": [],
        }

    weights = _load_weights(db)
    max_weight = max(weights.values()) if weights else 1.0
    stations = sorted({r.station_rsid for r in rows if r.station_rsid})
    burden_map = _latest_burden_by_scope(db, stations)
    production_map = _load_production_signal(db)
    effort_map = _load_effort_signal(db)

    recs = []
    for row in rows:
        station = row.station_rsid
        market_category = row.market_category.name if hasattr(row.market_category, "name") else str(row.market_category)
        market_weight_raw = float(weights.get(market_category, 1.0))
        market_weight = _clamp01(market_weight_raw / max_weight)

        opportunity = market_weight
        burden_ratio = float(burden_map.get(station, 1.0))
        burden_pressure = _clamp01((burden_ratio - 1.0) / 1.5)

        production_signal = _clamp01(production_map.get(station, production_map.get(station[:3], 0.0)))
        effort_signal = _clamp01(effort_map.get(station, effort_map.get(station[:3], 0.0)))
        warning_severity = _warning_severity(db, station)

        production_gap = _clamp01(1.0 - production_signal)
        effort_gap = _clamp01(1.0 - effort_signal)

        priority_score = 100.0 * (
            0.30 * market_weight
            + 0.25 * opportunity
            + 0.15 * warning_severity
            + 0.15 * production_gap
            + 0.10 * effort_gap
            + 0.05 * burden_pressure
        )

        base_reasons = _reason_codes(opportunity, burden_pressure, production_signal, effort_signal)
        market_key = f"{station}:{row.zip_code}"
        merged_reasons = enrich_reason_codes_with_market(base_reasons, market_overlays.get(market_key, {}))

        recs.append(
            {
                "entity_type": "zip",
                "station_rsid": station,
                "company_prefix": station[:3],
                "zip_code": row.zip_code,
                "market_category": market_category,
                "market_potential_score": round(opportunity * 100.0, 2),
                "burden_ratio": round(burden_ratio, 4),
                "warning_severity": round(warning_severity, 4),
                "production_signal": round(production_signal, 4),
                "effort_signal": round(effort_signal, 4),
                "priority_score": round(priority_score, 2),
                "reason_codes": merged_reasons,
                **_targeting_guidance(market_category, opportunity, effort_signal),
            }
        )

    recs.sort(key=lambda x: x["priority_score"], reverse=True)

    # Promote a scope-appropriate ranked rollup by station/company in addition to ZIP rows.
    station_rollup = {}
    company_rollup = {}
    for r in recs:
        stn = r["station_rsid"]
        co = r["company_prefix"]
        station_rollup.setdefault(stn, []).append(r["priority_score"])
        company_rollup.setdefault(co, []).append(r["priority_score"])

    ranked_stations = sorted(
        [{"entity_type": "station", "station_rsid": k, "priority_score": round(sum(v) / len(v), 2)} for k, v in station_rollup.items()],
        key=lambda x: x["priority_score"],
        reverse=True,
    )
    ranked_companies = sorted(
        [{"entity_type": "company", "company_prefix": k, "priority_score": round(sum(v) / len(v), 2)} for k, v in company_rollup.items()],
        key=lambda x: x["priority_score"],
        reverse=True,
    )

    ranked = recs[:top_n]
    if (scope_type or "").upper() in {"USAREC", "BDE", "BN"}:
        ranked = ranked_companies[:top_n] + ranked_stations[:top_n] + recs[:top_n]
    elif (scope_type or "").upper() == "CO":
        ranked = ranked_stations[:top_n] + recs[:top_n]

    return {
        "scope_type": scope_type,
        "scope_value": scope_value,
        "formula": {
            "priority_score": "100*(0.30*market_category_weight + 0.25*market_potential + 0.15*warning_severity + 0.15*production_gap + 0.10*effort_gap + 0.05*burden_pressure)",
            "components": {
                "market_category_weight": "normalized category weight from market_category_weights",
                "market_potential": "normalized opportunity from market category",
                "warning_severity": "active home alerts normalized to 0-1",
                "production_gap": "1 - normalized production signal",
                "effort_gap": "1 - normalized marketing effort signal",
                "burden_pressure": "normalized burden ratio pressure",
            },
        },
        "targeting_board_summary": {
            "recommended_focus_count": len([x for x in recs if x.get("entity_type") == "zip"]),
            "top_coas": [
                {
                    "coa_name": "concentrate_on_high_gap_market_supportive_zip",
                    "expected_effect": "increase_access_and_conversion",
                    "selection_rationale": "opportunity_gap_and_market_support",
                },
                {
                    "coa_name": "processing_recovery_in_high_stall_stations",
                    "expected_effect": "reduce_stage_aging_and_stalls",
                    "selection_rationale": "execution_quality_and_bottleneck_signals",
                },
            ],
        },
        "recommendations": ranked,
    }
