from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import text
from starlette.exceptions import HTTPException

from services.api.app.services import funnel_engine, market_engine, school_access

WEIGHT_MARKET_SCORE = 0.50
WEIGHT_FUNNEL_GAP = 0.30
WEIGHT_SCHOOL_GAP = 0.20

HIGH_PRIORITY_THRESHOLD = 0.70
MODERATE_PRIORITY_THRESHOLD = 0.40


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


def _priority_band(score: float) -> str:
    if score >= HIGH_PRIORITY_THRESHOLD:
        return "high"
    if score >= MODERATE_PRIORITY_THRESHOLD:
        return "moderate"
    return "low"


def _school_signal_from_access_payload(access_payload: Dict) -> Dict[str, Dict]:
    access = (access_payload.get("school_access") or {}) if isinstance(access_payload, dict) else {}
    gaps = access.get("top_access_gaps") or []

    by_zip: Dict[str, Dict] = {}
    for row in gaps:
        stn = str(row.get("station_rsid") or "").upper()
        zc = str(row.get("zip_code") or "")
        if not stn or not zc:
            continue
        key = f"{stn}:{zc}"
        cur = by_zip.setdefault(
            key,
            {
                "school_count": 0,
                "contacts_count": 0,
                "max_gap_score": 0.0,
                "schools": [],
            },
        )
        cur["school_count"] += 1
        cur["contacts_count"] += int(row.get("contacts_count") or 0)
        cur["max_gap_score"] = max(cur["max_gap_score"], float(row.get("access_gap_score") or 0.0))
        sid = str(row.get("school_id") or "")
        sname = str(row.get("school_name") or "")
        if sid or sname:
            cur["schools"].append({"school_id": sid, "school_name": sname})

    for key, val in by_zip.items():
        val["schools"] = sorted(
            val["schools"],
            key=lambda x: (str(x.get("school_name") or ""), str(x.get("school_id") or "")),
        )[:5]
    return by_zip


def _school_signal_from_contacts_fallback(db, scope_type: str, scope_value: str) -> Tuple[str, Dict[str, Dict]]:
    prefix = _scope_prefix(scope_type, scope_value)

    q = text("SELECT name FROM sqlite_master WHERE type='table' AND name='fact_school_contacts'")
    if not db.execute(q).first():
        return "none", {}

    if prefix:
        rows = db.execute(
            text(
                """
                SELECT
                    COALESCE(unit_rsid, '') AS station_rsid,
                    COALESCE(zip, '') AS zip_code,
                    COUNT(1) AS contacts_count,
                    COUNT(DISTINCT COALESCE(school_id, school_name)) AS school_count,
                    MIN(COALESCE(school_name, school_id, '')) AS sample_school
                FROM fact_school_contacts
                WHERE unit_rsid LIKE :pfx
                GROUP BY COALESCE(unit_rsid, ''), COALESCE(zip, '')
                """
            ),
            {"pfx": f"{prefix}%"},
        ).mappings().all()
    else:
        rows = db.execute(
            text(
                """
                SELECT
                    COALESCE(unit_rsid, '') AS station_rsid,
                    COALESCE(zip, '') AS zip_code,
                    COUNT(1) AS contacts_count,
                    COUNT(DISTINCT COALESCE(school_id, school_name)) AS school_count,
                    MIN(COALESCE(school_name, school_id, '')) AS sample_school
                FROM fact_school_contacts
                GROUP BY COALESCE(unit_rsid, ''), COALESCE(zip, '')
                """
            )
        ).mappings().all()

    out: Dict[str, Dict] = {}
    for row in rows:
        stn = str(row.get("station_rsid") or "").upper()
        zc = str(row.get("zip_code") or "")
        if not stn or not zc:
            continue
        out[f"{stn}:{zc}"] = {
            "school_count": int(row.get("school_count") or 0),
            "contacts_count": int(row.get("contacts_count") or 0),
            "max_gap_score": 0.0,
            "schools": ([{"school_id": "", "school_name": str(row.get("sample_school") or "")}] if str(row.get("sample_school") or "") else []),
        }
    return "fact_school_contacts", out


def _funnel_station_maps(funnel_payload: Dict) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
    engine = (funnel_payload.get("funnel_engine") or {}) if isinstance(funnel_payload, dict) else {}
    by_scope = engine.get("by_scope") or {}
    station_rows = by_scope.get("station") or []
    station_map = {
        str(r.get("station_rsid") or "").upper(): r
        for r in station_rows
        if str(r.get("station_rsid") or "")
    }

    gap_rows = engine.get("prioritized_funnel_gaps") or []
    gap_map: Dict[str, Dict] = {}
    for g in gap_rows:
        stn = str(g.get("station_rsid") or "").upper()
        if not stn:
            continue
        if stn not in gap_map:
            gap_map[stn] = g
    return station_map, gap_map


def _safe_iso_like(v) -> str:
    if v is None:
        return ""
    s = str(v).strip()
    return s


def summarize_targeting_engine(
    db,
    scope_type: str,
    scope_value: str,
    actor_scope_type: str = "USAREC",
    actor_scope_value: str = "USAREC",
    top_n: int = 25,
) -> Dict:
    enforce_scope(actor_scope_type, actor_scope_value, scope_type, scope_value)

    market_payload = market_engine.summarize_market_engine(
        db,
        scope_type=scope_type,
        scope_value=scope_value,
        actor_scope_type=actor_scope_type,
        actor_scope_value=actor_scope_value,
        top_n=max(500, top_n * 10),
    )
    if market_payload.get("status") == "invalid_dataset_schema":
        return {
            "status": "invalid",
            "targeting_engine": {
                "summary": {
                    "total_priority_zips": 0,
                    "high_priority_count": 0,
                    "moderate_priority_count": 0,
                    "low_priority_count": 0,
                },
                "prioritized_targets": [],
                "top_targeting_shifts": [],
                "data_sources": {
                    "market": None,
                    "funnel": None,
                    "school": None,
                },
                "schema_error": ((market_payload.get("market_engine") or {}).get("schema_error")),
            },
        }

    market_rows = ((market_payload.get("market_engine") or {}).get("prioritized_market_zip") or [])
    if not market_rows:
        return {
            "status": "no_data",
            "targeting_engine": {
                "summary": {
                    "total_priority_zips": 0,
                    "high_priority_count": 0,
                    "moderate_priority_count": 0,
                    "low_priority_count": 0,
                },
                "prioritized_targets": [],
                "top_targeting_shifts": [],
                "data_sources": {
                    "market": (market_payload.get("market_engine") or {}).get("source_dataset_name"),
                    "funnel": None,
                    "school": None,
                },
            },
        }

    funnel_payload = funnel_engine.summarize_funnel_engine(
        db,
        scope_type=scope_type,
        scope_value=scope_value,
        actor_scope_type=actor_scope_type,
        actor_scope_value=actor_scope_value,
        top_n=max(500, top_n * 10),
    )
    station_funnel, station_gap = _funnel_station_maps(funnel_payload)

    school_payload = school_access.summarize_school_access(
        db,
        scope_type=scope_type,
        scope_value=scope_value,
        actor_scope_type=actor_scope_type,
        actor_scope_value=actor_scope_value,
        top_n=max(500, top_n * 10),
    )
    school_by_zip: Dict[str, Dict] = {}
    school_source = None
    if school_payload.get("status") == "ok":
        school_by_zip = _school_signal_from_access_payload(school_payload)
        school_source = (school_payload.get("school_access") or {}).get("source_dataset_name")

    if not school_by_zip:
        fallback_source, fallback_zip = _school_signal_from_contacts_fallback(db, scope_type, scope_value)
        if fallback_zip:
            school_by_zip = fallback_zip
            school_source = fallback_source

    targets: List[Dict] = []
    for row in market_rows:
        zip_code = str(row.get("zip") or "")
        station = str(row.get("station_rsid") or "").upper()
        if not zip_code or not station:
            continue

        market_score = _clamp01(float(row.get("market_capability_score") or 0.0) / 100.0)

        stn_funnel = station_funnel.get(station) or {}
        stn_gap = station_gap.get(station) or {}
        funnel_status = str(stn_funnel.get("overall_funnel_status") or "unknown")
        conversion_rate = _clamp01(float(stn_funnel.get("lead_to_contract_rate") or 0.0))
        weak_stage = str(stn_gap.get("stage") or stn_funnel.get("largest_dropoff_stage") or "unknown")

        status_penalty = {
            "healthy": 0.00,
            "watch": 0.10,
            "critical": 0.20,
            "unknown": 0.15,
        }.get(funnel_status, 0.15)
        dropoff_severity = _clamp01(float(stn_gap.get("priority_score") or 0.0) / 100.0)
        funnel_efficiency = _clamp01(conversion_rate - status_penalty - (0.20 * dropoff_severity))

        school_key = f"{station}:{zip_code}"
        school_sig = school_by_zip.get(school_key) or {
            "school_count": 0,
            "contacts_count": 0,
            "max_gap_score": 0.0,
            "schools": [],
        }
        school_count = int(school_sig.get("school_count") or 0)
        contacts_count = int(school_sig.get("contacts_count") or 0)
        school_gap_score = _clamp01(float(school_sig.get("max_gap_score") or 0.0) / 100.0)

        if school_count <= 0:
            access_level = "none"
            school_gap_score = max(school_gap_score, 1.0)
        elif contacts_count <= 0:
            access_level = "low"
            school_gap_score = max(school_gap_score, 0.75)
        elif contacts_count < school_count:
            access_level = "moderate"
            school_gap_score = max(school_gap_score, 0.50)
        else:
            access_level = "high"
            school_gap_score = max(school_gap_score, 0.10)

        priority_score = (
            WEIGHT_MARKET_SCORE * market_score
            + WEIGHT_FUNNEL_GAP * (1.0 - funnel_efficiency)
            + WEIGHT_SCHOOL_GAP * school_gap_score
        )
        priority_score = _clamp01(priority_score)
        band = _priority_band(priority_score)

        recommended_action = "maintain_targeting_mix"
        if band == "high":
            if school_count <= 0:
                recommended_action = "open_school_access_and_shift_outreach"
            elif funnel_status in {"watch", "critical"}:
                recommended_action = "shift_targeting_to_repair_funnel_dropoff"
            else:
                recommended_action = "concentrate_high_yield_outreach"
        elif band == "moderate":
            recommended_action = "tighten_targeting_and_monitor_weekly"

        reason = (
            f"market={round(market_score,4)}, funnel_efficiency={round(funnel_efficiency,4)}, "
            f"school_gap={round(school_gap_score,4)}"
        )

        targets.append(
            {
                "zip": zip_code,
                "station_rsid": station,
                "market_capability_score": round(float(row.get("market_capability_score") or 0.0), 2),
                "opportunity_band": str(row.get("opportunity_band") or "weak"),
                "funnel_signal": {
                    "status": funnel_status,
                    "weak_stage": weak_stage,
                    "conversion_rate": round(conversion_rate, 4),
                },
                "school_signal": {
                    "access_level": access_level,
                    "gap": bool(school_gap_score >= 0.5),
                    "school_count": school_count,
                    "contacts_count": contacts_count,
                    "priority_schools": school_sig.get("schools") or [],
                },
                "priority_score": round(priority_score, 4),
                "priority_band": band,
                "recommended_action": recommended_action,
                "rationale": reason,
                "trace_id": f"targeting-engine:{station}:{zip_code}",
            }
        )

    targets.sort(
        key=lambda x: (
            -float(x.get("priority_score") or 0.0),
            str(x.get("station_rsid") or ""),
            str(x.get("zip") or ""),
        )
    )

    prioritized_targets = targets[:top_n]
    high_count = sum(1 for x in prioritized_targets if x.get("priority_band") == "high")
    moderate_count = sum(1 for x in prioritized_targets if x.get("priority_band") == "moderate")
    low_count = sum(1 for x in prioritized_targets if x.get("priority_band") == "low")

    top_targeting_shifts = [
        {
            "zip": x.get("zip"),
            "station_rsid": x.get("station_rsid"),
            "priority_band": x.get("priority_band"),
            "priority_score": x.get("priority_score"),
            "recommended_action": x.get("recommended_action"),
            "trace_id": x.get("trace_id"),
        }
        for x in prioritized_targets
        if str(x.get("priority_band") or "") in {"high", "moderate"}
    ][:10]

    merged_data_as_of = max(
        [
            _safe_iso_like((market_payload.get("market_engine") or {}).get("data_as_of")),
            _safe_iso_like((funnel_payload.get("funnel_engine") or {}).get("data_as_of")),
            _safe_iso_like(((school_payload.get("school_access") or {}).get("data_as_of")) if isinstance(school_payload, dict) else ""),
        ]
    )

    return {
        "status": "ok",
        "targeting_engine": {
            "summary": {
                "total_priority_zips": len(prioritized_targets),
                "high_priority_count": int(high_count),
                "moderate_priority_count": int(moderate_count),
                "low_priority_count": int(low_count),
            },
            "prioritized_targets": prioritized_targets,
            "top_targeting_shifts": top_targeting_shifts,
            "data_sources": {
                "market": (market_payload.get("market_engine") or {}).get("source_dataset_name"),
                "funnel": (funnel_payload.get("funnel_engine") or {}).get("source_dataset_name"),
                "school": school_source,
            },
            "formula": {
                "targeting_priority_score": "0.50*market_score + 0.30*(1-funnel_efficiency) + 0.20*school_gap_score",
                "weights": {
                    "market": WEIGHT_MARKET_SCORE,
                    "funnel_gap": WEIGHT_FUNNEL_GAP,
                    "school_gap": WEIGHT_SCHOOL_GAP,
                },
            },
            "data_as_of": merged_data_as_of or None,
            "last_refresh": datetime.utcnow().isoformat() + "Z",
        },
    }
