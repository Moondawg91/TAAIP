from typing import Dict, List

from services.api.app.services.market_engine import summarize_market_engine


def get_market_targeting_overlays(
    db,
    scope_type: str,
    scope_value: str,
    actor_scope_type: str = "USAREC",
    actor_scope_value: str = "USAREC",
) -> Dict[str, Dict]:
    payload = summarize_market_engine(
        db,
        scope_type=scope_type,
        scope_value=scope_value,
        actor_scope_type=actor_scope_type,
        actor_scope_value=actor_scope_value,
        top_n=100,
    )
    if payload.get("status") != "ok":
        return {}

    market = payload.get("market_engine", {})
    by_station = market.get("by_scope", {}).get("station", [])
    station_map: Dict[str, Dict] = {str(x.get("station_rsid")): x for x in by_station if x.get("station_rsid")}

    zip_overlays: Dict[str, Dict] = {}
    for z in market.get("prioritized_market_zip", []):
        stn = str(z.get("station_rsid") or "")
        zc = str(z.get("zip") or z.get("zip_code") or "")
        if not stn or not zc:
            continue
        key = f"{stn}:{zc}"
        station_status = station_map.get(stn, {})
        status = str(station_status.get("overall_market_status") or "")
        gap_hint = 1.0 if str(z.get("opportunity_band") or "") in {"moderate", "weak"} else 0.0
        zip_overlays[key] = {
            "station_rsid": stn,
            "zip_code": zc,
            "market_reason_codes": [
                "high_qma_low_output" if str(z.get("opportunity_band") or "") == "weak" else "market_supports_shift"
            ],
            "avg_opportunity_gap": float(gap_hint),
            "avg_opportunity_score": float(z.get("market_capability_score") or 0.0) / 100.0,
            "avg_output_score": float(z.get("market_capability_score") or 0.0) / 100.0,
            "market_status": "market_capable" if status == "strong" else ("market_constrained" if status == "weak" else "market_balanced"),
        }

    return zip_overlays


def enrich_reason_codes_with_market(base_reason_codes: List[str], market_overlay: Dict) -> List[str]:
    out = list(base_reason_codes or [])
    market_codes = list(market_overlay.get("market_reason_codes") or [])
    for c in market_codes:
        if c not in out:
            out.append(c)

    avg_gap = float(market_overlay.get("avg_opportunity_gap") or 0.0)
    avg_out = float(market_overlay.get("avg_output_score") or 0.0)
    market_status = str(market_overlay.get("market_status") or "")

    if avg_gap >= 0.2 and "high_qma_low_output" not in out:
        out.append("high_qma_low_output")
    if market_status == "market_constrained" and avg_out >= 0.4 and "weak_market_high_burden" not in out:
        out.append("weak_market_high_burden")
    if market_status == "market_capable" and avg_gap >= 0.15 and "strong_market_underworked" not in out:
        out.append("strong_market_underworked")
    if market_status == "market_capable" and avg_out <= 0.35 and "market_supports_shift" not in out:
        out.append("market_supports_shift")

    return out
