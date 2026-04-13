from typing import Dict, List, Optional

from sqlalchemy import text

from services.api.app import models
from services.api.app import models_domain as domain
from services.api.app.services import market_engine
from services.api.app.services import funnel_engine
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
    prefix = _scope_prefix(scope_type, scope_value)
    market_payload = market_engine.summarize_market_engine(
        db,
        scope_type=scope_type,
        scope_value=scope_value,
        actor_scope_type=scope_type,
        actor_scope_value=scope_value,
        top_n=max(500, top_n * 10),
    )
    market_priority_rows = {
        f"{str(r.get('station_rsid') or '')}:{str(r.get('zip') or '')}": r
        for r in ((market_payload.get("market_engine") or {}).get("prioritized_market_zip") or [])
    }
    market_source_dataset_name = ((market_payload.get("market_engine") or {}).get("source_dataset_name"))
    funnel_payload = funnel_engine.summarize_funnel_engine(
        db,
        scope_type=scope_type,
        scope_value=scope_value,
        actor_scope_type=scope_type,
        actor_scope_value=scope_value,
        top_n=max(100, top_n * 5),
    )
    funnel_station_map = {
        str(r.get("station_rsid") or ""): r
        for r in (((funnel_payload.get("funnel_engine") or {}).get("by_scope") or {}).get("station") or [])
        if str(r.get("station_rsid") or "")
    }
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

    coverage_by_key = {
        f"{str(r.station_rsid or '')}:{str(r.zip_code or '')}": r
        for r in rows
        if str(r.station_rsid or "") and str(r.zip_code or "")
    }
    base_keys = sorted(set(coverage_by_key.keys()) | set(market_priority_rows.keys()))

    if not base_keys:
        return {
            "scope_type": scope_type,
            "scope_value": scope_value,
            "source_dataset_name": market_source_dataset_name,
            "market_source_dataset_name": market_source_dataset_name,
            "formula": {
                "priority_score": "100*(0.30*market_category_weight + 0.25*market_potential + 0.15*warning_severity + 0.15*production_gap + 0.10*effort_gap + 0.05*burden_pressure)",
            },
            "recommendations": [],
        }

    weights = _load_weights(db)
    max_weight = max(weights.values()) if weights else 1.0
    stations = sorted({k.split(":", 1)[0] for k in base_keys if ":" in k})
    burden_map = _latest_burden_by_scope(db, stations)
    production_map = _load_production_signal(db)
    effort_map = _load_effort_signal(db)
    school_maps = _load_school_access_maps(db, scope_type, scope_value)

    recs = []
    for market_key in base_keys:
        station, zip_code = market_key.split(":", 1)
        row = coverage_by_key.get(market_key)
        market_category = "UNK"
        if row is not None:
            market_category = row.market_category.name if hasattr(row.market_category, "name") else str(row.market_category)
        market_weight_raw = float(weights.get(market_category, 1.0))
        market_weight = _clamp01(market_weight_raw / max_weight)

        market_row = market_priority_rows.get(market_key, {})
        if market_row:
            opportunity = _clamp01(float(market_row.get("market_capability_score") or 0.0) / 100.0)
        else:
            opportunity = market_weight
        burden_ratio = float(burden_map.get(station, 1.0))
        burden_pressure = _clamp01((burden_ratio - 1.0) / 1.5)

        production_signal = _clamp01(production_map.get(station, production_map.get(station[:3], 0.0)))
        effort_signal = _clamp01(effort_map.get(station, effort_map.get(station[:3], 0.0)))
        warning_severity = _warning_severity(db, station)

        production_gap = _clamp01(1.0 - production_signal)
        effort_gap = _clamp01(1.0 - effort_signal)

        station_school = (school_maps.get("by_station") or {}).get(station, {})
        zip_school = (school_maps.get("by_zip") or {}).get(market_key, {})
        school_penetration = float(station_school.get("penetration_rate") or 0.0)
        school_status = _school_signal(
            station_status=str(station_school.get("access_status") or ""),
            penetration_rate=school_penetration,
            zip_status=str(zip_school.get("access_classification") or ""),
        )

        priority_score = 100.0 * (
            0.30 * market_weight
            + 0.25 * opportunity
            + 0.15 * warning_severity
            + 0.15 * production_gap
            + 0.10 * effort_gap
            + 0.05 * burden_pressure
        )

        base_reasons = _reason_codes(opportunity, burden_pressure, production_signal, effort_signal)
        merged_reasons = enrich_reason_codes_with_market(base_reasons, market_overlays.get(market_key, {}))
        if market_row and str(market_row.get("opportunity_band") or "") == "weak" and "high_qma_low_output" not in merged_reasons:
            merged_reasons.append("high_qma_low_output")
        if school_status == "constrained" and "access_constrained" not in merged_reasons:
            merged_reasons.append("access_constrained")

        opportunity_band = str(market_row.get("opportunity_band") or "unknown")
        capability_score = round(opportunity * 100.0, 2)
        rationale_parts = [
            f"market {opportunity_band} ({capability_score})",
            f"school_access {school_status}",
        ]
        if zip_school:
            rationale_parts.append(f"school_gap {round(float(zip_school.get('access_gap_score') or 0.0), 2)}")
        rationale = "; ".join(rationale_parts)

        recs.append(
            {
                "entity_type": "zip",
                "station_rsid": station,
                "company_prefix": station[:3],
                "zip": zip_code,
                "zip_code": zip_code,
                "market_category": market_category,
                "market_capability_score": capability_score,
                "market_potential_score": round(opportunity * 100.0, 2),
                "opportunity_band": opportunity_band,
                "market_opportunity_band": opportunity_band,
                "burden_ratio": round(burden_ratio, 4),
                "warning_severity": round(warning_severity, 4),
                "production_signal": round(production_signal, 4),
                "effort_signal": round(effort_signal, 4),
                "school_access_signal": {
                    "status": school_status,
                    "penetration_rate": round(school_penetration, 4),
                    "access_gap_score": round(float(zip_school.get("access_gap_score") or 0.0), 2),
                    "contacts_count": int(zip_school.get("contacts_count") or station_school.get("contacts_count") or 0),
                    "contracts_count": int(zip_school.get("contracts_count") or 0),
                },
                "funnel_signal": {
                    "overall_funnel_status": str((funnel_station_map.get(station) or {}).get("overall_funnel_status") or "unknown"),
                    "lead_to_contract_rate": round(float((funnel_station_map.get(station) or {}).get("lead_to_contract_rate") or 0.0), 4),
                    "largest_dropoff_stage": (funnel_station_map.get(station) or {}).get("largest_dropoff_stage"),
                },
                "priority_score": round(priority_score, 2),
                "rationale": rationale,
                "trace_id": str(market_row.get("trace_id") or f"targeting:{station}:{zip_code}"),
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
        "source_dataset_name": market_source_dataset_name,
        "market_source_dataset_name": market_source_dataset_name,
        "funnel_source_dataset_name": ((funnel_payload.get("funnel_engine") or {}).get("source_dataset_name")),
        "funnel_summary": ((funnel_payload.get("funnel_engine") or {}).get("summary") or {}),
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
