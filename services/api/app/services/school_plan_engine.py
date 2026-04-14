from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import text
from starlette.exceptions import HTTPException

from services.api.app.services import funnel_engine, market_engine, school_access, targeting_engine

WEIGHT_MARKET_ALIGNMENT = 0.40
WEIGHT_ACCESS_GAP = 0.30
WEIGHT_FUNNEL_INTERVENTION = 0.20
WEIGHT_TARGETING_REINFORCEMENT = 0.10

HIGH_PRIORITY_THRESHOLD = 70.0
MODERATE_PRIORITY_THRESHOLD = 40.0


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


def _clamp01(v: Optional[float]) -> float:
    if v is None:
        return 0.0
    try:
        f = float(v)
    except Exception:
        return 0.0
    if f < 0:
        return 0.0
    if f > 1:
        return 1.0
    return f


def _safe_table_exists(db, table_name: str) -> bool:
    return bool(db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"), {"n": table_name}).first())


def _table_columns(db, table_name: str) -> List[str]:
    rows = db.execute(text(f"PRAGMA table_info('{table_name}')")).mappings().all()
    return [str(r.get("name") or "") for r in rows]


def _priority_band(score: float) -> str:
    if score >= HIGH_PRIORITY_THRESHOLD:
        return "high"
    if score >= MODERATE_PRIORITY_THRESHOLD:
        return "moderate"
    return "low"


def _owner_level(scope_type: str) -> str:
    st = (scope_type or "").upper().strip()
    if st in {"USAREC", "BDE", "BN"}:
        return "BN"
    if st == "CO":
        return "CO"
    return "STN"


def _map_school_access_rows_to_plan_rows(rows: List[Dict]) -> List[Dict]:
    out = []
    for r in rows:
        school_id = str(r.get("school_id") or "").strip()
        station = str(r.get("station_rsid") or "").strip().upper()
        if not school_id or not station:
            continue
        out.append(
            {
                "school_id": school_id,
                "school_name": str(r.get("school_name") or school_id),
                "station_rsid": station,
                "zip": str(r.get("zip_code") or "").strip(),
                "source": str(r.get("source_dataset_name") or "school_access"),
            }
        )
    out.sort(key=lambda x: (x["station_rsid"], x["zip"], x["school_name"], x["school_id"]))
    return out


def _load_school_rows(db, scope_type: str, scope_value: str) -> Tuple[str, str, List[Dict]]:
    prefix = _scope_prefix(scope_type, scope_value)

    if _safe_table_exists(db, "schools"):
        cols = set(_table_columns(db, "schools"))
        station_col = "station_rsid" if "station_rsid" in cols else ("org_unit_id" if "org_unit_id" in cols else None)
        id_col = "school_id" if "school_id" in cols else ("id" if "id" in cols else None)
        name_col = "school_name" if "school_name" in cols else ("name" if "name" in cols else None)
        zip_col = "zip_code" if "zip_code" in cols else ("zip" if "zip" in cols else ("postal_code" if "postal_code" in cols else None))

        if station_col is None or id_col is None or name_col is None or zip_col is None:
            access_status, access_rows, _data_as_of, access_error = school_access._load_school_rows(db, scope_type, scope_value)
            if access_status == "ok" and access_rows:
                source_name = str(access_rows[0].get("source_dataset_name") or "school_access")
                return "ok", source_name, _map_school_access_rows_to_plan_rows(access_rows)
            if not _safe_table_exists(db, "fact_school_contacts"):
                return "invalid_dataset_schema", access_error or "schools schema not mappable to required school plan fields", []
        else:
            if prefix:
                rows = db.execute(
                    text(
                        f"""
                        SELECT {id_col} AS school_id,
                               {name_col} AS school_name,
                               {station_col} AS station_rsid,
                               {zip_col} AS zip
                        FROM schools
                        WHERE {station_col} LIKE :pfx
                        """
                    ),
                    {"pfx": f"{prefix}%"},
                ).mappings().all()
            else:
                rows = db.execute(
                    text(
                        f"""
                        SELECT {id_col} AS school_id,
                               {name_col} AS school_name,
                               {station_col} AS station_rsid,
                               {zip_col} AS zip
                        FROM schools
                        """
                    )
                ).mappings().all()

            out = []
            for r in rows:
                school_id = str(r.get("school_id") or "").strip()
                station = str(r.get("station_rsid") or "").strip().upper()
                if not school_id or not station:
                    continue
                out.append(
                    {
                        "school_id": school_id,
                        "school_name": str(r.get("school_name") or school_id),
                        "station_rsid": station,
                        "zip": str(r.get("zip") or "").strip(),
                        "source": "schools",
                    }
                )
            if out:
                out.sort(key=lambda x: (x["station_rsid"], x["zip"], x["school_name"], x["school_id"]))
                return "ok", "schools", out

    if _safe_table_exists(db, "fact_school_contacts"):
        if prefix:
            rows = db.execute(
                text(
                    """
                    SELECT
                        COALESCE(school_id, school_name) AS school_id,
                        COALESCE(school_name, school_id, '') AS school_name,
                        COALESCE(unit_rsid, '') AS station_rsid,
                        COALESCE(zip, '') AS zip
                    FROM fact_school_contacts
                    WHERE unit_rsid LIKE :pfx OR unit_rsid IS NULL OR unit_rsid = ''
                    GROUP BY COALESCE(school_id, school_name), COALESCE(school_name, school_id, ''), COALESCE(unit_rsid, ''), COALESCE(zip, '')
                    """
                ),
                {"pfx": f"{prefix}%"},
            ).mappings().all()
        else:
            rows = db.execute(
                text(
                    """
                    SELECT
                        COALESCE(school_id, school_name) AS school_id,
                        COALESCE(school_name, school_id, '') AS school_name,
                        COALESCE(unit_rsid, '') AS station_rsid,
                        COALESCE(zip, '') AS zip
                    FROM fact_school_contacts
                    GROUP BY COALESCE(school_id, school_name), COALESCE(school_name, school_id, ''), COALESCE(unit_rsid, ''), COALESCE(zip, '')
                    """
                )
            ).mappings().all()

        out = []
        for r in rows:
            school_id = str(r.get("school_id") or "").strip()
            station = str(r.get("station_rsid") or "").strip().upper()
            if not school_id or not station:
                continue
            out.append(
                {
                    "school_id": school_id,
                    "school_name": str(r.get("school_name") or school_id),
                    "station_rsid": station,
                    "zip": str(r.get("zip") or "").strip(),
                    "source": "fact_school_contacts",
                }
            )

        if out:
            out.sort(key=lambda x: (x["station_rsid"], x["zip"], x["school_name"], x["school_id"]))
            return "ok", "fact_school_contacts", out

    access_status, access_rows, _data_as_of, access_error = school_access._load_school_rows(db, scope_type, scope_value)
    if access_status == "ok" and access_rows:
        source_name = str(access_rows[0].get("source_dataset_name") or "school_access")
        return "ok", source_name, _map_school_access_rows_to_plan_rows(access_rows)
    if access_status == "invalid_dataset_schema":
        return "invalid_dataset_schema", access_error or "school access fallback schema not mappable", []

    return "no_data", "none", []


def _market_maps(market_payload: Dict) -> Dict[str, Dict]:
    rows = ((market_payload.get("market_engine") or {}).get("prioritized_market_zip") or [])
    out: Dict[str, Dict] = {}
    for r in rows:
        stn = str(r.get("station_rsid") or "").upper()
        zc = str(r.get("zip") or "")
        if stn and zc:
            out[f"{stn}:{zc}"] = r
    return out


def _funnel_maps(funnel_payload: Dict) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
    by_station_rows = (((funnel_payload.get("funnel_engine") or {}).get("by_scope") or {}).get("station") or [])
    by_station = {
        str(r.get("station_rsid") or "").upper(): r
        for r in by_station_rows
        if str(r.get("station_rsid") or "")
    }

    gaps = ((funnel_payload.get("funnel_engine") or {}).get("prioritized_funnel_gaps") or [])
    gap_by_station: Dict[str, Dict] = {}
    for g in gaps:
        stn = str(g.get("station_rsid") or "").upper()
        if stn and stn not in gap_by_station:
            gap_by_station[stn] = g
    return by_station, gap_by_station


def _access_maps(access_payload: Dict) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
    top_gaps = ((access_payload.get("school_access") or {}).get("top_access_gaps") or [])
    by_school: Dict[str, Dict] = {}
    by_zip: Dict[str, Dict] = {}

    for r in top_gaps:
        sid = str(r.get("school_id") or "")
        stn = str(r.get("station_rsid") or "").upper()
        zc = str(r.get("zip_code") or "")

        if sid:
            by_school[sid] = {
                "contacts_count": int(r.get("contacts_count") or 0),
                "contracts_count": int(r.get("contracts_count") or 0),
                "access_gap_score": float(r.get("access_gap_score") or 0.0),
                "access_classification": str(r.get("access_classification") or "underpenetrated"),
            }

        if stn and zc:
            k = f"{stn}:{zc}"
            cur = by_zip.setdefault(
                k,
                {
                    "contacts_count": 0,
                    "access_gap_score": 0.0,
                },
            )
            cur["contacts_count"] = max(cur["contacts_count"], int(r.get("contacts_count") or 0))
            cur["access_gap_score"] = max(cur["access_gap_score"], float(r.get("access_gap_score") or 0.0))

    return by_school, by_zip


def _contacts_count_map(db, scope_type: str, scope_value: str) -> Dict[Tuple[str, str], int]:
    if not _safe_table_exists(db, "fact_school_contacts"):
        return {}

    prefix = _scope_prefix(scope_type, scope_value)
    if prefix:
        rows = db.execute(
            text(
                """
                SELECT
                    COALESCE(school_id, school_name) AS school_id,
                    COALESCE(unit_rsid, '') AS station_rsid,
                    COUNT(1) AS contacts_count
                FROM fact_school_contacts
                WHERE unit_rsid LIKE :pfx OR unit_rsid IS NULL OR unit_rsid = ''
                GROUP BY COALESCE(school_id, school_name), COALESCE(unit_rsid, '')
                """
            ),
            {"pfx": f"{prefix}%"},
        ).mappings().all()
    else:
        rows = db.execute(
            text(
                """
                SELECT
                    COALESCE(school_id, school_name) AS school_id,
                    COALESCE(unit_rsid, '') AS station_rsid,
                    COUNT(1) AS contacts_count
                FROM fact_school_contacts
                GROUP BY COALESCE(school_id, school_name), COALESCE(unit_rsid, '')
                """
            )
        ).mappings().all()

    out: Dict[Tuple[str, str], int] = {}
    for r in rows:
        sid = str(r.get("school_id") or "")
        stn = str(r.get("station_rsid") or "").upper()
        if sid and stn:
            out[(sid, stn)] = int(r.get("contacts_count") or 0)
    return out


def summarize_school_plan_engine(
    db,
    scope_type: str,
    scope_value: str,
    actor_scope_type: str = "USAREC",
    actor_scope_value: str = "USAREC",
    top_n: int = 50,
) -> Dict:
    enforce_scope(actor_scope_type, actor_scope_value, scope_type, scope_value)

    school_status, school_source, school_rows = _load_school_rows(db, scope_type, scope_value)
    if school_status == "invalid_dataset_schema":
        return {
            "status": "invalid_dataset_schema",
            "school_plan_engine": {
                "summary": {
                    "total_schools": 0,
                    "priority_school_count": 0,
                    "engaged_school_count": 0,
                    "underengaged_school_count": 0,
                    "high_opportunity_school_count": 0,
                    "overall_school_status": "unknown",
                },
                "prioritized_schools": [],
                "school_recruiting_plan": [],
                "top_school_gaps": [],
                "data_sources": {
                    "school_access": None,
                    "market": None,
                    "funnel": None,
                    "targeting": None,
                },
                "schema_error": school_source,
            },
        }

    if not school_rows:
        return {
            "status": "no_data",
            "school_plan_engine": {
                "summary": {
                    "total_schools": 0,
                    "priority_school_count": 0,
                    "engaged_school_count": 0,
                    "underengaged_school_count": 0,
                    "high_opportunity_school_count": 0,
                    "overall_school_status": "unknown",
                },
                "prioritized_schools": [],
                "school_recruiting_plan": [],
                "top_school_gaps": [],
                "data_sources": {
                    "school_access": None,
                    "market": None,
                    "funnel": None,
                    "targeting": None,
                },
            },
        }

    market_payload = market_engine.summarize_market_engine(
        db,
        scope_type=scope_type,
        scope_value=scope_value,
        actor_scope_type=actor_scope_type,
        actor_scope_value=actor_scope_value,
        top_n=max(500, top_n * 20),
    )
    funnel_payload = funnel_engine.summarize_funnel_engine(
        db,
        scope_type=scope_type,
        scope_value=scope_value,
        actor_scope_type=actor_scope_type,
        actor_scope_value=actor_scope_value,
        top_n=max(500, top_n * 20),
    )
    access_payload = school_access.summarize_school_access(
        db,
        scope_type=scope_type,
        scope_value=scope_value,
        actor_scope_type=actor_scope_type,
        actor_scope_value=actor_scope_value,
        top_n=max(500, top_n * 20),
    )
    targeting_payload = targeting_engine.summarize_targeting_engine(
        db,
        scope_type=scope_type,
        scope_value=scope_value,
        actor_scope_type=actor_scope_type,
        actor_scope_value=actor_scope_value,
        top_n=max(500, top_n * 20),
    )

    market_by_zip = _market_maps(market_payload)
    funnel_by_station, funnel_gap_by_station = _funnel_maps(funnel_payload)
    access_by_school, access_by_zip = _access_maps(access_payload)
    contacts_map = _contacts_count_map(db, scope_type, scope_value)

    targeting_rows = ((targeting_payload.get("targeting_engine") or {}).get("prioritized_targets") or [])
    targeting_by_zip = {
        f"{str(r.get('station_rsid') or '').upper()}:{str(r.get('zip') or '')}": r
        for r in targeting_rows
        if str(r.get("station_rsid") or "") and str(r.get("zip") or "")
    }

    prioritized = []
    for s in school_rows:
        sid = str(s.get("school_id") or "")
        sname = str(s.get("school_name") or sid)
        stn = str(s.get("station_rsid") or "").upper()
        zc = str(s.get("zip") or "")
        zip_key = f"{stn}:{zc}"

        market_row = market_by_zip.get(zip_key) or {}
        market_score = _clamp01(float(market_row.get("market_capability_score") or 0.0) / 100.0)
        opportunity_band = str(market_row.get("opportunity_band") or "weak")

        access_school = access_by_school.get(sid) or {}
        access_zip = access_by_zip.get(zip_key) or {}
        contact_count = int(access_school.get("contacts_count") or contacts_map.get((sid, stn), access_zip.get("contacts_count") or 0))
        access_gap_raw = float(access_school.get("access_gap_score") or access_zip.get("access_gap_score") or 0.0)

        if contact_count <= 0:
            penetration_level = "low"
            access_gap_score = max(_clamp01(access_gap_raw / 100.0), 1.0)
        elif contact_count < 4:
            penetration_level = "moderate"
            access_gap_score = max(_clamp01(access_gap_raw / 100.0), 0.60)
        else:
            penetration_level = "high"
            access_gap_score = max(_clamp01(access_gap_raw / 100.0), 0.10)

        funnel_station = funnel_by_station.get(stn) or {}
        funnel_gap = funnel_gap_by_station.get(stn) or {}
        funnel_status = str(funnel_station.get("overall_funnel_status") or "unknown")
        conversion_rate = _clamp01(float(funnel_station.get("lead_to_contract_rate") or 0.0))
        weak_stage = str(funnel_gap.get("stage") or funnel_station.get("largest_dropoff_stage") or "unknown")

        funnel_status_penalty = {
            "healthy": 0.20,
            "watch": 0.60,
            "critical": 0.90,
            "unknown": 0.50,
        }.get(funnel_status, 0.50)
        dropoff_component = _clamp01(float(funnel_gap.get("priority_score") or 0.0) / 100.0)
        funnel_intervention_score = _clamp01(max(funnel_status_penalty, (1.0 - conversion_rate) * 0.8 + dropoff_component * 0.2))

        targeting_row = targeting_by_zip.get(zip_key) or {}
        targeting_reinforcement_score = _clamp01(float(targeting_row.get("priority_score") or 0.0))

        priority_score_norm = (
            WEIGHT_MARKET_ALIGNMENT * market_score
            + WEIGHT_ACCESS_GAP * access_gap_score
            + WEIGHT_FUNNEL_INTERVENTION * funnel_intervention_score
            + WEIGHT_TARGETING_REINFORCEMENT * targeting_reinforcement_score
        )
        priority_score = round(priority_score_norm * 100.0, 2)
        priority_band = _priority_band(priority_score)

        recommended_action = "maintain_current_school_engagement"
        if priority_band == "high":
            if penetration_level == "low":
                recommended_action = "increase_school_engagement_cadence"
            elif funnel_status in {"watch", "critical"}:
                recommended_action = "align_school_effort_to_repair_funnel_stage"
            else:
                recommended_action = "assign_company_follow_up_for_high_opportunity_school"
        elif priority_band == "moderate":
            recommended_action = "align_recruiter_effort_to_school_cluster"

        rationale = (
            f"market={round(market_score,4)}, access_gap={round(access_gap_score,4)}, "
            f"funnel_intervention={round(funnel_intervention_score,4)}, "
            f"targeting_reinforcement={round(targeting_reinforcement_score,4)}"
        )

        prioritized.append(
            {
                "school_id": sid,
                "school_name": sname,
                "station_rsid": stn,
                "zip": zc,
                "market_signal": {
                    "market_capability_score": round(float(market_row.get("market_capability_score") or 0.0), 2),
                    "opportunity_band": opportunity_band,
                },
                "funnel_signal": {
                    "overall_funnel_status": funnel_status,
                    "weak_stage": weak_stage,
                    "conversion_rate": round(conversion_rate, 4) if conversion_rate > 0 else None,
                },
                "access_signal": {
                    "penetration_level": penetration_level,
                    "contact_count": contact_count,
                    "gap": bool(access_gap_score >= 0.5),
                },
                "priority_score": priority_score,
                "priority_band": priority_band,
                "recommended_action": recommended_action,
                "rationale": rationale,
                "trace_id": f"school-plan:{stn}:{zc}:{sid}",
            }
        )

    prioritized.sort(
        key=lambda x: (
            -float(x.get("priority_score") or 0.0),
            str(x.get("station_rsid") or ""),
            str(x.get("zip") or ""),
            str(x.get("school_name") or ""),
            str(x.get("school_id") or ""),
        )
    )

    prioritized_schools = prioritized[:top_n]

    owner_level = _owner_level(scope_type)
    plan_rows = []
    for row in prioritized_schools:
        action = row.get("recommended_action")
        if action == "increase_school_engagement_cadence":
            action_text = f"Increase school engagement cadence at {row['school_name']} and execute weekly touchpoints."
            expected = "Improves penetration and contact flow in high-opportunity school terrain."
        elif action == "align_school_effort_to_repair_funnel_stage":
            action_text = f"Align recruiter effort at {row['school_name']} to repair weak funnel stage {row['funnel_signal'].get('weak_stage')}."
            expected = "Improves stage conversion tied to school-origin leads."
        elif action == "assign_company_follow_up_for_high_opportunity_school":
            action_text = f"Assign company follow-up for underpenetrated high-opportunity school {row['school_name']}."
            expected = "Raises school engagement where market opportunity is strongest."
        elif action == "align_recruiter_effort_to_school_cluster":
            action_text = f"Align recruiter effort to the {row['zip']} school cluster anchored by {row['school_name']}."
            expected = "Stabilizes school pipeline and improves recruiting consistency."
        else:
            action_text = f"Maintain current school engagement posture at {row['school_name']} and monitor outcomes."
            expected = "Preserves current performance while validating signal stability."

        plan_rows.append(
            {
                "school_id": row["school_id"],
                "school_name": row["school_name"],
                "owner_level": owner_level,
                "action": action_text,
                "expected_effect": expected,
                "time_horizon": "next 14 days" if row.get("priority_band") == "high" else "next 30 days",
                "rationale": row["rationale"],
                "trace_id": row["trace_id"],
            }
        )

    top_school_gaps = [
        {
            "school_id": x.get("school_id"),
            "school_name": x.get("school_name"),
            "station_rsid": x.get("station_rsid"),
            "zip": x.get("zip"),
            "priority_score": x.get("priority_score"),
            "priority_band": x.get("priority_band"),
            "rationale": x.get("rationale"),
            "trace_id": x.get("trace_id"),
        }
        for x in prioritized_schools
        if x.get("priority_band") in {"high", "moderate"}
    ][:10]

    total = len(prioritized_schools)
    high = sum(1 for x in prioritized_schools if x.get("priority_band") == "high")
    moderate = sum(1 for x in prioritized_schools if x.get("priority_band") == "moderate")
    engaged = sum(1 for x in prioritized_schools if int((x.get("access_signal") or {}).get("contact_count") or 0) > 0)
    under = total - engaged
    high_opp = sum(1 for x in prioritized_schools if str((x.get("market_signal") or {}).get("opportunity_band") or "") == "strong")

    if total <= 0:
        overall_status = "unknown"
    else:
        under_ratio = under / float(total)
        high_ratio = high / float(total)
        if under_ratio <= 0.25 and high_ratio <= 0.30:
            overall_status = "strong"
        elif under_ratio >= 0.60 or high_ratio >= 0.55:
            overall_status = "weak"
        else:
            overall_status = "moderate"

    return {
        "status": "ok",
        "school_plan_engine": {
            "summary": {
                "total_schools": int(total),
                "priority_school_count": int(high + moderate),
                "engaged_school_count": int(engaged),
                "underengaged_school_count": int(under),
                "high_opportunity_school_count": int(high_opp),
                "overall_school_status": overall_status,
            },
            "prioritized_schools": prioritized_schools,
            "school_recruiting_plan": plan_rows,
            "top_school_gaps": top_school_gaps,
            "data_sources": {
                "school_access": (access_payload.get("school_access") or {}).get("source_dataset_name") if isinstance(access_payload, dict) else None,
                "market": (market_payload.get("market_engine") or {}).get("source_dataset_name"),
                "funnel": (funnel_payload.get("funnel_engine") or {}).get("source_dataset_name"),
                "targeting": ((targeting_payload.get("targeting_engine") or {}).get("data_sources") or {}).get("market"),
            },
            "formula": {
                "school_priority_score": "100*(0.40*market_alignment + 0.30*access_gap + 0.20*funnel_intervention + 0.10*targeting_reinforcement)",
                "weights": {
                    "market_alignment": WEIGHT_MARKET_ALIGNMENT,
                    "access_gap": WEIGHT_ACCESS_GAP,
                    "funnel_intervention": WEIGHT_FUNNEL_INTERVENTION,
                    "targeting_reinforcement": WEIGHT_TARGETING_REINFORCEMENT,
                },
            },
            "data_as_of": max(
                [
                    str((access_payload.get("school_access") or {}).get("data_as_of") or "") if isinstance(access_payload, dict) else "",
                    str((market_payload.get("market_engine") or {}).get("data_as_of") or ""),
                    str((funnel_payload.get("funnel_engine") or {}).get("data_as_of") or ""),
                    str((targeting_payload.get("targeting_engine") or {}).get("data_as_of") or ""),
                ]
            )
            or None,
            "last_refresh": datetime.utcnow().isoformat() + "Z",
            "source_school_dataset": school_source,
        },
    }
